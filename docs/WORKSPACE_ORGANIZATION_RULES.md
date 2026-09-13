# WORKSPACE_ORGANIZATION_RULES.md — Regras de Organização do Workspace

## 1. Regra Fundamental da Raiz (Zero Clutter)
Apenas os seguintes arquivos são permitidos na raiz oficial:
- `AGENTS.md`
- `DIRECTIVES.md`
- `README.md`
- `SETUP_AGENT_DIRECTIVE.md`
- `workspace.config.json` (ou `.template.json`)
- `package.json` / `pnpm-workspace.yaml` / `requirements.txt` (conforme stack)
- `.gitignore`

Todos os outros arquivos devem residir em suas pastas canônicas correspondentes.

---

## 2. Diretórios Canônicos

| Diretório | Finalidade | Regras de Uso |
|---|---|---|
| `apps/` | Aplicações voltadas ao usuário (SPAs, sites, dashboards) | Cada app em sua própria pasta isolada |
| `services/` | APIs, microsserviços, workers e backends | Cada serviço com Dockerfile e testes próprios |
| `packages/` | Código compartilhado entre apps e services | Zero duplicação de utilitários e tipos |
| `docs/` | Documentação arquitetural, guias e especificações | Markdown legível e versionado |
| `memory/` | Histórico cronológico e coordenação | `daily_logs/` e `cowork/` |
| `secure/` | Credenciais e configurações sensíveis | Estritamente listado no `.gitignore` |
