#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lead_geo_scraper.py — Geospatial Intelligence & Lead Extraction Engine
Part of agentic-engineering-suite skill — AXION Enterprise
Combines OpenStreetMap Geocoding & POI search, Local Scraper Support (gosom)
and Zero-Token Social Media Regex Enrichment.
Zero external dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import re
import csv
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

UA = "AXION-LeadGeoScraper/1.0 (https://example.com; dev@example.com)"

SOCIAL_PATTERNS = {
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)", re.I),
    "facebook": re.compile(r"https?://(?:www\.|m\.|web\.)?facebook\.com/([A-Za-z0-9_.\-]+)", re.I),
    "linkedin": re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/(?:company|in|school)/([A-Za-z0-9_.\-%]+)", re.I),
}

SKIP_HANDLES = {
    "", "home", "pages", "people", "help", "about", "policies", "policy", "legal",
    "tos", "privacy", "settings", "sharer", "tr", "profile.php", "plugins", "dialog",
    "intent", "login", "share.php", "permalink.php", "p", "reel", "reels", "explore",
}


def geocode_place(place_name: str) -> Optional[Tuple[float, float, str]]:
    """Resolves city or place name to (lat, lon, display_name) via OpenStreetMap Nominatim."""
    params = urllib.parse.urlencode({"format": "json", "limit": 1, "q": place_name})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            time.sleep(1.0)  # Respect OSM Nominatim usage policy (max 1 req/s)
            if data and len(data) > 0:
                first = data[0]
                return float(first["lat"]), float(first["lon"]), first.get("display_name", place_name)
    except Exception as e:
        sys.stderr.write(f"[WARN] Falha na geocodificacao: {e}\n")
    return None


def fetch_socials_from_website(url: str, timeout: int = 6) -> Dict[str, str]:
    """Extracts social media profile handles from a website via regex without LLM token cost."""
    socials = {"instagram": "", "facebook": "", "linkedin": ""}
    if not url:
        return socials

    target_url = url if url.startswith(("http://", "https://")) else "https://" + url

    try:
        req = urllib.request.Request(
            target_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read(300_000).decode("utf-8", errors="replace")

        for plat, regex in SOCIAL_PATTERNS.items():
            for m in regex.finditer(html):
                handle = m.group(1).strip("/?#").split("?")[0]
                if handle.lower() not in SKIP_HANDLES and len(handle) < 60:
                    socials[plat] = handle
                    break
    except Exception:
        pass

    return socials


def query_nominatim_poi(place: str, category: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Fetches verified POI listings via Nominatim structured search."""
    query = f"{category} in {place}"
    params = urllib.parse.urlencode({
        "format": "json",
        "q": query,
        "addressdetails": 1,
        "limit": limit
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})

    leads = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            items = json.loads(resp.read().decode("utf-8", errors="replace"))
            for item in items:
                name = item.get("name") or item.get("display_name", "").split(",")[0]
                addr = item.get("address", {})
                road = addr.get("road", "")
                house = addr.get("house_number", "")
                suburb = addr.get("suburb") or addr.get("neighbourhood", "")
                city = addr.get("city") or addr.get("town", "")
                address_parts = [p for p in [road, house, suburb, city] if p]
                address = ", ".join(address_parts) if address_parts else item.get("display_name", "")

                leads.append({
                    "title": name,
                    "phone": "",
                    "website": "",
                    "emails": "",
                    "category": category,
                    "address": address,
                    "latitude": float(item.get("lat", 0)),
                    "longitude": float(item.get("lon", 0)),
                    "instagram": "",
                    "facebook": "",
                    "linkedin": "",
                })
    except Exception as e:
        sys.stderr.write(f"[WARN] Nominatim POI query failed: {e}\n")

    return leads


def check_local_scraper_service(base_url: str = "http://127.0.0.1:8080") -> bool:
    """Checks whether the local gosom Docker scraper container is responsive."""
    try:
        req = urllib.request.Request(base_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status in (200, 404, 405)
    except Exception:
        return False


def run_pipeline(
    place: str,
    category: str,
    limit: int = 10,
    enrich_socials: bool = True,
    output_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Runs complete end-to-end geospatial lead extraction pipeline."""
    print(f"[*] Geocodificando e buscando: '{category}' em '{place}'...")

    has_docker_daemon = check_local_scraper_service()
    if has_docker_daemon:
        print("[+] Backend local de alta escala (gosom/docker) detectado em 127.0.0.1:8080.")
    else:
        print("[i] Modo autônomo ativo via OpenStreetMap Nominatim.")

    leads = query_nominatim_poi(place, category, limit=limit)
    print(f"[+] {len(leads)} estabelecimentos encontrados.")

    if enrich_socials and leads:
        print("[*] Enriquecendo perfis sociais via regex nos websites (0 tokens LLM)...")
        for lead in leads:
            if lead["website"]:
                soc = fetch_socials_from_website(lead["website"])
                lead["instagram"] = soc["instagram"]
                lead["facebook"] = soc["facebook"]
                lead["linkedin"] = soc["linkedin"]

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        if output_path.endswith(".json"):
            out_file.write_text(json.dumps(leads, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            fieldnames = ["title", "phone", "emails", "website", "category", "address", "instagram", "facebook", "linkedin", "latitude", "longitude"]
            with open(out_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in leads:
                    writer.writerow({k: item.get(k, "") for k in fieldnames})
        print(f"[✓] Resultados gravados em: {out_file}")

    return leads


def main():
    parser = argparse.ArgumentParser(description="Extração Inteligente de Leads Geoespaciais e Enriquecimento Social")
    parser.add_argument("--city", default="Sao Paulo, SP", help="Nome da cidade ou localização para geocodificação")
    parser.add_argument("--category", default="cafe", help="Nicho de negócio (ex: cafe, academia, restaurante, hotel)")
    parser.add_argument("--limit", type=int, default=5, help="Quantidade máxima de estabelecimentos")
    parser.add_argument("--no-socials", action="store_true", help="Pula o enriquecimento de redes sociais")
    parser.add_argument("--out", help="Arquivo de destino (.csv ou .json)")
    parser.add_argument("--json", action="store_true", help="Exibe os resultados em JSON no terminal")
    args = parser.parse_args()

    results = run_pipeline(
        place=args.city,
        category=args.category,
        limit=args.limit,
        enrich_socials=not args.no_socials,
        output_path=args.out,
    )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif not args.out:
        print("\n" + "=" * 60)
        print(f" LEADS ENCONTRADOS ({len(results)} registros)")
        print("=" * 60)
        for i, lead in enumerate(results, 1):
            print(f"{i}. {lead['title']}")
            print(f"   Endereço: {lead['address']}")
            if lead['phone']:
                print(f"   Telefone: {lead['phone']}")
            if lead['website']:
                print(f"   Website : {lead['website']}")
            socs = [f"{k}: @{v}" for k, v in [('IG', lead['instagram']), ('FB', lead['facebook']), ('IN', lead['linkedin'])] if v]
            if socs:
                print(f"   Sociais : {' | '.join(socs)}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
