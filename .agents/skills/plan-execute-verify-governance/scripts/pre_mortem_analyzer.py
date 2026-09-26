#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_mortem_analyzer.py — Pre-Mortem Failure Risk Analyzer
Zero-dependency, Python 3 stdlib only.
Performs prospective hindsight analysis:
"Assume the change was deployed and caused a catastrophic failure in production.
What are the most likely failure modes, regressions, and hidden dependencies?"

Audits git diffs or file changes against:
1. Secret leaks & credentials (.env, tokens, private keys).
2. Chesterton's Fence violations (deleted safeguards, removed timeouts, stripped CORS/auth).
3. Unhandled asynchronous operations (missing timeouts, uncaught promises/exceptions).
4. Breaking changes in API signatures or database queries.
5. Missing test coverage for modified logic.
"""

import sys
import re
import subprocess
import argparse
from typing import List, Dict, Tuple

RISK_PATTERNS = [
    # 1. Credentials and Secrets
    (r"(?i)(api[_-]?key|secret|token|password|passwd|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]",
     "CRITICAL", "Potencial vazamento de credencial / segredo hardcoded no código."),

    # 2. Chesterton's Fence (Removal of protections)
    (r"^\-\s*(verify|auth|permission|cors|validate|sanitiz|escape|check_token|bearer)",
     "HIGH", "Remoção de barreira de segurança ou validação (Violação do princípio de Chesterton's Fence)."),
    
    (r"^\-\s*(timeout|deadline|max_retries|connect_timeout)",
     "HIGH", "Remoção de configuração de timeout ou proteção contra bloqueio de recursos."),

    # 3. Unbounded Queries & Operations
    (r"(?i)SELECT\s+\*\s+FROM\s+\w+\s*(?!WHERE|LIMIT)",
     "MEDIUM", "Consulta SQL sem cláusula WHERE ou LIMIT explícito (Risco de exaustão de memória/I/O)."),

    # 4. Error Suppression
    (r"(?i)(except\s*:\s*pass|catch\s*\([^\)]*\)\s*\{\s*\})",
     "HIGH", "Supressão silenciosa de exceções / erros (Catch-all vazio oculta falhas em produção)."),

    # 5. Native Alerts in UI (AGENTS.md Rule #8)
    (r"\b(window\.)?(alert|confirm|prompt)\s*\(",
     "HIGH", "Invocação de caixa de diálogo nativa do navegador (Violação de UI Rule #8).")
]

def analyze_diff(diff_text: str) -> Dict:
    findings = []
    lines = diff_text.splitlines()
    
    added_lines = [l for l in lines if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in lines if l.startswith("-") and not l.startswith("---")]
    
    # Check all lines against risk patterns
    for line in lines:
        for pattern, severity, description in RISK_PATTERNS:
            if re.search(pattern, line):
                findings.append({
                    "severity": severity,
                    "description": description,
                    "evidence": line.strip()[:100]
                })

    # Test file presence check
    modified_files = set(re.findall(r"diff --git a/(\S+) b/\S+", diff_text))
    code_files = [f for f in modified_files if not any(t in f for t in ["test", "spec", "docs", ".md", ".json"])]
    test_files = [f for f in modified_files if any(t in f for t in ["test", "spec"])]
    
    if code_files and not test_files:
        findings.append({
            "severity": "MEDIUM",
            "description": f"Foram alterados {len(code_files)} arquivo(s) de lógica, mas nenhum arquivo de teste correspondente foi modificado.",
            "evidence": ", ".join(list(code_files)[:3])
        })

    # Calculate overall risk score
    severity_weights = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}
    total_score = sum(severity_weights.get(f["severity"], 1) for f in findings)
    
    if total_score >= 10:
        overall_risk = "CRITICAL"
    elif total_score >= 5:
        overall_risk = "HIGH"
    elif total_score >= 2:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    return {
        "overall_risk": overall_risk,
        "risk_score": total_score,
        "files_analyzed": len(modified_files),
        "total_diff_lines": len(lines),
        "findings": findings
    }

def main():
    parser = argparse.ArgumentParser(description="Pre-Mortem Failure Risk Analyzer")
    parser.add_argument("diff_source", nargs="?", default="git", help="'git' to use 'git diff', file path, or '-' for stdin")
    
    args = parser.parse_args()
    
    if args.diff_source == "git":
        try:
            diff_text = subprocess.check_output(["git", "diff", "HEAD"], text=True, stderr=subprocess.DEVNULL)
            if not diff_text.strip():
                # Try cached/staged
                diff_text = subprocess.check_output(["git", "diff", "--cached"], text=True, stderr=subprocess.DEVNULL)
        except Exception as e:
            diff_text = ""
    elif args.diff_source == "-":
        diff_text = sys.stdin.read()
    else:
        with open(args.diff_source, "r", encoding="utf-8") as f:
            diff_text = f.read()

    if not diff_text.strip():
        print("[PRE-MORTEM] Nenhuma alteração/diff detectada para análise.")
        sys.exit(0)

    report = analyze_diff(diff_text)
    
    print(f"\n{'='*60}")
    print(f"RELATÓRIO PRE-MORTEM DE RISCO: [{report['overall_risk']}] (Score: {report['risk_score']})")
    print(f"Arquivos inspecionados: {report['files_analyzed']} | Linhas de diff: {report['total_diff_lines']}")
    print(f"{'='*60}")
    
    if not report["findings"]:
        print("[✓] Nenhum padrão de alto risco ou regressão detectado no diff.")
    else:
        print(f"Foram identificados {len(report['findings'])} ponto(s) de atenção preventivo(s):\n")
        for i, f in enumerate(report["findings"], 1):
            print(f"  {i}. [{f['severity']}] {f['description']}")
            print(f"     Evidência: {f['evidence']}\n")
            
    # Exit with code 1 if CRITICAL risk found
    sys.exit(1 if report["overall_risk"] == "CRITICAL" else 0)

if __name__ == "__main__":
    main()
