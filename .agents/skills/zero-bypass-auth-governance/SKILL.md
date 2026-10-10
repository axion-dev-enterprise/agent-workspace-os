---
name: zero-bypass-auth-governance
description: >-
  Governança de segurança mandatória para autenticação e controle de acesso no
  ecossistema AXION. Proíbe terminantemente rotas de bypass, botões de login direto
  sem validação, emissão de tokens mockados ou atalhos em interfaces e APIs.
  Exige validação criptográfica (Google OAuth 2.0 / TOTP 2FA / hash seguro),
  conferência obrigatória em banco de dados (PostgreSQL dashboard_users e
  merchant_accounts) e fail-closed com HTTP 503 quando credenciais estiverem ausentes.
---

# Zero-Bypass Auth Governance — Master Security Skill

Esta skill rege **todos os agentes, desenvolvedores e deploys** atuando no ecossistema AXION para qualquer camada de autenticação, emissão de sessões, controle de acesso e autorização (RBAC).

---

## 1. Regra de Ferro Inviolável (Zero-Bypass Auth Invariant)

> **"É EXPRESSAMENTE E TERMINANTEMENTE PROIBIDO CRIAR BOTÕES DE LOGIN DIRETO, ROTAS DE ATALHO (EX: `/login/ceo`, `/login/mock`, `/login/cliente`), EMISSÃO ARBITRÁRIA DE TOKENS JWT SEM VALIDAÇÃO DE CREDENCIAIS, OU QUALQUER FORMA DE BYPASS/BACKDOOR."**

Todo agente que implementar, refatorar ou manter rotas de autenticação DEVE seguir estritamente:

1. **Validação Criptográfica Real**:
   - Google SSO via OAuth 2.0 com `state` assinado por HMAC SHA-256 e validação de tokens na API do Google (`https://oauth2.googleapis.com/token` e `verifyIdToken`).
   - TOTP 2FA via Speakeasy / RFC 6238 com janela de tempo defensiva.
   - Senhas locais (quando habilitadas) com hash forte `argon2id` ou `bcrypt` (mínimo 12 rounds), jamais plain text ou tokens estáticos.

2. **Validação e Persistência no Banco de Dados (`PostgreSQL`)**:
   - Todo usuário autenticado DEVE existir ou ser conferido na tabela canônica `dashboard_users`.
   - Toda operação de merchant/cliente DEVE validar a existência e status `ACTIVE` na tabela `merchant_accounts`.
   - Papéis (`roles`) DEVEM ser derivados do banco de dados e de domínios corporativos verificados (`@example.com`), jamais injetados arbitrariamente por parâmetro de query string ou formulário mock.

3. **Política de Fail-Closed (Ausência de Credenciais no Vault)**:
   - Se o `GOOGLE_CLIENT_ID` ou `GOOGLE_CLIENT_SECRET` não estiverem presentes no Vault (`c:\workspace\vault\` ou ambiente da VPS), o serviço DEVE retornar erro explícito **HTTP 503 Service Unavailable** informando a pendência de configuração.
   - **PROIBIÇÃO ABSOLUTA DE MOCKS**: É proibido gerar sessões automáticas ou emitir cookies de mentira "para testar a tela" em ambiente conectado à rede ou produção.

4. **Governança de Frontend**:
   - Proibido adicionar à interface botões com links diretos emitindo sessão sem passar pelo formulário de consentimento ou handshake OAuth oficial.
   - A página de login canônica (`auth.example.com`) deve expor unicamente os métodos autênticos suportados (ex: botão único "Continuar com Google" e campo de 2FA pós-login).

---

## 2. Topologia Canônica de Autenticação

| Componente | Responsabilidade | Implementação |
| :--- | :--- | :--- |
| **`axion-auth-center`** | Central única de SSO e emissão de sessões wildcard | Node.js na porta 4000 (`auth.example.com`), Nginx TLS 1.3 |
| **`axion-postgres`** | Fonte de verdade de usuários, perfis e contas merchant | PostgreSQL 16 (`axion_pay`), tabelas `dashboard_users` e `merchant_accounts` |
| **Cookies de Sessão** | Autenticação cross-subdomain | `axion_session` (HttpOnly, Secure, Lax, Domain: `.example.com`) e `axion_token` |
| **Apps Consumidores** | Consomem cookies ou Bearer JWT | `pay.example.com`, `flow.example.com`, `hub.example.com` |

---

## 3. Schema Técnico Mandatório no PostgreSQL

Toda conta ou merchant DEVE ser provisionado seguindo o schema relacional:

```sql
-- 1. Usuário Corporativo / Cliente
CREATE TABLE IF NOT EXISTS dashboard_users (
  auth_user_id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  display_name TEXT,
  picture_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Conta de Merchant vinculada ao usuário
CREATE TABLE IF NOT EXISTS merchant_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_auth_user_id TEXT NOT NULL REFERENCES dashboard_users(auth_user_id) ON DELETE RESTRICT,
  name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
  document TEXT,
  billing_email TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Matriz de Papéis (RBAC)
- **`ceo` / `master_admin`**: `Operator@example.com`, `developer@example.com`
- **`admin`**: Administradores com autorização na organização
- **`merchant`**: Donos de contas de faturamento e operação no AXION Pay (`manadiario@example.com`)
- **`user` / `client`**: Usuários comuns do ecossistema

---

## 4. Checklist Pré-Deploy e Verificação de Qualidade

Antes de qualquer commit, deploy ou entrega de alterações em serviços de autenticação, o agente DEVE executar e atestar factualmente:

1. **Greps de Segurança Antifraude**:
   ```powershell
   # Procura por rotas de bypass ou mock no código-fonte
   Select-String -Path @("apps/**", "services/**", "scripts/**") -Pattern "(login/(ceo|mana|mock|direct|admin)|issueSession\([^)]*mock|bypass)"
   ```
   *Critério de aprovação*: ZERO correspondências em rotas ativas ou templates HTML públicos.

2. **Inspeção de Resposta Não Autenticada (HTTP 401)**:
   ```bash
   curl -s -i https://auth.example.com/api/auth/me
   # Deve retornar estritamente HTTP 401 Unauthorized com {"authenticated":false}
   ```

3. **Verificação de Healthcheck e Conexão de Banco**:
   ```bash
   curl -s -L https://auth.example.com/health
   # Deve retornar {"status":"ok", "database":"connected"}
   ```

4. **Tentativa de Acesso a Rotas Removidas**:
   ```bash
   curl -s -i https://auth.example.com/api/auth/login/ceo
   # Não pode retornar cookies nem emitir tokens de autenticação
   ```

---

## 5. Protocolo de Ação em Caso de Falha de Provedor Externo

Se a integração com Google OAuth falhar ou as chaves não estiverem configuradas:
1. Retornar **HTTP 503** na API e tela limpa de indisponibilidade no navegador.
2. Solicitar ao operador humano a inserção das credenciais oficiais no Vault (`vault/tokens/google/google.env` ou variáveis de ambiente).
3. **NUNCA** contornar o fluxo fornecendo sessões mockadas ou links de acesso direto.
