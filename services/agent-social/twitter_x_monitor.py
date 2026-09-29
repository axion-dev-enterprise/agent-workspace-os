"""
AXION Twitter/X Monitor
========================
Monitor de conteúdo do Twitter/X para o ecossistema AXION.

ESTADO ATUAL DO ECOSSISTEMA (2026):
  - Nitter (mirrors open-source) requer login autenticado desde 2024 → instâncias públicas não funcionam
  - A ÚNICA forma gratuita e confiável de ler tweets sem scraping ilegal é:
    → Twitter API v2 FREE TIER: 500k tweets lidos/mês, sem custo
    → Cadastro em ~5 minutos: https://developer.x.com/en/portal/dashboard

MODOS DISPONÍVEIS:
  1. API v2 (RECOMENDADO — Free tier, sem custo):
     Configure: X_BEARER_TOKEN no .env
     
  2. Mock/Demo (sem configuração):
     Retorna dados simulados para testar o pipeline
     Execute: python twitter_x_monitor.py --mock

COMO ATIVAR (Twitter API v2 Free):
  1. Acesse: https://developer.x.com/en/portal/dashboard
  2. Sign in com sua conta Twitter/X
  3. Clique "Create Project" → nomeie (ex: "AXION Monitor")
  4. Clique "Add App" → copie o Bearer Token
  5. Adicione ao c:\\workspace\\.env:
       X_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAxxxxx...
  6. Execute: python twitter_x_monitor.py
"""

import os
import json
import sys
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Garantir que a raiz canônica do workspace esteja no sys.path
WORKSPACE_ROOT = Path("c:/workspace")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Carregar segredos centralizados do AXION Vault
try:
    from scripts.vault_loader import load_vault
    load_vault()
except Exception as e:
    print(f"[!] Erro ao carregar vault: {e}")

MEMORY_DIR  = Path("c:/workspace/memory/intelligence")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
TWITTER_LOG   = MEMORY_DIR / "twitter_hits.jsonl"
TWITTER_CACHE = MEMORY_DIR / "twitter_cache.json"

X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "")

# Perfis a monitorar via API v2 e Syndication Engine
TWITTER_PROFILES = [
    # Infraestrutura & Plataforma
    "cloudflare", "vercel", "nextjs", "tailscale", "github", "docker", "ProtonPrivacy",
    # Labs & Fundadores de IA
    "OpenAI", "GoogleDeepMind", "AnthropicAI", "sama",
    # Pesquisadores de Ponta & Pioneiros em LLMs
    "karpathy", "ylecun", "ilyasut", "fchollet", "DrJimFan",
    # Agentes Autônomos & Frameworks (LangGraph, BabyAGI, Latent Space)
    "hwchase17", "yoheinakajima", "swyx", "simonw", "OfficialLoganK", "bindureddy",
    # Papers Diários & Open Source
    "_akhaliq",
]

# Queries de busca (Twitter API v2 search_recent_tweets)
TWITTER_QUERIES = [
    "cloudflare workers -is:retweet",
    "nextjs 15 -is:retweet",
    "langchain agent -is:retweet",
    "#rag llm -is:retweet",
    "autonomous agent llm -is:retweet",
    "mcp model context protocol -is:retweet",
]

AXION_KEYWORDS = [
    "cloudflare", "workers", "nextjs", "fastapi", "docker",
    "kubernetes", "tailscale", "agent", "agents", "llm", "rag", "vector",
    "gemini", "langchain", "langgraph", "openai", "claude", "anthropic",
    "deepseek", "mcp", "reasoning", "python", "typescript", "proton",
    "zero trust", "osint", "pentest", "postgresql", "redis", "prisma", "vercel",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TWITTER-MONITOR] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("twitter_monitor")


def _fp(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def load_cache() -> set:
    if TWITTER_CACHE.exists():
        try:
            return set(json.loads(TWITTER_CACHE.read_text("utf-8")).get("seen", []))
        except Exception:
            pass
    return set()


def save_cache(seen: set):
    TWITTER_CACHE.write_text(
        json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "seen": list(seen)[-3000:]}),
        "utf-8"
    )


def scan_keywords(text: str) -> list[str]:
    t = text.lower()
    return [kw for kw in AXION_KEYWORDS if kw in t]


# ══════════════════════════════════════════════════════════════════════════════
# Modo 1: Twitter API v2 (Bearer Token)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_api_v2(queries: list[str], max_per_query: int = 20) -> list[dict]:
    """Busca tweets via Twitter API v2 usando Bearer Token."""
    try:
        import tweepy
    except ImportError:
        log.error("tweepy não instalado. Execute: pip install tweepy")
        return []

    client = tweepy.Client(bearer_token=X_BEARER_TOKEN, wait_on_rate_limit=True)
    items = []

    for query in queries:
        try:
            resp = client.search_recent_tweets(
                query=query,
                max_results=min(max_per_query, 100),
                tweet_fields=["created_at", "author_id", "public_metrics", "text"],
                expansions=["author_id"],
                user_fields=["username", "name"],
            )
            if not resp.data:
                continue

            # Mapear author_id → username
            users = {}
            if resp.includes and resp.includes.get("users"):
                for u in resp.includes["users"]:
                    users[u.id] = u.username

            for tweet in resp.data:
                username = users.get(tweet.author_id, "unknown")
                text     = tweet.text or ""
                kws      = scan_keywords(text)
                url      = f"https://x.com/{username}/status/{tweet.id}"
                items.append({
                    "source":           "twitter_api_v2",
                    "label":            f"q:{query[:30]}",
                    "username":         username,
                    "title":            text[:100],
                    "text":             text,
                    "url":              url,
                    "published":        str(tweet.created_at) if tweet.created_at else "",
                    "keywords_matched": kws,
                    "fetched_at":       datetime.now(timezone.utc).isoformat(),
                })
            log.info(f"Query '{query[:40]}': {len([i for i in items if query[:30] in i['label']])} tweets")

        except tweepy.TweepyException as e:
            if "402" in str(e) or "credits depleted" in str(e):
                log.info("API v2: créditos de busca esgotados/pay-per-use ativo — usando Syndication Engine.")
                break
            log.warning(f"Tweepy error '{query}': {e}")

    return items


# ══════════════════════════════════════════════════════════════════════════════
# Modo 1: Twitter Syndication Engine (Bypass 100% Funcional sem API Paga)
# ══════════════════════════════════════════════════════════════════════════════

import subprocess
import re

def fetch_syndication_profile(screen_name: str) -> list[dict]:
    """Busca tweets públicos recentes via endpoint oficial de Syndication do X."""
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{screen_name}"
    cmd = [
        "curl.exe", "-s", "-L",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "-H", "Referer: https://platform.twitter.com/",
        "-H", "Accept-Language: en-US,en;q=0.9",
        url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        html = res.stdout
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group(1))
        entries = data.get("props", {}).get("pageProps", {}).get("timeline", {}).get("entries", [])
        tweets = []
        for e in entries:
            t = e.get("content", {}).get("tweet")
            if t:
                text = t.get("full_text", "")
                kws = scan_keywords(text)
                tweets.append({
                    "source": "twitter_syndication",
                    "label": f"@{screen_name}",
                    "username": screen_name,
                    "title": text[:100],
                    "text": text,
                    "url": f"https://x.com/{screen_name}/status/{t.get('id_str')}",
                    "published": t.get("created_at", ""),
                    "keywords_matched": kws,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                })
        log.info(f"@{screen_name}: {len(tweets)} tweets via Syndication")
        return tweets
    except Exception as err:
        log.warning(f"Erro syndication @{screen_name}: {err}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# Modo 2: Mock (demo)
# ══════════════════════════════════════════════════════════════════════════════

MOCK_TWEETS = [
    {"username": "cloudflare",    "text": "Python Workers are now GA on Cloudflare Workers. Write your Workers in Python!"},
    {"username": "vercel",        "text": "Next.js 15.1 is out - faster builds, improved caching, and new ISR controls"},
    {"username": "github",        "text": "GitHub Copilot now supports Claude Sonnet in all plans"},
    {"username": "docker",        "text": "Docker Desktop 4.35 - enhanced resource management and BuildKit improvements"},
    {"username": "tailscale",     "text": "Taildrop improvements: faster transfers and better Windows support in 1.76"},
    {"username": "OpenAI",        "text": "GPT-4o mini is now available in the API with a 128k context window"},
    {"username": "ProtonPrivacy", "text": "Proton VPN now has 10,000+ servers across 117 countries. Stay private."},
    {"username": "GoogleDeepMind","text": "Gemini 2.0 Flash is 2x faster than 1.5 Flash with improved multimodal capabilities"},
]


def fetch_mock() -> list[dict]:
    """Retorna tweets simulados para testar o pipeline sem API key."""
    items = []
    for t in MOCK_TWEETS:
        text = t["text"]
        kws  = scan_keywords(text)
        items.append({
            "source":           "twitter_mock",
            "label":            f"@{t['username']}",
            "username":         t["username"],
            "title":            text[:100],
            "text":             text,
            "url":              f"https://x.com/{t['username']}/status/mock",
            "published":        datetime.now(timezone.utc).isoformat(),
            "keywords_matched": kws,
            "fetched_at":       datetime.now(timezone.utc).isoformat(),
            "_is_mock":         True,
        })
    log.info(f"Mock: {len(items)} tweets simulados")
    return items


# ══════════════════════════════════════════════════════════════════════════════
# Main Runner
# ══════════════════════════════════════════════════════════════════════════════

def run(mock: bool = False) -> dict:
    mode_name = "MOCK" if mock else "SYNDICATION_BYPASS"
    log.info(f"=== Twitter/X Monitor — início ({mode_name}) ===")
    seen = load_cache()

    all_items = []
    if mock:
        all_items = fetch_mock()
    else:
        # Extração direta via Syndication Bypass oficial
        for profile in TWITTER_PROFILES:
            all_items.extend(fetch_syndication_profile(profile))

        # Se API v2 estiver configurada, tenta queries também (se der 402/payment required, avisa uma vez e ignora)
        if X_BEARER_TOKEN:
            try:
                api_items = fetch_api_v2(TWITTER_QUERIES)
                all_items.extend(api_items)
            except Exception as e:
                log.debug(f"API v2 opcional indisponível: {e}")

    # Deduplicar e filtrar hits
    new_items, hits = [], []
    for item in all_items:
        fp = _fp(item.get("url", "") + item.get("text", ""))
        if fp not in seen:
            seen.add(fp)
            new_items.append(item)
            if item.get("keywords_matched"):
                hits.append(item)

    log.info(f"Total: {len(all_items)} | Novos: {len(new_items)} | Hits: {len(hits)}")

    # Persistir hits
    for h in hits:
        with open(TWITTER_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(h, ensure_ascii=False) + "\n")

    save_cache(seen)

    summary = {
        "run_at":   datetime.now(timezone.utc).isoformat(),
        "mode":     mode_name.lower(),
        "total":    len(all_items),
        "new":      len(new_items),
        "hits":     len(hits),
        "top_hits": hits[:5],
    }

    print(f"\n[TWITTER-MONITOR] {len(hits)} hits relevantes de {len(new_items)} novos tweets | modo: {mode_name}")
    for h in hits[:5]:
        kws  = ", ".join(h.get("keywords_matched", [])[:3])
        text = h.get("text", "")[:80].replace("\n", " ").encode("ascii", errors="replace").decode("ascii")
        print(f"  [@{h.get('username','')}] {text} -- {kws}")

    return summary


if __name__ == "__main__":
    use_mock = "--mock" in sys.argv
    run(mock=use_mock)
