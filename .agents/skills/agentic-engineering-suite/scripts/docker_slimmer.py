#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docker_slimmer.py — Automated Dockerfile & Container Slimming Engine
Part of agentic-engineering-suite skill — AXION Enterprise
Reduces image sizes by up to 90% using Multi-Stage Builds, Minimal Bases and .dockerignore audits.
Zero external dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


STANDARD_DOCKERIGNORE = """# Git metadata & versioning
.git
.github
.gitignore

# Environment & secrets (Rule #4 Vault protection)
.env
.env.*
vault/
*.pem
*.key

# Dependencies & build caches
node_modules/
.npm/
.pnpm-store/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage

# Temporary artifacts & system junk
temp/
tmp/
scratch/
memory/daily_logs/
*.log
.DS_Store
Thumbs.db

# Documentation & tests
docs/
tests/
test/
*.md
"""

NODE_MULTISTAGE_TEMPLATE = """# ── Stage 1: Build Dependencies & Source Compilation ─────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Install build dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build --if-present

# ── Stage 2: Minimal Production Runner ───────────────────────────────
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \\
    PORT=3000

# Install production-only packages
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

# Copy compiled artifacts from builder
COPY --from=builder /app/dist ./dist 2>/dev/null || true
COPY --from=builder /app/.next ./.next 2>/dev/null || true
COPY --from=builder /app/public ./public 2>/dev/null || true

# Non-root user for security hardening
USER node

EXPOSE 3000

CMD ["node", "dist/index.js"]
"""

PYTHON_MULTISTAGE_TEMPLATE = """# ── Stage 1: Wheels & Dependencies Builder ────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Minimal Distroless/Slim Production Runner ─────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PATH="/root/.local/bin:$PATH"

# Copy installed wheels and dependencies
COPY --from=builder /root/.local /root/.local

# Copy application source
COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def audit_dockerfile(dockerfile_path: Path) -> Dict[str, Any]:
    """Audits a Dockerfile against anti-bloat rules."""
    result = {
        "file": str(dockerfile_path),
        "exists": dockerfile_path.exists(),
        "score": 100,
        "is_multistage": False,
        "base_images": [],
        "findings": [],
        "recommendations": [],
    }

    if not dockerfile_path.exists():
        result["score"] = 0
        result["findings"].append("Dockerfile não encontrado.")
        return result

    content = dockerfile_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    from_stages = re.findall(r"^FROM\s+(\S+)(?:\s+[aA][sS]\s+(\S+))?", content, re.MULTILINE)
    result["base_images"] = [stage[0] for stage in from_stages]
    result["is_multistage"] = len(from_stages) > 1

    if not result["is_multistage"]:
        result["score"] -= 35
        result["findings"].append("Single-stage build detectado: Compiladores e dependências de desenvolvimento podem inchar a imagem final.")
        result["recommendations"].append("Adote Multi-Stage Build: Separe o estágio 'builder' (compilação) do estágio 'runner' (produção).")

    # Base image check
    for base in result["base_images"]:
        lower_base = base.lower()
        if "alpine" not in lower_base and "slim" not in lower_base and "distroless" not in lower_base:
            result["score"] -= 25
            result["findings"].append(f"Imagem base pesada detectada: '{base}' pode adicionar centenas de MB de overhead.")
            result["recommendations"].append(f"Substitua '{base}' por uma variante 'alpine' ou 'slim' (ex: node:22-alpine ou python:3.11-slim).")

    # Package cache check
    if "npm install" in content and "npm ci" not in content:
        result["score"] -= 10
        result["findings"].append("Uso de 'npm install' ao invés de 'npm ci'.")
        result["recommendations"].append("Utilize 'npm ci' para builds reproduzíveis e mais rápidos em containers.")

    if "pip install" in content and "--no-cache-dir" not in content:
        result["score"] -= 10
        result["findings"].append("Pip sem '--no-cache-dir': Caches locais de wheels acumulam megabytes desnecessários.")
        result["recommendations"].append("Adicione a flag '--no-cache-dir' aos comandos pip install.")

    # Dockerignore check in same directory
    dockerignore = dockerfile_path.parent / ".dockerignore"
    if not dockerignore.exists():
        result["score"] -= 20
        result["findings"].append("Arquivo '.dockerignore' ausente: Diretórios .git, node_modules ou segredos podem ser acidentalmente copiados para a imagem.")
        result["recommendations"].append("Crie um arquivo .dockerignore estrito para evitar poluição da imagem.")

    result["score"] = max(0, result["score"])
    return result


def generate_slimmer(target_dir: Path, tech: str) -> None:
    """Generates an optimized Dockerfile and .dockerignore for the selected technology."""
    target_dir.mkdir(parents=True, exist_ok=True)
    df_path = target_dir / "Dockerfile.optimized"
    di_path = target_dir / ".dockerignore"

    if tech.lower() == "python":
        template = PYTHON_MULTISTAGE_TEMPLATE
    else:
        template = NODE_MULTISTAGE_TEMPLATE

    df_path.write_text(template, encoding="utf-8")
    if not di_path.exists():
        di_path.write_text(STANDARD_DOCKERIGNORE, encoding="utf-8")

    print(f"✅ Dockerfile otimizado gerado em: {df_path}")
    print(f"✅ .dockerignore criado/verificado em: {di_path}")


def main():
    parser = argparse.ArgumentParser(description="Auditor e Otimizador de Containers Docker")
    parser.add_argument("path", nargs="?", default=".", help="Caminho do Dockerfile ou diretório a auditar")
    parser.add_argument("--generate", choices=["node", "python"], help="Gera um template Dockerfile multi-stage otimizado")
    parser.add_argument("--json", action="store_true", help="Saída em formato JSON estruturado")
    args = parser.parse_args()

    target = Path(args.path)

    if args.generate:
        generate_slimmer(target, args.generate)
        return

    dockerfile = target / "Dockerfile" if target.is_dir() else target
    report = audit_dockerfile(dockerfile)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("═════════════════════════════════════════════════════════════════════")
    print("           AXION DOCKER CONTAINER SLIMMER & AUDITOR                 ")
    print("═════════════════════════════════════════════════════════════════════")
    print(f"Alvo     : {report['file']}")
    print(f"Pontuação: {report['score']}/100")
    print(f"Multi-Stg: {'Sim (Otimizado)' if report['is_multistage'] else 'Não (Passível de Redução)'}")
    print(f"Bases    : {', '.join(report['base_images']) if report['base_images'] else 'Nenhuma'}")

    if report["findings"]:
        print("\n[Diagnóstico de Bloat & Riscos]")
        for f in report["findings"]:
            print(f"  ⚠️ {f}")

    if report["recommendations"]:
        print("\n[Ações Recomendadas (Redução ~90%)]")
        for r in report["recommendations"]:
            print(f"  💡 {r}")
    else:
        print("\n✅ O Dockerfile já segue os padrões modernos de containerização enxuta!")

    print("═════════════════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
