# SETUP_AGENT_DIRECTIVE.md — Diretriz Universal de Operação para Agentes de IA

> **ATENÇÃO AGENTE DE IA (Claude Code, Antigravity, Cursor, Codex, Hermes, Copilot, Windsurf):**  
> Você está operando em um repositório governado pelo **Agent Workspace OS**.  
> Leia atentamente a regra mandatória abaixo antes de responder ao usuário.

---

## Regra mandatória: setup é opt-in e conectores exigem consentimento

Quando o usuário solicitar explicitamente **"setup"**, **"iniciar setup"** ou **"configurar workspace"**:

1. Não presuma que a ausência de `workspace.config.json` autoriza iniciar serviços ou coletar configurações. Explique o setup em uma frase e peça a confirmação quando o pedido não for inequívoco.
2. Após uma solicitação explícita, é permitido:
   - Iniciar imediatamente o servidor visual Python em segundo plano:
     ```bash
     python scripts/setup_server.py
     ```
   - Responder ao usuário diretamente com uma mensagem amigável e o link:
     > *"Iniciei o **Painel Visual de Setup & Controle** em: **http://127.0.0.1:8765**.
     > Acesse pelo seu navegador para:*  
     > 1. *Preencher o nome da organização, identidade Git e destino de deploy na aba **Workspace**.*  
     > 2. *Clicar em **Salvar & Inicializar Workspace** (todos os arquivos e regras serão configurados automaticamente).*  
     > 3. *Verificar as ferramentas instaladas e instalar dependências faltantes com 1 clique.*  
     > 4. *Opcionalmente, após autorizar o acesso, escanear o QR Code do WhatsApp para parear o agente.*
     >  
     > *(Nota: Caso esteja em um ambiente de terminal remoto sem navegador, responda 'configurar por chat' para ativar o modo conversacional fallback)."*

3. Antes de ativar WhatsApp, Drive, OAuth, transcrição, proxy de IA ou qualquer conector, informe os dados acessados e aguarde autorização específica. Um conector não é ativado apenas porque o setup foi iniciado.
4. **MODO FALLBACK (Apenas se solicitado)**: Somente se o usuário pedir explicitamente *"configurar por chat"*, execute as perguntas conversacionais de [SETUP_PROTOCOL.md](SETUP_PROTOCOL.md).

---

## 🎯 Decisão Imediata: Setup vs Update vs Tarefa

```
                                 [Checagem do Workspace]
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 ▼                                                     ▼
     `workspace.config.json`                              `workspace.config.json`
          NÃO EXISTE                                            JÁ EXISTE
                 │                                                     │
                 ▼                                                     ▼
 Verifique se o usuário pediu setup                       Verifique o intento no prompt
        explicitamente                                  ┌─────────────┴─────────────┐
                 │                                     ▼                           ▼
                 ▼                            "update" / "sync"           "task" / "código"
 Inicie o painel somente após confirmação
 `python scripts/setup_server.py`
                                                         │                           │
                                                         ▼                           ▼
                                              [UPDATE_PROTOCOL.md]         1. Consulte active_tasks.json
                                             (Puxe commits upstream,       2. Registre seu lock
                                              preserve vars locais)        3. Siga regras de AGENTS.md
```

---

## 🚦 Regras Invioláveis de Engenharia
- **Zero Root Clutter**: Nunca crie arquivos avulsos na raiz. Arquivos temporários vão para `temp/` ou `scratch/`.
- **Zero Falsos Declarativos**: Nunca declare sucesso sem verificação empírica real (HTTP 200, DOM inspecionado, syntax check).
- **Zero Diálogos Nativos**: PROIBIDO `alert()`, `confirm()` ou `prompt()`. Use toasts glassmorphic dark.
- **Daily Timeline**: Registre cada tarefa cronologicamente em `memory/daily_logs/YYYY-MM-DD.md`.
