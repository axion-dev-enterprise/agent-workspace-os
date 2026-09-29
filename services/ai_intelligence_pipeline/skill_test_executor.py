"""
Motor 4: Executor de Testes Empíricos e Geração de Resultados Úteis
===================================================================
Executa testes determinísticos nas skills e conectores MCP criados:
1. Validação estática de conformidade com AGENTS.md (frontmatter YAML, seções obrigatórias)
2. Teste sintático e compilação AST do código Python gerado
3. Teste de execução pontual do MCP / rotina gerada
4. Geração de um resultado útil tangível e mensurável

Arquitetura de Custo Consciente:
- Testes 100% locais no ambiente Windows sem consumo de API externa (Custo = 0 tokens)
- Rastreamento rigoroso de consumo financeiro da pipeline
"""

import sys
import os
import ast
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path("c:/workspace")
MEMORY_DIR = WORKSPACE_ROOT / "memory" / "intelligence"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_FILE = MEMORY_DIR / "pipeline_execution_results.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SKILL-TEST-EXECUTOR] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("skill_test_executor")


def test_skill_markdown_integrity(skill_path: str) -> dict:
    """Valida se a SKILL.md segue os padrões estruturais de governança."""
    p = Path(skill_path)
    if not p.exists():
        return {"passed": False, "error": f"Arquivo não encontrado: {skill_path}"}

    content = p.read_text(encoding="utf-8", errors="replace")

    checks = {
        "has_yaml_frontmatter": content.startswith("---") and "---" in content[3:],
        "has_name_in_frontmatter": "name:" in content[:300],
        "has_description_in_frontmatter": "description:" in content[:300],
        "has_overview_section": "## 1." in content or "Visão Geral" in content,
        "has_code_examples": "```python" in content or "```powershell" in content or "```bash" in content,
        "length_sufficient": len(content) > 600
    }

    passed = all(checks.values())
    return {
        "passed": passed,
        "details": checks,
        "file_size_bytes": len(content)
    }


def test_mcp_server_execution(mcp_path: str) -> dict:
    """Executa o script do conector MCP em subprocess para validar se executa sem erros."""
    if not mcp_path:
        return {"passed": True, "skipped": True, "reason": "Nenhum conector MCP associado"}

    p = Path(mcp_path)
    if not p.exists():
        return {"passed": False, "error": f"Arquivo MCP não encontrado: {mcp_path}"}

    # 1. Teste de Sintaxe AST Python puro (Custo 0)
    try:
        source = p.read_text(encoding="utf-8")
        ast.parse(source)
    except SyntaxError as se:
        return {"passed": False, "error": f"Erro de sintaxe Python no conector: {se}"}

    # 2. Execução de teste local (sem rede ou APIs pagas)
    try:
        cmd = ["python", str(p)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode != 0:
            return {"passed": False, "error": f"Falha na execução: {res.stderr}"}

        out = res.stdout.strip()
        data = json.loads(out)
        return {
            "passed": True,
            "output_preview": data,
            "execution_verified": True
        }
    except Exception as e:
        return {"passed": False, "error": f"Erro durante teste do MCP: {e}"}


def execute_and_produce_useful_result(skill_build_result: dict) -> dict:
    """Executa a bateria de testes e produz um resultado útil comprovado."""
    skill_path = skill_build_result.get("skill_path")
    mcp_path = skill_build_result.get("mcp_path")
    skill_slug = skill_build_result.get("skill_slug", "unknown")

    log.info(f"Testando integridade da skill: {skill_slug}...")
    skill_audit = test_skill_markdown_integrity(skill_path)

    log.info(f"Testando conector MCP associado: {mcp_path or 'Nenhum'}...")
    mcp_audit = test_mcp_server_execution(mcp_path)

    all_passed = skill_audit["passed"] and mcp_audit["passed"]

    # Produzir o resultado útil tangível
    useful_result = {
        "skill_slug": skill_slug,
        "status": "VERIFIED_OPERATIONAL" if all_passed else "FAILED_VERIFICATION",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill_audit": skill_audit,
        "mcp_audit": mcp_audit,
        "deliverables": {
            "canonical_skill_file": skill_path,
            "executable_connector": mcp_path,
            "readiness": "Pronto para uso por agentes de IA e humanos no workspace"
        },
        "cost_efficiency": {
            "test_token_cost": 0,
            "test_strategy": "100% Deterministic Local Ast & Process Execution",
            "waste_avoidance": "Zero chamadas pagas de LLM durante fase de testes"
        }
    }

    # Salvar no histórico de resultados
    history = []
    if RESULTS_FILE.exists():
        try:
            history = json.loads(RESULTS_FILE.read_text("utf-8"))
        except Exception:
            history = []

    history.append(useful_result)
    RESULTS_FILE.write_text(json.dumps(history[-50:], indent=2, ensure_ascii=False), "utf-8")

    log.info(f"Resultado útil produzido com sucesso para {skill_slug}. Status: {useful_result['status']}")
    return useful_result


if __name__ == "__main__":
    test_result = {
        "skill_slug": "mcp-agent-tool-orchestrator",
        "skill_path": "c:/workspace/.agents/skills/mcp-agent-tool-orchestrator/SKILL.md",
        "mcp_path": "c:/workspace/packages/mcp-connectors/mcp-agent-tool-orchestrator/server.py"
    }
    out = execute_and_produce_useful_result(test_result)
    print(json.dumps(out, indent=2))
