# WORKSPACE_ORGANIZATION_RULES.md — Regras de Organização do Workspace

## 1. Regra Fundamental da Raiz (Zero Clutter)
A raiz contém somente o manifesto do projeto: documentação de entrada, licenças e políticas, arquivos de configuração da ferramenta, lockfiles, launchers e metadados de release. Cada repositório deve listar esses arquivos em seu README; arquivos temporários, relatórios de execução, exportações, sessões, dumps e scripts ad hoc pertencem a diretórios dedicados e devem ser ignorados pelo Git quando privados.

Não use uma allowlist rígida que contradiga os arquivos de entrada reais do repositório. Antes de criar um novo arquivo na raiz, prefira `docs/`, `scripts/`, `apps/`, `services/`, `packages/` ou `temp/` e justifique qualquer exceção no Pull Request.

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
