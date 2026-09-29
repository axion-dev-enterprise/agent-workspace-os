"""
Motor 2: Análise, Interpretação e Validação de Informações
==========================================================
Processa os posts/tweets técnicos coletados, filtra marketing oco,
interpreta as nuances da arquitetura e valida se as afirmações
têm fundamentação técnica comprovável (papers, repositórios, benchmarks).

Arquitetura de Custo Consciente:
- Pré-filtra tweets com Python regex (elimina opiniões vagas ou posts curtos)
- Extrai somente os posts com alta densidade técnica
- Faz requisições compactas ao OpenRouter estruturadas em JSON
"""

import os
import re
import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import sys
WORKSPACE_ROOT = Path("c:/workspace")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

MEMORY_DIR = WORKSPACE_ROOT / "memory" / "intelligence"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

TWITTER_HITS_FILE = MEMORY_DIR / "twitter_hits.jsonl"
VALIDATED_INSIGHTS_FILE = MEMORY_DIR / "validated_insights.jsonl"
VALIDATED_CACHE_FILE = MEMORY_DIR / "validated_cache.json"

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
    format="%(asctime)s [INSIGHT-VALIDATOR] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("insight_validator")


def load_validated_cache() -> set:
    if VALIDATED_CACHE_FILE.exists():
        try:
            return set(json.loads(VALIDATED_CACHE_FILE.read_text("utf-8")).get("seen_urls", []))
        except Exception:
            pass
    return set()


def save_validated_cache(seen: set):
    VALIDATED_CACHE_FILE.write_text(
        json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "seen_urls": list(seen)[-3000:]}),
        "utf-8"
    )


def extract_high_density_candidates(limit: int = 15) -> list[dict]:
    """Seleciona posts com maior densidade de informação técnica para análise."""
    if not TWITTER_HITS_FILE.exists():
        return []

    seen = load_validated_cache()
    candidates = []

    priority_keywords = [
        "agent", "agents", "langgraph", "mcp", "reasoning", "benchmark",
        "eval", "inference", "quantization", "rag", "claude", "deepseek",
        "gemini", "openai", "vllm", "tool", "function calling"
    ]

    try:
        with open(TWITTER_HITS_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            # Iterar dos mais novos para os mais antigos
            for line in reversed(lines):
                if len(candidates) >= limit:
                    break
                try:
                    item = json.loads(line)
                    url = item.get("url", "")
                    if url in seen:
                        continue
                    text = item.get("text", "")
                    # Filtro de tamanho mínimo e relevância
                    if len(text) < 50:
                        continue
                    low = text.lower()
                    score = sum(1 for kw in priority_keywords if kw in low)
                    if score >= 1:
                        candidates.append(item)
                except Exception:
                    continue
    except Exception as e:
        log.warning(f"Erro ao extrair candidatos: {e}")

    return candidates


def validate_and_interpret_post(post: dict) -> dict | None:
    """Interpreta e valida um post usando OpenRouter de forma ultra-econômica."""
    if not OPENROUTER_API_KEY:
        log.warning("OPENROUTER_API_KEY ausente.")
        return None

    text = post.get("text", "")
    author = post.get("username", "desconhecido")
    url = post.get("url", "")

    prompt = (
        f"Analise o seguinte post técnico publicado por @{author} no X/Twitter:\n\n"
        f"\"\"\"{text}\"\"\"\n\n"
        "Sua tarefa é INTERPRETAR tecnicamente e VALIDAR a informação.\n"
        "Retorne APENAS um JSON válido estritamente com este formato:\n"
        "{\n"
        '  "headline": "<resumo factual em 1 frase>",\n'
        '  "category": "<AGENT_FRAMEWORK|REASONING_LLM|MCP_PROTOCOL|RAG_OPTIMIZATION|LOCAL_INFERENCE|INFRA_OPS>",\n'
        '  "technical_essence": "<explicação da arquitetura ou inovação técnica em 2 frases>",\n'
        '  "is_factual_and_useful": <true ou false>,\n'
        '  "confidence_score": <float 0.0 a 1.0>,\n'
        '  "actionable_takeaway": "<como engenheiros ou agentes podem aplicar isso na prática>",\n'
        '  "is_skill_or_mcp_candidate": <true ou false>,\n'
        '  "suggested_skill_name": "<nome-em-kebab-case caso seja candidato, ou null>"\n'
        "}"
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Você é um auditor rigoroso de engenharia de software e IA. Responda estritamente em JSON puro sem texto ao redor."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400,
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
                return None
            json_match = re.search(r"\{[\s\S]*\}", raw_text)
            if not json_match:
                return None
            parsed = json.loads(json_match.group(0))
            parsed["source_author"] = author
            parsed["source_url"] = url
            parsed["source_text"] = text[:200]
            parsed["analyzed_at"] = datetime.now(timezone.utc).isoformat()
            return parsed
    except Exception as e:
        log.warning(f"Erro ao validar insight do post de @{author}: {e}")
        return None


def run_insight_validation(max_items: int = 5) -> list[dict]:
    """Executa a validação de novos insights a partir dos hits coletados."""
    candidates = extract_high_density_candidates(limit=max_items)
    if not candidates:
        log.info("Nenhum post novo com densidade técnica para validar.")
        return []

    log.info(f"Validando {len(candidates)} posts de alta densidade via OpenRouter...")
    validated_list = []
    seen = load_validated_cache()

    for post in candidates:
        url = post.get("url", "")
        res = validate_and_interpret_post(post)
        seen.add(url)
        if res and res.get("is_factual_and_useful"):
            validated_list.append(res)
            # Persistir no JSONL
            with open(VALIDATED_INSIGHTS_FILE, "a", encoding="utf-8") as out:
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
            log.info(f"[VALIDADO] ({res.get('category')}): {res.get('headline')[:60]}... | Skill?: {res.get('is_skill_or_mcp_candidate')}")

    save_validated_cache(seen)
    return validated_list


if __name__ == "__main__":
    print("Iniciando Motor 2: Análise, Interpretação e Validação...")
    insights = run_insight_validation(max_items=3)
    print(f"Total validados: {len(insights)}")
    for ins in insights:
        print(f"- [{ins['category']}] {ins['headline']} (Confiança: {ins['confidence_score']}) -> Skill: {ins['suggested_skill_name']}")
