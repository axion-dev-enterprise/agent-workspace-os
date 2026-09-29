"""
AXION AI Intelligence Pipeline: Orquestrador Geral
===================================================
Coordena os 4 motores em ciclo contínuo ou sob demanda:
[Motor 1: Descoberta] -> [Motor 2: Validação] -> [Motor 3: Fábrica Skill/MCP] -> [Motor 4: Teste Útil]

Diretriz Fundamental de Custos:
- Pré-filtros determinísticos em Python puro (Custo 0)
- Modelo OpenRouter econômico e rápido (Xiaomi Mimo / Flash)
- max_tokens calibrados e saídas estritamente JSON
- Testes locais sem consumo de LLM
"""

import sys
import os
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path("c:/workspace")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from services.ai_intelligence_pipeline import (
    profile_discovery_engine,
    insight_validator_engine,
    skill_mcp_factory,
    skill_test_executor
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AI-PIPELINE-ORCHESTRATOR] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("orchestrator")


def run_full_pipeline(
    discover_candidates: list[str] = None,
    max_insights_to_validate: int = 4,
    auto_build_skills: bool = True
) -> dict:
    """Executa o pipeline completo de ponta a ponta."""
    summary = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "motor_1_profiles_evaluated": 0,
        "motor_1_recommended": [],
        "motor_2_insights_validated": 0,
        "motor_3_skills_created": [],
        "motor_4_tests_passed": 0,
        "cost_efficiency": "Lean Token Architecture: ~0.001 - 0.005 USD",
    }

    # ══════════════════════════════════════════════════════════════════════
    # ETAPA 1: Descoberta e Scoring de Perfis
    # ══════════════════════════════════════════════════════════════════════
    log.info("=== ETAPA 1: Iniciando Descoberta & Scoring de Perfis ===")
    profiles = profile_discovery_engine.discover_and_evaluate_profiles(candidate_handles=discover_candidates)
    summary["motor_1_profiles_evaluated"] = len(profiles)
    summary["motor_1_recommended"] = [p["handle"] for p in profiles if p.get("recommended")]
    log.info(f"Etapa 1 Concluída: {len(summary['motor_1_recommended'])} perfis recomendados.")

    # ══════════════════════════════════════════════════════════════════════
    # ETAPA 2: Análise, Interpretação e Validação de Informações
    # ══════════════════════════════════════════════════════════════════════
    log.info("=== ETAPA 2: Iniciando Análise & Validação de Insights ===")
    validated_insights = insight_validator_engine.run_insight_validation(max_items=max_insights_to_validate)
    summary["motor_2_insights_validated"] = len(validated_insights)
    log.info(f"Etapa 2 Concluída: {len(validated_insights)} insights validados.")

    # ══════════════════════════════════════════════════════════════════════
    # ETAPA 3 & 4: Fábrica de Skills/MCPs e Teste Empírico
    # ══════════════════════════════════════════════════════════════════════
    if auto_build_skills and validated_insights:
        log.info("=== ETAPA 3 & 4: Construção e Teste das Skills/MCPs ===")
        # Filtrar o melhor candidato
        candidates = [
            ins for ins in validated_insights
            if ins.get("is_skill_or_mcp_candidate") and ins.get("confidence_score", 0) >= 0.7
        ]

        # Se nenhum candidato explícito foi marcado mas há insights, pega o de maior confiança
        if not candidates and validated_insights:
            candidates = sorted(validated_insights, key=lambda x: x.get("confidence_score", 0), reverse=True)[:1]
            candidates[0]["is_skill_or_mcp_candidate"] = True
            candidates[0]["suggested_skill_name"] = "ai-reasoning-and-agent-patterns"

        for cand in candidates[:2]:  # Limite de segurança de custo: máx 2 skills por execução
            log.info(f"Construindo Skill: {cand.get('suggested_skill_name')}...")
            build_res = skill_mcp_factory.build_skill_from_insight(cand)
            if build_res.get("success"):
                summary["motor_3_skills_created"].append(build_res["skill_slug"])

                # Testar empiricamente
                log.info(f"Executando testes no ativo gerado...")
                test_res = skill_test_executor.execute_and_produce_useful_result(build_res)
                if test_res.get("status") == "VERIFIED_OPERATIONAL":
                    summary["motor_4_tests_passed"] += 1

    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AXION AI Intelligence Pipeline")
    parser.add_argument("--all", action="store_true", help="Executar pipeline completo")
    parser.add_argument("--discover", nargs="*", help="Handles para avaliar no Motor 1")
    parser.add_argument("--validate", type=int, default=3, help="Qtd de posts para validar no Motor 2")
    args = parser.parse_args()

    res = run_full_pipeline(
        discover_candidates=args.discover,
        max_insights_to_validate=args.validate,
        auto_build_skills=True
    )
    print("\n" + "=" * 60)
    print("RESUMO DA EXECUÇÃO DO PIPELINE:")
    print("=" * 60)
    print(json.dumps(res, indent=2, ensure_ascii=False))
