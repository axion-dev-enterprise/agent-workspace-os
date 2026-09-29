"""
AXION Content Intelligence Monitor
====================================
Rotina de análise de conteúdo para absorver novas técnicas, ferramentas
e tendências do ecossistema AXION.

Fontes monitoradas:
  - GitHub Trending (Python, JavaScript, TypeScript, Docker)
  - Hacker News (Top Stories via API)
  - Cloudflare Blog RSS
  - Proton Blog RSS
  - The Hacker News (infosec)
  - ArXiv (AI/ML papers - cs.AI, cs.LG)
  - Reddit r/netsec, r/selfhosted, r/homelab

Saída:
  - memory/intelligence/daily_digest.jsonl  (uma entrada por execução)
  - memory/intelligence/feeds_cache.json    (cache dos últimos items por fonte)
  - memory/intelligence/keywords_hits.jsonl (hits de keywords do ecossistema)

Agendamento (Task Scheduler):
  AXION-Content-Intelligence — Daily 08:00 AM
"""

import os
import json
import hashlib
import logging
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
MEMORY_DIR  = Path("c:/workspace/memory/intelligence")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
DIGEST_LOG  = MEMORY_DIR / "daily_digest.jsonl"
CACHE_FILE  = MEMORY_DIR / "feeds_cache.json"
HITS_LOG    = MEMORY_DIR / "keywords_hits.jsonl"

AXION_KEYWORDS = [
    # Core stack
    "cloudflare", "workers", "d1", "r2", "pages", "tunnels",
    "nextjs", "react", "fastapi", "nestjs", "prisma", "drizzle",
    "tailwind", "shadcn", "radix",
    # Infra & DevOps
    "docker", "kubernetes", "k3s", "tailscale", "vercel",
    "github actions", "ci/cd",
    # AI & Agents
    "gemini", "langchain", "langgraph", "rag", "vector", "embedding",
    "llm", "agent", "mcp", "openai",
    # Security & Privacy
    "proton", "wireguard", "zero trust", "osint", "pentest",
    "vulnerability", "cve", "exploit",
    # Databases
    "postgresql", "redis", "qdrant", "mongodb", "sqlite",
    # Languages
    "python", "typescript", "rust",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [INTEL-MONITOR] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("content_monitor")


def _get(url: str, timeout: int = 10) -> str | None:
    """HTTP GET simples, retorna body como string ou None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AXION-Intel-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        log.warning(f"GET failed {url}: {e}")
        return None


def _fingerprint(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


# ══════════════════════════════════════════════════════════════════════════════
# Fetchers
# ══════════════════════════════════════════════════════════════════════════════

def fetch_github_trending(language: str = "", since: str = "daily") -> list[dict]:
    """Scraping básico do GitHub Trending (sem auth necessária)."""
    url = f"https://github.com/trending/{language}?since={since}"
    body = _get(url)
    if not body:
        return []

    items = []
    # Parse <h2 class="h3 lh-condensed"> tags
    import re
    # Padrão: href="/owner/repo" dentro de heading de trending
    pattern = re.compile(r'href="/([a-zA-Z0-9_.\-]+/[a-zA-Z0-9_.\-]+)"')
    seen = set()
    for m in pattern.finditer(body):
        slug = m.group(1).strip()
        if slug.count("/") == 1 and slug not in seen and not slug.startswith("#"):
            seen.add(slug)
            items.append({
                "source": "github_trending",
                "language": language or "all",
                "repo": slug,
                "url": f"https://github.com/{slug}",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        if len(items) >= 25:
            break
    log.info(f"GitHub trending ({language or 'all'}): {len(items)} repos")
    return items


def fetch_hackernews_top(limit: int = 20) -> list[dict]:
    """HN Top Stories via API oficial."""
    ids_raw = _get("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids_raw:
        return []
    ids = json.loads(ids_raw)[:limit]
    items = []
    for story_id in ids:
        raw = _get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not raw:
            continue
        item = json.loads(raw)
        if item.get("type") != "story":
            continue
        items.append({
            "source":     "hackernews",
            "id":         story_id,
            "title":      item.get("title", ""),
            "url":        item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            "score":      item.get("score", 0),
            "comments":   item.get("descendants", 0),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })
    log.info(f"HackerNews top: {len(items)} stories")
    return items


def fetch_rss(name: str, url: str, limit: int = 15) -> list[dict]:
    """Parser RSS/Atom genérico."""
    body = _get(url)
    if not body:
        return []
    try:
        root = ET.fromstring(body)
        ns   = {"atom": "http://www.w3.org/2005/Atom"}
        items = []

        # RSS 2.0
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link") or "").strip()
            pub   = (item.findtext("pubDate") or "").strip()
            desc  = (item.findtext("description") or "").strip()[:300]
            items.append({
                "source":     name,
                "title":      title,
                "url":        link,
                "published":  pub,
                "excerpt":    desc,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        # Atom
        if not items:
            for entry in root.findall("atom:entry", ns)[:limit]:
                title   = (entry.findtext("atom:title", namespaces=ns) or "").strip()
                link_el = entry.find("atom:link", ns)
                link    = link_el.get("href", "") if link_el is not None else ""
                pub     = (entry.findtext("atom:published", namespaces=ns) or "").strip()
                items.append({
                    "source":     name,
                    "title":      title,
                    "url":        link,
                    "published":  pub,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                })

        log.info(f"RSS {name}: {len(items)} items")
        return items
    except ET.ParseError as e:
        log.warning(f"RSS parse error {name}: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# Keyword Scanner
# ══════════════════════════════════════════════════════════════════════════════

def scan_keywords(items: list[dict]) -> list[dict]:
    """Filtra items que contêm keywords do ecossistema AXION."""
    hits = []
    for item in items:
        text = (
            item.get("title", "") + " " +
            item.get("excerpt", "") + " " +
            item.get("repo", "")
        ).lower()
        matched = [kw for kw in AXION_KEYWORDS if kw in text]
        if matched:
            hits.append({**item, "keywords_matched": matched})
    return hits


# ══════════════════════════════════════════════════════════════════════════════
# Cache Management
# ══════════════════════════════════════════════════════════════════════════════

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {}


def save_cache(data: dict):
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")


def is_new(item: dict, cache: dict) -> bool:
    """Retorna True se o item não estava no cache anterior."""
    url = item.get("url") or item.get("repo") or ""
    fp  = _fingerprint(url)
    return fp not in cache.get("seen_fps", [])


# ══════════════════════════════════════════════════════════════════════════════
# Main Runner
# ══════════════════════════════════════════════════════════════════════════════

RSS_FEEDS = {
    "cloudflare_blog":  "https://blog.cloudflare.com/rss/",
    "proton_blog":      "https://proton.me/blog/feed",
    "thehackernews":    "https://feeds.feedburner.com/TheHackersNews",
    "github_changelog": "https://github.blog/changelog/feed/",
    "vercel_blog":      "https://vercel.com/blog/rss.xml",
    "nextjs_releases":  "https://github.com/vercel/next.js/releases.atom",
    "tailscale_blog":   "https://tailscale.com/blog/index.xml",
}


def run():
    log.info("=== AXION Content Intelligence Monitor — início ===")
    cache = load_cache()
    seen_fps: list[str] = cache.get("seen_fps", [])

    all_items: list[dict] = []

    # GitHub Trending
    for lang in ["", "python", "typescript", "javascript"]:
        all_items.extend(fetch_github_trending(lang))

    # Hacker News
    all_items.extend(fetch_hackernews_top(25))

    # RSS Feeds
    for name, url in RSS_FEEDS.items():
        all_items.extend(fetch_rss(name, url))

    # Filtrar novos
    new_items = [i for i in all_items if is_new(i, cache)]
    log.info(f"Total: {len(all_items)} items | Novos: {len(new_items)}")

    # Escanear keywords
    keyword_hits = scan_keywords(new_items)
    log.info(f"Keyword hits: {len(keyword_hits)}")

    # Persistir hits
    for hit in keyword_hits:
        with open(HITS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(hit, ensure_ascii=False) + "\n")

    # Digest diário
    digest = {
        "run_at":          datetime.now(timezone.utc).isoformat(),
        "total_fetched":   len(all_items),
        "new_items":       len(new_items),
        "keyword_hits":    len(keyword_hits),
        "top_hits":        keyword_hits[:10],
        "github_trending": [i for i in new_items if i["source"] == "github_trending"][:10],
        "hn_top":          [i for i in new_items if i["source"] == "hackernews"][:5],
    }
    with open(DIGEST_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(digest, ensure_ascii=False) + "\n")

    # Atualizar cache (manter últimas 2000 fps)
    new_fps = [_fingerprint(i.get("url", "") or i.get("repo", "")) for i in all_items]
    all_fps = list(dict.fromkeys(seen_fps + new_fps))[-2000:]
    save_cache({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "seen_fps":   all_fps,
        "last_counts": {
            "total": len(all_items),
            "new":   len(new_items),
            "hits":  len(keyword_hits),
        },
    })

    log.info("=== Monitor concluído ===")
    print(f"\n[AXION-INTEL] {len(keyword_hits)} hits relevantes encontrados de {len(new_items)} novos items")
    if keyword_hits:
        print("\nTop 5 hits:")
        for h in keyword_hits[:5]:
            kws = ", ".join(h.get("keywords_matched", [])[:3])
            print(f"  [{h['source']}] {h.get('title') or h.get('repo')} — keywords: {kws}")
            print(f"    URL: {h.get('url', '')}")

    # ── Módulos sociais (Twitter/X e Instagram) ────────────────────────────────
    _run_social_monitors()

    return digest


def _run_social_monitors():
    """Executa monitores de redes sociais de forma isolada (falha não bloqueia o monitor principal)."""
    import sys, os
    sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "agent-social"))

    # Twitter/X
    try:
        import twitter_x_monitor
        tw = twitter_x_monitor.run()
        log.info(f"Twitter/X: {tw.get('hits', 0)} hits")
    except Exception as e:
        log.warning(f"Twitter monitor: {e}")

    # Instagram
    try:
        import instagram_monitor
        ig = instagram_monitor.run()
        log.info(f"Instagram: {ig.get('hits', 0)} hits")
    except Exception as e:
        log.warning(f"Instagram monitor: {e}")


if __name__ == "__main__":
    run()
