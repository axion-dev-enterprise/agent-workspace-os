# AXION Enterprise Secrets Vault 🔐

## 1. Visão Geral e Arquitetura

O **AXION Vault** substitui o uso caótico de um único arquivo `.env` na raiz do projeto por uma arquitetura hierárquica, categorizada e auditável.

Cada plataforma ou subsistema possui seu próprio diretório isolado contendo três arquivos canônicos:
- `.env` — Valores reais dos segredos e chaves de API (estritamente ignorados pelo Git via `.gitignore`).
- `index.json` — Manifesto técnico da plataforma (schema das variáveis, obrigatoriedade, tipo, endpoints e propósitos).
- `README.md` — Guia operacional de como gerar, renovar, revogar e auditar as credenciais da plataforma.

---

## 2. Topologia do Vault

Shopify: `vault/cloud/shopify/` — acesso temporário, schema e instruções de rotação; valores somente no `.env`.

```
vault/
├── index.json                     # Manifesto mestre do Vault
├── README.md                      # Governança e arquitetura geral
│
├── social/                        # Redes Sociais & Mensageria
│   ├── twitter-x/                 # .env, index.json, README.md
│   ├── instagram/                 # .env, index.json, README.md
│   ├── telegram/                  # .env, index.json, README.md
│   └── whatsapp/                  # .env, index.json, README.md
│
├── ai/                            # Inteligência Artificial & LLMs
│   ├── llm-providers/             # Providers AXION gerais e Flow
│   └── isabela-clients/           # OpenRouter exclusivo para workloads de clientes
│
├── cloud/                         # Provedores de Nuvem & Serverless
│   ├── cloudflare/                # API Tokens, Account ID, Workers, D1, R2
│   └── vercel/                    # Deploy Tokens, Teams, Domains
│
├── communication/                 # Serviços de E-mail
│   └── email/                     # Proton Bridge, Gmail IMAP/SMTP
│
├── security/                      # Redes & VPN
│   ├── proton/                    # Proton VPN & Drive
│   ├── tailscale/                 # Tailnet Auth Keys
│   ├── auth-center-core/          # Auth Center JWT e papel DB least-privilege
│   └── juliana-legacy-vps/        # Credencial recebida; validar chave SSH do host antes de usar
│
└── payments/                      # Pagamentos & Credenciais de Teste
    ├── axion-staging/             # API key de teste Pay e segredo HMAC do webhook Flow
    └── isabela-staging/           # Credenciais MP/Stripe exclusivamente sandbox do pivô Isabela
```

---

## 3. Carregamento Automático em Tempo de Execução

Todos os agentes, scripts e daemons do ecossistema AXION utilizam o carregador unificado:

```python
from scripts.vault_loader import load_vault

# Carrega recursivamente todos os .env sob vault/ para o os.environ
load_vault()
```

### Auditoria Segura via Terminal (Zero Credential Leak)

Para auditar quais credenciais estão ativas sem expor chaves sensíveis:

```powershell
python scripts/vault_loader.py audit
```

O comando exibe cada chave somente com o status (`CONFIGURADO` ou `PENDENTE`).
Não imprime prefixos, sufixos, comprimentos ou qualquer fragmento do segredo.

- `cloud/isabela-clients`: dedicated Isabela PostgreSQL owner/runtime; credentials only in platform .env.
- `security/auth-center-core`: Auth Center runtime key and least-privilege database URL; only in its categorized `.env`.
