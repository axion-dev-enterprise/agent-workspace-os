#!/usr/bin/env python3
"""
Resilient Web Scraper & Structured Data Extractor
Fetches web pages using standard browser headers, handles HTTP 429 retries with backoff,
and extracts structured metadata, JSON-LD, and Next.js __NEXT_DATA__ blocks.
Zero external dependencies (Python 3 stdlib only).
"""

import sys
import json
import re
import time
import random
import urllib.request
import urllib.error
from html.parser import HTMLParser

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    "Sec-CH-UA": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


class MetadataHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_tags = {}
        self.json_ld_blocks = []
        self.next_data = None
        self._in_title = False
        self._in_json_ld = False
        self._in_next_data = False
        self._script_buffer = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = attr_dict.get("name") or attr_dict.get("property")
            val = attr_dict.get("content")
            if key and val:
                self.meta_tags[key.lower()] = val
        elif tag == "script":
            script_type = attr_dict.get("type", "").lower()
            script_id = attr_dict.get("id", "")
            if script_type == "application/ld+json":
                self._in_json_ld = True
                self._script_buffer = []
            elif script_id == "__NEXT_DATA__":
                self._in_next_data = True
                self._script_buffer = []

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            raw_text = "".join(self._script_buffer).strip()
            if self._in_json_ld and raw_text:
                try:
                    self.json_ld_blocks.append(json.loads(raw_text))
                except json.JSONDecodeError:
                    pass
                self._in_json_ld = False
            elif self._in_next_data and raw_text:
                try:
                    self.next_data = json.loads(raw_text)
                except json.JSONDecodeError:
                    pass
                self._in_next_data = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_json_ld or self._in_next_data:
            self._script_buffer.append(data)


def fetch_with_backoff(url: str, max_retries: int = 3) -> str:
    """Fetches a URL with realistic headers and exponential jitter backoff on 429/503."""
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    attempt = 0

    while attempt <= max_retries:
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                content = response.read()
                encoding = response.headers.get_content_charset() or "utf-8"
                return content.decode(encoding, errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries:
                retry_after = e.headers.get("Retry-After")
                wait_time = float(retry_after) if retry_after and retry_after.isdigit() else (2 ** attempt) + random.uniform(0.5, 1.5)
                print(f"[!] HTTP {e.code} received. Backing off for {wait_time:.1f}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
                attempt += 1
            else:
                raise RuntimeError(f"HTTP {e.code}: {e.reason}") from e
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2)
                attempt += 1
            else:
                raise RuntimeError(f"Failed to fetch {url}: {e}") from e

    raise RuntimeError(f"Exceeded max retries for {url}")


def scrape_structured_data(url: str) -> dict:
    html_content = fetch_with_backoff(url)
    parser = MetadataHTMLParser()
    parser.feed(html_content)

    return {
        "url": url,
        "title": parser.title.strip(),
        "meta_description": parser.meta_tags.get("description", ""),
        "og_title": parser.meta_tags.get("og:title", ""),
        "og_image": parser.meta_tags.get("og:image", ""),
        "json_ld_count": len(parser.json_ld_blocks),
        "json_ld_schemas": parser.json_ld_blocks,
        "has_next_data": parser.next_data is not None,
        "next_data_page": parser.next_data.get("page") if parser.next_data else None,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python resilient_scraper.py <url>")
        sys.exit(0)

    url = sys.argv[1]
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    print(f"=== Scraping Structured Data from: {url} ===")
    try:
        data = scrape_structured_data(url)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
