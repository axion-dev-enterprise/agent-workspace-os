"""
Motor 1: Descoberta e Scoring de Perfis Técnicos
================================================
Analisa perfis do X/Twitter candidatos a monitoramento técnico no ecossistema AXION.
Métricas avaliadas:
- Legibilidade e clareza da comunicação técnica
- Densidade de informação útil (código, papers, repositórios, arquitetura de agentes)
- Frequência e cadência de postagens
- Relação Sinal vs Ruído (SNR)

Arquitetura de Custo Consciente:
- Pré-filtro heurístico em Python puro (0 tokens)
- Avaliação semântica via OpenRouter com modelo econômico (max 350 tokens)
"""

import os
import re
import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import sys
# Workspace Root & Vault
WORKSPACE_ROOT = Path("c:/workspace")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

MEMORY_DIR = WORKSPACE_ROOT / "memory" / "intelligence"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

DISCOVERED_PROFILES_FILE = MEMORY_DIR / "discovered_profiles.json"
TWITTER_HITS_FILE = MEMORY_DIR / "twitter_hits.jsonl"

try:
    from scripts.vault_loader import load_vault
    load_vault()
except Exception:
    pass

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_FALLBACK_MODEL", "xiaomi/mimo-v2.6-flash")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PROFILE-DISCOVERY] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("profile_discovery")


def extract_candidate_handles_from_hits(limit: int = 50) -> list[str]:
    """Extrai menções (@handle) presentes nos tweets coletados na memória."""
    if not TWITTER_HITS_FILE.exists():
        return []

    candidates = set()
    known_ignored = {
        "cloudflare", "vercel", "nextjs", "tailscale", "github", "docker",
        "protonprivacy", "openai", "googledeepmind", "anthropicai", "sama",
        "karpathy", "ylecun", "ilyasut", "fchollet", "drjimfan", "hwchase17",
        "yoheinakajima", "swyx", "simonw", "officiallogank", "bindureddy", "_akhaliq"
    }

    try:
        with open(TWITTER_HITS_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-200:]
            for line in lines:
                try:
                    item = json.loads(line)
                    text = item.get("text", "")
                    mentions = re.findall(r"@([A-Za-z0-9_]{3,20})", text)
                    for m in mentions:
                        low = m.lower()
                        if low not in known_ignored and not low.isdigit():
                            candidates.add(m)
                except Exception:
                    continue
    except Exception as e:
        log.warning(f"Erro ao ler hits: {e}")

    return list(candidates)[:limit]


def fetch_profile_sample_tweets(handle: str, count: int = 5) -> list[str]:
    """Obtém amostra de tweets públicos recentes do perfil via Syndication."""
    import subprocess
    cmd = [
        "curl.exe", "-s", "-L",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=12)
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', res.stdout, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group(1))
        entries = data.get("props", {}).get("pageProps", {}).get("timeline", {}).get("entries", [])
        tweets = []
        for e in entries:
            t = e.get("content", {}).get("tweet")
            if t and t.get("full_text"):
                text = t.get("full_text")
                if not text.startswith("RT @"):
                    tweets.append(text)
            if len(tweets) >= count:
                break
        return tweets
    except Exception as e:
        log.warning(f"Erro ao buscar @{handle}: {e}")
        return []


def calculate_heuristic_score(tweets: list[str]) -> dict:
    """Calcula score heurístico determinístico (Custo 0 de tokens)."""
    if not tweets:
        return {"heuristic_score": 0, "has_code_or_links": False, "pass_filter": False}

    technical_words = {
        "llm", "llms", "agent", "agents", "model", "models", "rag", "benchmark", "paper", "papers",
        "eval", "evals", "context", "inference", "quantization", "gguf", "weights", "ai", "agi",
        "mcp", "prompt", "fine-tuning", "vllm", "transformers", "langgraph", "api", "apis", "gpu",
        "deepseek", "claude", "gemini", "gpt", "reasoning", "coding", "software", "compute", "tokens"
    }

    spam_words = {"airdrop", "presale", "crypto", "giveaway", "follow & rt", "100x gem", "nft", "casino"}

    total_words = 0
    tech_count = 0
    spam_count = 0
    links_count = 0
    code_count = 0

    for t in tweets:
        words = set(re.findall(r"\b[a-zA-Z_\-]{2,15}\b", t.lower()))
        total_words += len(words)
        tech_count += len(words.intersection(technical_words))
        spam_count += len(words.intersection(spam_words))
        if "http://" in t or "https://" in t or "github.com" in t or "arxiv.org" in t:
            links_count += 1
        if "```" in t or "import " in t or "def " in t or "class " in t:
            code_count += 1

    # Penalização drástica para spam
    if spam_count > 0:
        return {"heuristic_score": 10, "has_code_or_links": False, "pass_filter": False}

    tech_density = (tech_count / max(1, len(tweets))) * 20
    links_score = min(25, links_count * 6)
    code_score = min(20, code_count * 10)
    length_avg = sum(len(t) for t in tweets) / max(1, len(tweets))
    length_score = min(25, (length_avg / 120) * 25)

    score = min(100, int(tech_density + links_score + code_score + length_score))
    pass_filter = score >= 20

    return {
        "heuristic_score": score,
        "tech_count": tech_count,
        "has_code_or_links": links_count > 0 or code_count > 0,
        "pass_filter": pass_filter
    }


def call_openrouter_scoring(handle: str, tweets: list[str]) -> dict:
    """Chama OpenRouter para avaliação semântica concisa do perfil."""
    if not OPENROUTER_API_KEY:
        log.warning("OPENROUTER_API_KEY não definida. Usando score heurístico puro.")
        return {}

    sample_text = "\n---\n".join([t[:280] for t in tweets[:3]])
    prompt = (
        f"Analise este perfil do Twitter/X @{handle} com base na amostra de tweets abaixo.\n"
        f"Avalie estritamente a relevância técnica para AGENTES AUTÔNOMOS, LLMS, IA E ENGENHARIA DE SOFTWARE.\n"
        f"Retorne APENAS um objeto JSON válido no seguinte formato exato:\n"
        "{\n"
        '  "readability_score": <int 0-25>,\n'
        '  "technical_depth_score": <int 0-35>,\n'
        '  "actionability_score": <int 0-25>,\n'
        '  "signal_to_noise_score": <int 0-15>,\n'
        '  "total_score": <int 0-100>,\n'
        '  "primary_topics": ["<topico1>", "<topico2>"],\n'
        '  "one_line_verdict": "<resumo factual de 1 frase>",\n'
        '  "recommended_to_monitor": <true ou false>\n'
        "}\n\n"
        f"Amostra de Tweets de @{handle}:\n{sample_text}"
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Você é um auditor sênior de inteligência técnica em IA e Engenharia. Responda estritamente em JSON puro sem markdown."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.1,
    }

    try:
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            raw_text = msg.get("content") or msg.get("reasoning_content") or choice.get("text") or ""
            if not raw_text:
                return {}
            # Extrair bloco JSON se houver texto envolta
            json_match = re.search(r"\{[\s\S]*\}", raw_text)
            if json_match:
                return json.loads(json_match.group(0))
            return {}
    except Exception as e:
        log.warning(f"Erro OpenRouter scoring para @{handle}: {e}")
        return {}


def discover_and_evaluate_profiles(candidate_handles: list[str] = None) -> list[dict]:
    """Executa a descoberta e o scoring de novos perfis candidatos."""
    if not candidate_handles:
        candidate_handles = extract_candidate_handles_from_hits(limit=8)

    # Adicionar candidatos de referência padrão em IA caso a lista esteja curta
    defaults = [
        "antonosika", "jerryjliu0", "eugeneyan", "HamelHusain",
        "omarsanseviero", "tri_dao", "charlie_irl", "ClementDelangue"
    ]
    for d in defaults:
        if d not in candidate_handles and len(candidate_handles) < 12:
            candidate_handles.append(d)

    log.info(f"Avaliando {len(candidate_handles)} perfis candidatos...")
    results = []

    # Carregar banco existente
    existing = {}
    if DISCOVERED_PROFILES_FILE.exists():
        try:
            existing = json.loads(DISCOVERED_PROFILES_FILE.read_text("utf-8"))
        except Exception:
            existing = {}

    for handle in candidate_handles:
        # Se já foi avaliado há menos de 7 dias com score bom, reaproveita
        if handle in existing and (datetime.now(timezone.utc).timestamp() - existing[handle].get("timestamp", 0) < 86400 * 7):
            results.append(existing[handle])
            continue

        tweets = fetch_profile_sample_tweets(handle, count=4)
        if not tweets:
            log.info(f"@{handle}: nenhum tweet recuperado ou perfil fechado.")
            continue

        # 1. Heurística (Custo 0)
        h_res = calculate_heuristic_score(tweets)
        if not h_res["pass_filter"]:
            log.info(f"@{handle}: descartado no pré-filtro heurístico (score: {h_res['heuristic_score']}).")
            continue

        # 2. Avaliação Semântica (Econômica com LLM)
        llm_res = call_openrouter_scoring(handle, tweets)

        final_score = llm_res.get("total_score", h_res["heuristic_score"])
        recommended = llm_res.get("recommended_to_monitor", final_score >= 70)

        profile_card = {
            "handle": handle,
            "url": f"https://x.com/{handle}",
            "final_score": final_score,
            "readability": llm_res.get("readability_score", 15),
            "technical_depth": llm_res.get("technical_depth_score", 20),
            "actionability": llm_res.get("actionability_score", 15),
            "signal_to_noise": llm_res.get("signal_to_noise_score", 10),
            "primary_topics": llm_res.get("primary_topics", ["AI", "Agents"]),
            "verdict": llm_res.get("one_line_verdict", "Perfil técnico avaliado via heurística."),
            "recommended": recommended,
            "sample_tweet_count": len(tweets),
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc).timestamp()
        }

        existing[handle] = profile_card
        results.append(profile_card)
        log.info(f"@{handle}: Score {final_score}/100 | Recomendado: {recommended}")

    # Salvar cache
    DISCOVERED_PROFILES_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False), "utf-8")
    return results


if __name__ == "__main__":
    print("Iniciando Motor 1: Descoberta e Scoring de Perfis...")
    res = discover_and_evaluate_profiles(["antonosika", "jerryjliu0", "eugeneyan", "HamelHusain"])
    for r in res:
        print(f"[@{r['handle']}] Score: {r['final_score']} | Rec: {r['recommended']} | {r['verdict']}")
