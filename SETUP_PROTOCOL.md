# SETUP_PROTOCOL.md — Canonical Onboarding Protocol

> **Purpose**: Configure a freshly cloned workspace from scratch by populating user project variables, establishing Git identity, and initializing the multi-agent directory tree.

---

## 🖥️ Option A: Visual Web Dashboard (Fastest & Zero Prompting)

If you prefer a graphical interface to check tools, scan the WhatsApp QR Code, and configure settings visually:

```bash
# Windows (Double-click or terminal):
start.bat
# or: npm start / python scripts/setup_server.py

# macOS / Linux:
./start.sh
# or: npm start / python3 scripts/setup_server.py
```
Open **`http://127.0.0.1:8765`** in your browser:
- **Tools & CLI**: Live diagnostics of Python, Node, Git, GitHub CLI, Vercel, and Cloudflare Wrangler with 1-click installation.
- **Login & OAuth**: Instant validation of GitHub, Vercel, and Cloudflare credentials.
- **WhatsApp Bridge**: Live QR Code pairing for Monitor Mode (passive logging) and React Mode (task dispatch).
- **Google Drive**: One-click connection to sync meeting transcripts and briefs.

---

## 🤖 Option B: Conversational Setup via AI Agent

If you are interacting with an AI Agent (Claude Code, Antigravity, Cursor, Codex, Windsurf), tell the agent:
> *"Please execute SETUP_PROTOCOL.md and configure my workspace."*

### Step 1: State Detection
1. Check if `workspace.config.json` already exists.
   - If it exists, inform the user: *"This workspace is already configured. If you wish to pull new skills and upstream updates, use **UPDATE_PROTOCOL.md**."*
2. If not configured, proceed to Step 2.

### Step 2: 6-Question Interactive Interview
Ask the user the following 6 concise questions (or if the user specified *"use defaults"*, fill in default values):

1. **Project / Organization Name**: (e.g., `Acme Corp`, `DevStudio`, `My App`)
2. **Project Slug**: (e.g., `acme`, `devstudio`, `my-app`)
3. **Git Identity**:
   - Committer Name: (e.g., `Acme Bot` or your name)
   - Committer Email: (e.g., `dev@acme.com` or your email)
4. **Canonical Workspace Root**: (e.g., `.` for current folder, or absolute path)
5. **Primary Domain**: (e.g., `acme.com` or `localhost`)
6. **Primary Deploy Target**: (e.g., `Vercel`, `VPS / Docker`, `Cloudflare Pages`, `Local-only`)

> 💡 **Quick Defaults**: If the user says *"use standard defaults"*, set:
> - Name: `My Workspace Project`
> - Slug: `my-workspace`
> - Branch: `main`
> - Deploy Target: `Vercel`
> - Root: `.`

### Step 3: Config Generation & Placeholder Replacement
1. Create `workspace.config.json` by copying `workspace.config.template.json` with user answers.
2. Add metadata:
   ```json
   "setup_completed_at": "<ISO-TIMESTAMP>",
   "setup_agent": "<AGENT_NAME>",
   "version": "1.1.0"
   ```
3. Replace all matching `{{PLACEHOLDER}}` tags in `AGENTS.md` and `DIRECTIVES.md`.

### Step 4: Canonical Directory Tree Initialization
Ensure the following directory tree exists:
```
├── apps/               # Frontends, SPAs, and client applications
├── services/           # Backend APIs, workers, and microservices
├── packages/           # Shared libraries and internal SDKs
├── docs/               # Technical specs, architecture decision records (ADRs)
├── memory/             # Multi-agent persistent telemetry and state
│   ├── daily_logs/     # Chronological daily journals (YYYY-MM-DD.md)
│   └── cowork/         # active_tasks.json, blackboard.json, handoffs/
└── credentials/        # Private keys and service accounts (.gitignored)
```

Initialize default cowork state:
- `memory/cowork/active_tasks.json` with `{"tasks": []}`.
- `memory/cowork/blackboard.json` with initial setup record.

### Step 5: Timeline Entry
Record entry in `memory/daily_logs/YYYY-MM-DD.md`:
```markdown
## [HH:mm:ss] [agent-setup] Workspace Setup Successfully Initialized
- **Organization**: <ORGANIZATION_NAME> (<ORGANIZATION_SLUG>)
- **Git Identity**: <GIT_USER_NAME> <<GIT_USER_EMAIL>>
- **Primary Target**: <PRIMARY_DEPLOY_TARGET>
- **Executor**: <AGENT_NAME>
```

### Step 6: User Confirmation
Output a clean, concise summary confirming the workspace is 100% ready for engineering tasks.
