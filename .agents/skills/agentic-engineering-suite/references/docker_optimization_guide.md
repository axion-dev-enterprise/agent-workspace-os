# Docker Container Optimization & Extreme Slimming Runbook

Este runbook documenta a metodologia canônica para redução de tamanho de imagens Docker em até **90%** (de ~2 GB para ~150 MB), eliminando bloat, compiladores e arquivos desnecessários na imagem de produção.

---

## 1. As 3 Leis da Containerização Enxuta

### 1.1 Multi-Stage Builds (Separação Builder vs. Runner)
- **Estágio Builder (`AS builder`)**: Instala compiladores (`gcc`, `g++`, `python-dev`), devDependencies (`typescript`, linters, test runners, bundlers) e executa a compilação (`npm run build` ou `cargo build` ou `pip wheel`).
- **Estágio Runner (`AS runner`)**: Parte de uma imagem base mínima limpa. Copia **estritamente os artefatos compilados** (`dist/`, `.next/standalone`, binários) e dependências de produção (`npm ci --omit=dev` ou wheels instalados).
- **Resultado**: Todas as ferramentas de compilação e caches são descartados no primeiro estágio.

### 1.2 Imagens Base Mínimas (Alpine vs. Distroless vs. Slim)
| Base Image | Tamanho Típico | Casos de Uso Recomendados |
| :--- | :--- | :--- |
| `node:22-alpine` | ~50 MB | Aplicações Node.js, Next.js, Express, Fastify com dependências puras JS |
| `gcr.io/distroless/nodejs` | ~30 MB | Máxima segurança (zero shell, zero package manager, zero utilitários) |
| `python:3.11-slim` | ~120 MB | Aplicações Python (FastAPI/Flask) que necessitam de libc compatível |
| `alpine:latest` | ~5 MB | Microsserviços compilados em Go, Rust ou C++ estático |

### 1.3 O Arquivo `.dockerignore` Mandatório
Qualquer build de container DEVE conter um arquivo `.dockerignore` ao lado do `Dockerfile`, excluindo:
- `.git` e `.github` (evita leak de histórico e metadados).
- `.env*` e `vault/` (bloqueio inegociável de segredos locais - Regra #4).
- `node_modules/` local (evita transferir dependências da arquitetura do host para dentro do Linux do container).
- Diretórios de cache, temporários e documentação (`temp/`, `scratch/`, `tests/`, `docs/`, `*.log`).

---

## 2. Templates Canônicos Otimizados

### Node.js (Next.js / SSR / Microservices)
```dockerfile
# ── Stage 1: Build Dependencies & Source Compilation ─────────────────
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build --if-present

# ── Stage 2: Minimal Production Runner ───────────────────────────────
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=builder /app/dist ./dist 2>/dev/null || true
COPY --from=builder /app/.next ./.next 2>/dev/null || true
COPY --from=builder /app/public ./public 2>/dev/null || true
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Python (FastAPI / Asynchronous APIs)
```dockerfile
# ── Stage 1: Wheels Builder ──────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Slim Production Runner ──────────────────────────────────
FROM python:3.11-slim AS runner
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/root/.local/bin:$PATH"
COPY --from=builder /root/.local /root/.local
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 3. Automação via CLI
A skill disponibiliza o utilitário `scripts/docker_slimmer.py` para automatizar auditorias e geração de templates:
```bash
# Auditar um Dockerfile existente
python .agents/skills/agentic-engineering-suite/scripts/docker_slimmer.py services/axion-flow/Dockerfile

# Gerar template otimizado para Node.js
python .agents/skills/agentic-engineering-suite/scripts/docker_slimmer.py --generate node my-service/
```
