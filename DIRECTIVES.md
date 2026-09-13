# DIRECTIVES.md — Diretrizes de Engenharia, Qualidade e Segurança

## 1. Quality Gates Mandatórios (Decisão Go / No-Go)
Antes de qualquer liberação de código, promoção para `main` ou deploy, o agente DEVE validar:
1. **Typecheck & Lint**: Zero erros em `tsc`, ESLint/Biome ou linters da linguagem alvo.
2. **Logs Limpos**: Zero exceções não tratadas e zero crashes em runtime.
3. **Validação Live**: Resposta HTTP 200 com validação empírica do HTML/DOM (título correto, renderização de dados reais, ausência de erros 404/500).
4. **Layout Responsivo**: Zero barras de rolagem horizontais espúrias (`overflow-x: hidden / visible; scrollbar-width: none`).
5. **Segurança**: Zero segredos expostos no código ou histórico Git.

> Se **qualquer** item falhar ➔ **NO-GO IMEDIATO** (abortar e corrigir a causa raiz).
> Se **todos** os itens passarem ➔ **GO** (autorizar deploy e version bump).

---

## 2. Matriz Canônica de Destino de Deploy

| Tipo de Componente | Destino Recomendado | Protocolo |
|---|---|---|
| Frontend Estático / SPA Leve | `{{PRIMARY_DEPLOY_TARGET}}` (Vercel, Cloudflare, etc.) | Build prebuilt auditado |
| API com Estado / Workers / DB | VPS Dedicada (`{{VPS_HOST_IP}}`) / Docker | Docker Compose + Traefik/Nginx |
| Background Jobs / Filas | VPS / Redis / Queue Worker | Systemd ou Docker com restart |

---

## 3. Padrão de Tratamento de Erros e Telemetria
- Todo erro de API deve aderir ao padrão **RFC 7807 (Problem Details for HTTP APIs)**:
  - `type`: URI identificando o tipo do erro.
  - `title`: Descrição curta e legível por humanos.
  - `status`: Código de status HTTP.
  - `detail`: Detalhamento específico da ocorrência sem vazamento de stack traces internas.
  - `instance`: Trace ID único para correlação com logs.

---

## 4. Gerenciamento de Dependências
- Priorizar gerenciadores rápidos e determinísticos com lockfile versionado (PNPM, Yarn Berry ou NPM limpo).
- Proibido instalar dependências desnecessárias ou pacotes que adicionem mais de 50KB ao bundle sem justificativa de arquitetura.
