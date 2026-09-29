# AGENTS.md — Protocolo Canônico de Governança do Vault de Segredos 🔐

## 1. Escopo e Propósito
- Este documento rege o comportamento de **todos os agentes de IA** (Antigravity, Cursor, Claude Code, subagentes e scripts operacionais) ao manipular, armazenar ou atualizar tokens, chaves de API e credenciais em `C:\workspace\vault`.
- O Vault categorizado substitui integralmente arquivos `.env` soltos na raiz.

---

## 2. Regra Fundamental: Proibição de Segredos Fora do Vault (Zero Root Secrets)
- É terminantemente **PROIBIDO** para qualquer agente:
  1. Criar ou despejar novas variáveis de ambiente em `C:\workspace\.env` ou na raiz do workspace.
  2. Gravar tokens, senhas ou segredos *hardcoded* em código-fonte, scripts, commits ou mensagens diárias.
  3. Commitar qualquer arquivo `.env` para o Git (reforçado pela regra `vault/**/.env` no `.gitignore`).

---

## 3. Protocolo Canônico de Ingestão de Tokens (5 Passos Obrigatórios)

Sempre que um agente receber do operador humano ou de um serviço uma nova credencial, token ou API key, o agente **DEVE** seguir rigorosamente este fluxo atômico:

```
[Token Recebido]
       │
       ▼
1. Classificação (Categoria & Plataforma)
       │
       ▼
2. Armazenamento Seguro no .env Específico (vault/<categoria>/<plataforma>/.env)
       │
       ▼
3. Atualização do Schema Técnico (vault/<categoria>/<plataforma>/index.json)
       │
       ▼
4. Atualização da Documentação Operacional (vault/<categoria>/<plataforma>/README.md)
       │
       ▼
5. Verificação Empírica & Auditoria (python scripts/vault_loader.py audit)
```

### Passo 1: Classificação Categórica
Identifique o domínio e o serviço:
- `social/`: Redes sociais, mensageria e bots (`twitter-x`, `instagram`, `telegram`, `whatsapp`).
- `ai/`: Modelos de linguagem, visão e TTS (`llm-providers`, `elevenlabs`, `openai`, `gemini`).
- `cloud/`: Provedores de nuvem, serverless e edge (`cloudflare`, `vercel`, `gcp`).
- `communication/`: E-mail, alertas e notificações (`email`, `smtp`, `imap`).
- `security/`: Redes, VPN, malhas e túneis (`proton`, `tailscale`).
- *Se a plataforma ainda não existir*: Crie a nova subpasta sob a categoria apropriada (ex: `vault/cloud/aws/`).

### Passo 2: Armazenamento Seguro no `.env`
- Grave a variável no arquivo `.env` da respectiva subpasta (`vault/<categoria>/<plataforma>/.env`).
- Utilize maiúsculas e snake_case padrão (`SERVICO_NOME_DA_VARIAVEL`).
- Certifique-se de usar codificação UTF-8 limpa.

### Passo 3: Atualização do Manifesto Técnico (`index.json`)
Abra ou crie o arquivo `vault/<categoria>/<plataforma>/index.json` e registre a nova variável na seção `variables`:
```json
"NOME_DA_VARIAVEL": {
  "type": "string",
  "required": true,
  "description": "Explicação clara da função da credencial",
  "scope": "ex: auth / inference / edge_ops / write_tweets"
}
```

### Passo 4: Atualização da Documentação (`README.md`)
Atualize o `README.md` da subpasta descrevendo:
- Finalidade do serviço.
- Como o operador humano pode gerar, rotacionar ou revogar essa chave no portal correspondente.
- Quais scripts ou módulos do sistema consomem a chave.

*Se for criada uma nova categoria ou plataforma*: Atualize também o catálogo mestre em `vault/index.json` e `vault/README.md`.

### Passo 5: Auditoria Mandatória de Verificação
O agente **NUNCA** deve declarar a tarefa como concluída sem antes executar factual e empiricamente a validação:
```powershell
python scripts/vault_loader.py audit
```
- Verifique se a variável foi detectada como `[OK] CONFIGURADO`.
- Certifique-se de que nenhum valor em texto plano foi vazado na tela (apenas valores mascarados).

---

## 4. Consumo Programático em Código

Qualquer serviço que precise carregar as variáveis de ambiente deve importar e executar o `load_vault`:

```python
import sys
from pathlib import Path

# Garante que a raiz do workspace esteja no sys.path
WORKSPACE_ROOT = Path("c:/workspace")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.vault_loader import load_vault
load_vault()  # Injeta recursivamente todas as credenciais ativas em os.environ
```

---

## 5. Precedência de Governança
Este documento deriva de [C:\workspace\AGENTS.md](file:///c:/workspace/AGENTS.md) e das regras corporativas de segurança AXION. Em caso de conflito, as regras de Zero Credential Logging e Pre-Commit Guard prevalecem irrestritamente.
