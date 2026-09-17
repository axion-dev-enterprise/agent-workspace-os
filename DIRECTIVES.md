# DIRECTIVES.md — Diretrizes de Engenharia, Qualidade e Segurança

## 1. Quality Gates Mandatórios (Decisão Go / No-Go)
Antes de qualquer liberação de código, promoção para `main` ou deploy, o agente DEVE selecionar e executar as validações aplicáveis à mudança:
1. **Estrutura**: Arquivos, links, esquemas e formatos alterados devem ser verificáveis sem ambiguidade.
2. **Código**: Typecheck, lint e testes focados quando o projeto fornecer esses comandos e a política do ambiente permitir executá-los.
3. **Runtime**: Logs limpos e validação do fluxo alterado quando houver ambiente autorizado; uma resposta HTTP isolada não comprova comportamento correto.
4. **Interface**: Navegação por teclado, foco, contraste, responsividade e estados de erro/carregamento para mudanças de UI.
5. **Segurança**: Sem segredos, dados privados, permissões excessivas, endpoints mutáveis sem proteção ou dependências não revisadas.

> Se **qualquer** item falhar ➔ **NO-GO IMEDIATO** (abortar e corrigir a causa raiz).
> Se **todos** os itens passarem ➔ **GO** (autorizar deploy e version bump).

Uma release exclusivamente documental deve declarar quais gates não se aplicam. É proibido reciclar evidências de versões anteriores.

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

Telemetria não deve registrar conteúdo de mensagens, segredos, cookies, cabeçalhos de autorização ou dados pessoais além do mínimo necessário para diagnóstico.

---

## 4. Gerenciamento de Dependências
- Priorizar gerenciadores rápidos e determinísticos com lockfile versionado (PNPM, Yarn Berry ou NPM limpo).
- Proibido instalar dependências desnecessárias ou pacotes que adicionem mais de 50KB ao bundle sem justificativa de arquitetura.
- Dependências e skills de terceiros exigem origem, revisão fixada, licença compatível e diff revisado antes de atualização.

---

## 5. Superfície de administração e conectores
- Painéis locais, APIs de administração e bridges devem usar loopback por padrão. Se expostos à rede, devem ter autenticação, autorização por rota, CORS restrito, rate limiting e logs redigidos.
- Rotas de simulação, debug e teste devem exigir ambiente de desenvolvimento e não podem acionar serviços reais.
- Conectores que enviam mensagens, chamam APIs pagas ou processam dados de terceiros permanecem desabilitados até a autorização explícita do operador.

---

## 6. Fluxo de contribuição e manutenção
- `main` é protegida por processo: mudanças chegam por branch e Pull Request revisável.
- O update de um workspace deve começar com fetch e diff. Uma árvore modificada interrompe o fluxo até que o proprietário escolha como preservá-la.
- Vulnerabilidades devem seguir [SECURITY.md](SECURITY.md); não abra issue pública com segredo, sessão, exploit reproduzível contra terceiros ou dados pessoais.
