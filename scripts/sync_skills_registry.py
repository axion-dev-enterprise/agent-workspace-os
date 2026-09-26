#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canonical Skills Registry Synchronizer — AXION Enterprise
Scans .agents/skills/ for all SKILL.md definitions, extracts metadata,
and automatically synchronizes:
1. docs/SKILLS_REGISTRY.md (Full documentation catalog)
2. AGENTS.md (Dynamic markdown table between <!-- SKILLS_REGISTRY_START --> and <!-- SKILLS_REGISTRY_END -->)
3. workspace/inventory.json (Updates active skills list)
"""

import os
import re
import json
import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(r"C:\workspace")
SKILLS_DIR = WORKSPACE_ROOT / ".agents" / "skills"
GLOBAL_SKILLS_DIR = Path(os.path.expanduser(r"~\.gemini\antigravity\skills"))
AGENTS_MD_PATH = WORKSPACE_ROOT / "AGENTS.md"
SKILLS_REGISTRY_MD_PATH = WORKSPACE_ROOT / "docs" / "SKILLS_REGISTRY.md"
INVENTORY_JSON_PATH = WORKSPACE_ROOT / "workspace" / "inventory.json"

DOMAIN_MAP = {
    # 1. Core Integrations
    "gam-ops": ("Google Workspace", "Drive, Gmail, Docs, Sheets, OUs, Service Accounts e Domain-wide Delegation"),
    "cloudflare-edge-ops": ("Edge & Serverless", "Workers, Pages, D1 SQL, KV, R2 Storage, Queues e DNS example.com"),
    "tailwind-shadcn-ux": ("UI/UX & Design", "Design tokens, componentes Radix UI (WCAG AAA), Dark/Light mode, microinterações e skeleton loaders"),
    "threejs-gsap-animation": ("2D/3D & Animações", "Cenas 3D Three.js / React Three Fiber, shaders GLSL, modelos Draco e GSAP ScrollTrigger"),
    "modern-responsive-architect": ("Layout & Responsividade", "Container Queries (@container), Subgrid, fontes fluidas com clamp(), viewports dvh/svh"),
    "web-security-pentest": ("Segurança & Pentest", "Auditoria OWASP Top 10, prevenção de Subdomain Takeover (124 subdomínios), secret scanning e WAF"),
    "meta-marketing-capi": ("Meta Ecosystem", "Meta Conversions API (CAPI server-side), UTM tracking, Meta Ads Graph API e WhatsApp Cloud API"),
    "gcp-cloud-ops": ("Google Cloud Platform", "Cloud Run, Secret Manager, Cloud Storage, Artifact Registry, IAM e políticas organizacionais GCP"),
    "gemini-multimodal-agent": ("IA & Engenharia de Agentes", "Gemini 1.5/2.0 Pro e Flash, Function Calling determinístico, Pydantic Structured Outputs e áudio/vídeo"),
    "vps-docker-orchestration": ("Nós VPS & Docker", "Administração remota Linux, Docker multi-stage builds, Docker Compose em produção, PM2 e systemd"),
    "tailscale-mesh-vpn": ("Rede & Conectividade", "Rede mesh WireGuard privada, nós remotos, MagicDNS, Tailscale SSH e Funnel"),

    # 2. Backend & APIs
    "fastapi-async-api": ("Backend & APIs", "APIs assíncronas em Python com Pydantic v2, dependency injection, background tasks e OpenAPI"),
    "nestjs-modular-backend": ("Backend & APIs", "Arquitetura modular corporativa em TypeScript com NestJS, Guards, Interceptors e DTOs"),
    "graphql-apollo-federation": ("Backend & APIs", "Design de esquemas GraphQL, resolvers tipados, caching e Apollo Federation em microserviços"),
    "stripe-payments-engine": ("Backend & APIs", "Checkout global, verificação de webhooks, assinaturas recorrentes e split de pagamentos com Stripe"),
    "grpc-protobuf-microservices": ("Backend & APIs", "Comunicação inter-serviços de alta taxa de transferência com gRPC e Protocol Buffers"),

    # 3. Databases & Caching
    "postgresql-advanced-optimization": ("Databases & Caching", "Otimização de PostgreSQL, tuning de índices (B-Tree, GIN, BRIN), EXPLAIN ANALYZE e pooling"),
    "redis-caching-queues": ("Databases & Caching", "Cache estratégico, estruturas Redis 7 (Hashes, Sets, Streams), BullMQ e locks distribuídos (Redlock)"),
    "prisma-drizzle-orm": ("Databases & Caching", "Migrations automatizadas, consultas seguras com tipagem estrita e edge compatibility em Drizzle e Prisma"),
    "mongodb-aggregation-pipeline": ("Databases & Caching", "Pipelines de agregação complexos, indexação composta e change streams no MongoDB"),
    "qdrant-vector-database": ("Databases & Caching", "Busca vetorial, coleções semânticas, filtragem de payloads e integração com RAG no Qdrant"),

    # 4. Frontend & Mobile
    "nextjs-app-router-rsc": ("Frontend & Mobile", "Arquitetura Next.js 15, React Server Components (RSC), Server Actions, Suspense e streaming"),
    "react-query-tanstack": ("Frontend & Mobile", "Gerenciamento de estado assíncrono, cache inteligente, revalidação e mutações com TanStack Query v5"),
    "state-zustand-jotai": ("Frontend & Mobile", "Estado global leve, atômico e determinístico com Zustand e Jotai (sem boilerplate)"),
    "react-native-expo": ("Frontend & Mobile", "Desenvolvimento mobile multiplataforma (iOS e Android) com Expo Router e React Native"),
    "web-vitals-performance": ("Frontend & Mobile", "Otimização de Core Web Vitals (LCP, INP, CLS), auditoria Lighthouse 100/100 e code-splitting"),

    # 5. DevOps & Observability
    "github-actions-cicd": ("DevOps & CI/CD", "Pipelines de CI/CD automatizadas, testes em matriz, builds multi-plataforma e deploy seguro via OIDC"),
    "kubernetes-k8s-manifests": ("DevOps & CI/CD", "Orquestração de pods, deployments, ingress, autoscaling e manifestos K8s/K3s"),
    "terraform-iac-automation": ("DevOps & CI/CD", "Infraestrutura como Código (IaC) com Terraform, módulos reutilizáveis e gestão de estado seguro"),
    "prometheus-grafana-metrics": ("DevOps & CI/CD", "Exposição de métricas RED/USE, configuração de painéis no Grafana e alertas em tempo real"),
    "sentry-error-tracking": ("DevOps & CI/CD", "Monitoramento de erros em tempo real, upload de source maps, session replay e profiling com Sentry"),

    # 6. AI & Machine Learning
    "langchain-langgraph-orchestration": ("IA & Engenharia de Agentes", "Orquestração de agentes cíclicos com estado, LangGraph, roteamento de ferramentas e memória persistente"),
    "rag-chunking-embeddings": ("IA & Engenharia de Agentes", "Pipelines de RAG avançado, divisão semântica de texto (chunking), busca híbrida BM25 + Vetorial e re-ranking"),
    "prompt-engineering-jailbreak-defense": ("IA & Engenharia de Agentes", "Engenharia de prompts robusta, defesa contra injeção de prompt (prompt injection) e estruturação de contexto"),
    "whisper-stt-neural-voice": ("IA & Engenharia de Agentes", "Transcrição de áudio com OpenAI Whisper, diarização de locutores e tratamento de ruído acústico"),
    "elevenlabs-tts-voiceover": ("IA & Engenharia de Agentes", "Síntese de voz neural ultrarrealista com ElevenLabs API, controle emocional e streaming de áudio"),
    "token-reduction-context-compression": ("IA & Engenharia de Agentes", "Otimização agressiva de tokens, compressão AST de código, minificação JSON, condensação de logs de CLI e padrão Ponytail YAGNI"),
    "plan-execute-verify-governance": ("IA & Engenharia de Agentes", "Ciclo Plan-Execute-Verify (PEV), portão de verificação empírica, análise pre-mortem de risco e arquitetura ADR"),

    # 7. Testing & Automation
    "playwright-e2e-testing": ("Testing & QA", "Testes end-to-end automatizados com Playwright, regressão visual, gravação de traces e execução headless"),
    "pytest-mocking-fixtures": ("Testing & QA", "Testes unitários e de integração em Python com Pytest, fixtures parametrizadas, mocking e cobertura"),
    "web-scraping-crawling": ("Automação & Scraping", "Extração de dados resiliente, bypass de anti-bot, Playwright headless, Beautiful Soup e rotação de proxies"),
    "seo-technical-structured-data": ("SEO & Performance", "SEO técnico, Schema.org JSON-LD, metatags OpenGraph/Twitter, sitemaps XML e indexação no Google"),
    "pdf-generation-puppeteer": ("Automação de Documentos", "Geração de relatórios PDF pixel-perfect a partir de HTML/CSS com Puppeteer/Playwright e print styles"),

    # 8. SRE, Cloud & Specialized Operations
    "cron-scheduled-tasks": ("Automação & SRE", "Windows Task Scheduler, Linux Systemd Timers, Cloudflare Cron Triggers e GitHub Scheduled Workflows"),
    "vercel-deployment-ops": ("DevOps & Deploy", "Gestão do escopo your-team-slug, 11 projetos em produção, preview branches, domains e rollback"),
    "postgresql-dba-maintenance": ("Databases & Caching", "Manutenção preventiva de PostgreSQL 15/16, VACUUM ANALYZE, index bloat, pooling e queries lentas"),
    "cloudflare-zero-trust-tunnels": ("Segurança & Rede", "Cloudflare Zero Trust, túneis cloudflared, eliminação de portas públicas, WAF e Access"),
    "whatsapp-baileys-bot-ops": ("Comunicação & Mensageria", "Arquitetura Baileys WhatsApp bot, reconexões resilientes, auth state e dispatch de webhooks"),
    "telegram-bot-ops": ("Comunicação & Mensageria", "Telegram Bot API, BotFather metadados, comandos, inline keyboards, SRE alerts e daemons")
}

def parse_frontmatter(content: str):
    """Extracts YAML frontmatter name and description from SKILL.md"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return None, None
    frontmatter = match.group(1)
    
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else None
    
    desc_match = re.search(r"^description:\s*(?:>-\s*\n|\s*)(.*?)(?=\n\w+:|\Z)", frontmatter, re.DOTALL | re.MULTILINE)
    desc = ""
    if desc_match:
        desc = " ".join([line.strip() for line in desc_match.group(1).strip().splitlines() if line.strip()])
        
    return name, desc

def scan_skills():
    """Scans all skills in .agents/skills/"""
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_path in sorted(SKILLS_DIR.iterdir()):
        if skill_path.is_dir():
            skill_md = skill_path / "SKILL.md"
            if skill_md.exists():
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    name, desc = parse_frontmatter(content)
                    if not name:
                        name = skill_path.name
                    
                    domain, scope = DOMAIN_MAP.get(name, ("Geral / Utilitário", desc or "Skill operacional especializada"))
                    skills.append({
                        "name": name,
                        "description": desc,
                        "domain": domain,
                        "scope": scope,
                        "rel_path": f".agents/skills/{name}/SKILL.md",
                        "full_path": str(skill_md)
                    })
                except Exception as e:
                    print(f"[!] Erro ao ler {skill_md}: {e}")
    return skills

def update_skills_registry_md(skills):
    """Updates docs/SKILLS_REGISTRY.md with the latest scanned skills"""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    
    md_lines = [
        "# Registro Canônico de Skills Operacionais — AXION Enterprise",
        "",
        f"> **Última Sincronização Automática**: {now}  ",
        "> **Padrão de Especificação**: Antigravity / Cursor / Claude Code / MCP Standard (`SKILL.md` com YAML Frontmatter)  ",
        "> **Local do Workspace**: `C:\\workspace\\.agents\\skills/`  ",
        "> **Local Global do Sistema**: `C:\\Users\\AXION\\.gemini\\antigravity\\skills/`  ",
        f"> **Total de Skills Ativas**: {len(skills)}  ",
        "",
        "---",
        "",
        "## Matriz de Skills Operacionais Instaladas",
        "",
        "| Skill | Domínio Principal | Escopo & Tecnologias | Arquivo Canônico |",
        "| :--- | :--- | :--- | :--- |"
    ]
    
    for s in skills:
        md_lines.append(f"| **`{s['name']}`** | {s['domain']} | {s['scope']} | [`{s['name']}/SKILL.md`](file:///C:/workspace/{s['rel_path']}) |")
        
    md_lines.extend([
        "",
        "---",
        "",
        "## Como as Skills são Ativadas e Aplicadas",
        "",
        "1. **Descoberta Automática (Progressive Disclosure)**: O Antigravity lê a descrição no YAML frontmatter de cada `SKILL.md`. Quando uma instrução necessita de regras especializadas de um desses domínios, o agente carrega o conteúdo completo sob demanda.",
        "2. **Invocação Mandatória por Escopo**: Conforme a **Regra #13 do AGENTS.md**, o agente é obrigado a aplicar a skill correspondente antes de redigir código ou executar comandos na respectiva tecnologia.",
        "3. **Protocolo de Aprendizado Ativo**: Conforme a **Regra #14 do AGENTS.md**, caso o agente se depare com uma tecnologia não coberta, deve consultar as fontes em [`docs/SKILL_SOURCES_GUIDE.md`](file:///C:/workspace/docs/SKILL_SOURCES_GUIDE.md), criar a skill e rodar este sincronizador.",
        "",
        "---",
        "",
        "## Sincronização Automática",
        "Para re-sincronizar este registro e o `AGENTS.md` a qualquer momento após criar uma nova skill, execute:",
        "```powershell",
        "python scripts/sync_skills_registry.py",
        "```",
        ""
    ])
    
    SKILLS_REGISTRY_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    SKILLS_REGISTRY_MD_PATH.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[OK] Atualizado: {SKILLS_REGISTRY_MD_PATH}")

def update_agents_md(skills):
    """Updates the dynamic skills table in AGENTS.md between the registry markers"""
    if not AGENTS_MD_PATH.exists():
        print(f"[!] {AGENTS_MD_PATH} não encontrado.")
        return

    content = AGENTS_MD_PATH.read_text(encoding="utf-8")
    
    table_lines = [
        "<!-- SKILLS_REGISTRY_START -->",
        "| Escopo da Tarefa | Skill Mandatória | Arquivo Canônico |",
        "| :--- | :--- | :--- |"
    ]
    for s in skills:
        table_lines.append(f"| **{s['domain']}** | `{s['name']}` | [`{s['rel_path']}`](file:///C:/workspace/{s['rel_path']}) |")
    table_lines.append("<!-- SKILLS_REGISTRY_END -->")
    
    new_table_str = "\n".join(table_lines)
    
    if "<!-- SKILLS_REGISTRY_START -->" in content and "<!-- SKILLS_REGISTRY_END -->" in content:
        pattern = re.compile(r"<!-- SKILLS_REGISTRY_START -->.*?<!-- SKILLS_REGISTRY_END -->", re.DOTALL)
        updated_content = pattern.sub(new_table_str, content)
    else:
        # Se os marcadores ainda não existirem, anexa ao final da seção de governança
        print("[*] Inserindo marcadores de registro de skills no AGENTS.md...")
        updated_content = content + "\n\n" + new_table_str + "\n"

    AGENTS_MD_PATH.write_text(updated_content, encoding="utf-8")
    print(f"[OK] Atualizado: {AGENTS_MD_PATH}")

def update_inventory_json(skills):
    """Updates active skills list in workspace/inventory.json"""
    if not INVENTORY_JSON_PATH.exists():
        return
    try:
        data = json.loads(INVENTORY_JSON_PATH.read_text(encoding="utf-8"))
        data["skills"] = {
            "total_active": len(skills),
            "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "skills_list": [s["name"] for s in skills]
        }
        INVENTORY_JSON_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Atualizado: {INVENTORY_JSON_PATH}")
    except Exception as e:
        print(f"[!] Erro ao atualizar {INVENTORY_JSON_PATH}: {e}")

def mirror_to_global_skills(skills):
    """Mirrors all skills to ~/.gemini/antigravity/skills/"""
    GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    mirrored_count = 0
    for s in skills:
        src_file = Path(s["full_path"])
        dest_dir = GLOBAL_SKILLS_DIR / s["name"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "SKILL.md"
        try:
            dest_file.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")
            mirrored_count += 1
        except Exception as e:
            print(f"[!] Erro ao espelhar {s['name']} globalmente: {e}")
    print(f"[OK] Espelhadas {mirrored_count} skills globalmente em: {GLOBAL_SKILLS_DIR}")

def main():
    print("=== Sincronizador Canônico de Skills AXION ===")
    skills = scan_skills()
    print(f"[*] Encontradas {len(skills)} skills operacionais em {SKILLS_DIR}")
    
    update_skills_registry_md(skills)
    update_agents_md(skills)
    update_inventory_json(skills)
    mirror_to_global_skills(skills)
    print("=== Sincronização Concluída com Sucesso! ===")

if __name__ == "__main__":
    main()
