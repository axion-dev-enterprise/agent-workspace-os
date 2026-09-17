# SETUP_PROTOCOL.md — Protocolo Canônico de Setup & Onboarding

> **PROPÓSITO**: Configurar e inicializar o workspace através do **Painel Visual Web Local** (`http://127.0.0.1:8765`) após uma solicitação explícita do operador.

> **Limite de autorização**: iniciar o painel não autoriza OAuth, WhatsApp, Drive, transcrição, proxy de IA, instalação de ferramentas, deploy ou qualquer envio de dados. Cada integração exige consentimento específico e informado.

---

## 🖥️ Fluxo Primário e Obrigatório: Painel Web Local

### Instrução para o Agente de IA:
Sempre que o usuário solicitar explicitamente setup ou inicialização:
1. **Inicie o servidor de setup em segundo plano**:
   ```bash
   python scripts/setup_server.py
   ```
2. **Envie ao usuário o link do dashboard**:
   ```
   http://127.0.0.1:8765
   ```
3. No painel, o usuário irá:
   - Visualizar o status de todos os compiladores e CLIs (Python, Node, Git, gh, Vercel, Wrangler).
   - Instalar ferramentas faltantes com 1 clique (com streaming live de logs).
   - Escolher se deseja conectar autenticação GitHub e Vercel.
   - Escolher se deseja escanear o QR Code do WhatsApp para pareamento com o agente.
   - Na aba **Workspace**, preencher os dados do projeto e clicar em **Salvar**.

> **O que o botão Salvar faz:**
> Ao salvar no painel web, o servidor cria `workspace.config.json`, substitui todos os placeholders `{{...}}` em `AGENTS.md` e `DIRECTIVES.md`, cria as pastas canônicas (`apps/`, `services/`, `packages/`, `docs/`, `memory/cowork/`), inicializa o lock de concorrência (`active_tasks.json`) e grava a entrada inaugural no log diário!

---

## 1-Click Launchers para Usuários Humanos

Se você é o desenvolvedor e acabou de clonar o repositório, pode iniciar imediatamente sem agente:

- **Windows**: Duplo-clique em **`start.bat`** (ou `npm start`).
- **macOS / Linux**: Execute **`./start.sh`** (ou `npm start`).
- **Qualquer sistema com Python**: `python scripts/setup_server.py`.

---

## 💬 Fluxo Secundário (Fallback): Configuração via Chat

> ⚠️ **Atenção**: Use este fluxo **apenas se o usuário solicitar explicitamente** *"configurar via chat"* ou estiver em um ambiente sem interface gráfica (ex: servidor SSH remoto).

Nesse caso de exceção, faça 6 perguntas objetivas:
1. **Nome da Organização / Projeto**: (ex: `Acme Corp`, `Meu App`)
2. **Slug do Projeto**: (ex: `acme`, `meu-app`)
3. **Identidade Git Oficial**:
   - Nome para commits: (ex: `Acme Bot`)
   - Email para commits: (ex: `dev@acme.com`)
4. **Caminho Raiz Oficial**: (`.` para a pasta atual)
5. **Domínio Principal**: (ex: `acme.com` ou `localhost`)
6. **Destino Canônico de Deploy**: (ex: `Vercel`, `VPS / Docker`, `Cloudflare Pages`)

*(Se o usuário disser "usar padrões", aplique: Name: `My Workspace`, Slug: `my-workspace`, Deploy: `Vercel`, Root: `.`)*.

Antes de gravar qualquer configuração fornecida no chat, apresente os valores que serão persistidos e confirme que não incluem credenciais. Credenciais devem ser configuradas fora do repositório e nunca devem aparecer na conversa, em arquivos versionados ou no log diário.
