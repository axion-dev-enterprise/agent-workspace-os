# Agent Workspace OS 🤖

<div align="center">

**The Deterministic Operating Framework for Autonomous AI Software Engineering.**  
*Turn any repository into an hallucination-resistant, multi-agent collaborative environment.*

[![Release: v2.1.0](https://img.shields.io/badge/Release-v2.1.0-blue.svg?style=flat-square)](version_dump.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)
[![Portable](https://img.shields.io/badge/Configuration-template--first-blue?style=flat-square)](docs/TEMPLATE_CUSTOMIZATION.md)

[⚡ 1-Click Launch](#-1-click-launch) • [📋 Agent Copyboxes](#-copy-paste-prompts-for-ai-agents) • [🖥️ Web Dashboard](#-visual-web-dashboard--control-center) • [🎯 Core Principles](#-core-principles) • [🤝 Multi-Agent Cowork](#-multi-agent-cowork-protocol) • [🚀 Changelog](#-changelog)

</div>

---

## Quick start

Copy the distribution, read the pre-flight, then customize the local manifest before enabling any connector:

```bash
git clone <your-fork-or-distribution-url> my-project
cd my-project
copy templates\workspace-manifest.template.json workspace\workspace-manifest.json
copy templates\capability-policy.template.json workspace\capability-policy.json
```

Before enabling a connector or entering credentials, read [Security](SECURITY.md), [the setup protocol](SETUP_PROTOCOL.md), and [the documentation index](docs/README.md). A setup request does not authorize messages, deployments, account changes, or other external mutations.

### Run the Dashboard:

| Platform | 1-Click Command | What Happens |
|---|---|---|
| **Windows** | Double-click **`start.bat`** (or `npm start`) | Automatically starts server and opens **`http://127.0.0.1:8765`** in your default browser. |
| **macOS / Linux** | Run **`./start.sh`** (or `npm start`) | Starts server and opens dashboard in your browser. |
| **Any System (Python)** | Run **`python scripts/setup_server.py`** | Starts the zero-dependency threaded HTTP dashboard. |

---

## 📋 Copy-Paste Prompts for AI Agents

Already using an AI coding assistant? Copy and paste one of the prompts below directly into your agent's chat:

### 🟣 For Claude Code:
```text
Please start the visual setup server (python scripts/setup_server.py) and give me the link http://127.0.0.1:8765 to configure my workspace.
```

### For another compatible agent:
```text
Inicie o servidor de setup (python scripts/setup_server.py) e me envie o link http://127.0.0.1:8765 para eu configurar o projeto.
```

### 🟢 For Cursor Composer / Windsurf:
```text
@SETUP_AGENT_DIRECTIVE.md Start the setup server (python scripts/setup_server.py) and provide the dashboard link http://127.0.0.1:8765.
```

### ⚪ For ChatGPT / OpenAI Codex:
```text
Start python scripts/setup_server.py and give me the dashboard link http://127.0.0.1:8765 to set up my workspace.
```

### 🔄 To Update an Existing Workspace (Pull New Skills & Upstream Commits):
```text
Please execute UPDATE_PROTOCOL.md to fetch new upstream commits while preserving my local config.
```

---

## 🖥️ Visual Web Dashboard & Control Center

Agent Workspace OS includes a modern, high-performance local web dashboard running at **`http://127.0.0.1:8765`**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent Workspace OS   [Setup & Control Center]                              │
├───────────────┬───────────────┬──────────────────┬──────────────┬───────────┤
│ 🔧 Tools & CLI│ 🔐 OAuth Auth │ 💬 WhatsApp Link │ 📂 Drive Sync│ ⚙️ Config │
├───────────────┴───────────────┴──────────────────┴──────────────┴───────────┤
│                                                                             │
│  System Preflight Diagnostics                      Quick Actions            │
│  ├─ Python 3.11.15       [Installed]  [Copy]       ├─ [Install Missing Tools│
│  ├─ Node.js v24.19.0     [Installed]  [Copy]       ├─ [Connect GitHub OAuth]│
│  ├─ Git 2.54.0           [Installed]  [Copy]       ├─ [Connect Vercel]      │
│  ├─ GitHub CLI 2.97.0    [Installed]  [Copy]       └─ [Scan WhatsApp QR]    │
│  ├─ Vercel CLI 59.16.0   [Installed]  [Copy]                                │
│  └─ Cloudflare Wrangler  [Install]    [Copy]  ──> Live SSE streaming output │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Live CLI Installation**: 1-click install for missing tools via `winget`/`npm` with live terminal output streaming via SSE.
- **WhatsApp Client Bridge**: Real-time QR Code scanning for WhatsApp pairing. Supports **Monitor Mode** (passive chat & audio logging) and **React Mode** (autonomous task queue execution with `/task`).
- **Google Drive Synchronizer**: Direct ingestion of meeting transcripts, Google Docs, and briefs into workspace memory.
- **Zero Native Dialogs**: Dark glassmorphic toast notification system (zero `alert()`, `confirm()`, or `prompt()`).

---

## ⌨️ NPM Quick Reference

| Command | Action |
|---|---|
| `npm start` | Launches the visual setup dashboard on `http://127.0.0.1:8765` |
| `npm run dashboard` | Alias to start the setup server |
| `npm run preflight` | Runs fast concurrent environment check (`<4.2s`) |
| `npm run whatsapp:bridge` | Starts the Baileys WhatsApp client bridge on port `4114` |
| `npm run drive:check` | Verifies Google Drive credentials |
| `npm run drive:sync` | Ingests recent documents and meeting transcripts from Google Drive |

---

## 🎯 Core Principles & Anti-Hallucination Rails

| Principle | Technical Specification |
|---|---|
| **Zero Root Clutter** | Only essential configuration files permitted in root. All temporary tests and scratch scripts reside in `temp/` or `scratch/`. |
| **Empirical Verification** | Prohibits agents from declaring success based solely on status codes. HTML/DOM inspection, syntax compilation, and live tests are mandatory. |
| **Zero Test Pollution** | Mandatory teardown blocks (`finally`) ensuring test users, carts, and mock database rows are purged immediately after testing. |
| **Big Tech UI/UX Standard** | Total prohibition of emojis as UI icons. Professional SVG vector icons only (Lucide, Heroicons). Obsidian/Zinc surfaces, 150-200ms transitions, CLS = 0. |
| **Custom Modals & Toasts** | Browser-native `alert()`, `confirm()`, and `prompt()` are strictly prohibited. Custom 3D glassmorphic notifications only. |
| **Multi-Agent Cowork** | Asynchronous coordination via `active_tasks.json` (locks), `blackboard.json` (findings), and formal `handoffs/`. |
| **Mandatory Daily Timeline** | Every action and technical diagnosis is chronologically recorded in `memory/daily_logs/YYYY-MM-DD.md`. |

---

## 📂 Canonical Directory Layout

```
.
├── start.bat                   # 1-Click launcher for Windows
├── start.sh                    # 1-Click launcher for macOS / Linux
├── package.json                # Project shortcuts (npm start, npm run preflight)
├── version_dump.json           # Machine-readable release metadata
├── WORKFLOW.md                 # Master operational router (Setup vs Update)
├── SETUP_PROTOCOL.md           # Step-by-step onboarding protocol (GUI & Agent)
├── UPDATE_PROTOCOL.md          # Step-by-step incremental update & memory sync
├── SETUP_AGENT_DIRECTIVE.md    # Universal directive for all AI agents
├── AGENTS.md                   # Canonical governance rules for AI coding agents
├── DIRECTIVES.md               # Engineering, CI/CD, and security policies
├── README.md                   # Project documentation
├── workspace.config.template.json # Template for project variables
├── .skills/                    # Modular skills executable by agents
│   ├── cicd-quality-gate/      # 5 Mandatory quality gates (Go / No-Go)
│   ├── multi-agent-cowork/     # Concurrency locks and shared findings
│   ├── post-deploy-verification/# Real DOM and public endpoint auditing
│   ├── ui-anti-cliche-design/  # Big Tech design system specifications
│   ├── zero-test-pollution/    # Automated database teardown patterns
│   ├── whatsapp-monitor-react/ # WhatsApp client bridge (Monitor & React modes)
│   ├── google-drive-sync/      # Google Drive transcripts and docs synchronizer
│   ├── environment-preflight-tooling/ # CLI diagnostic and fast dependency installer
│   ├── web-design-guidelines/     # Accessibility, UX, and performance audit guidance
│   ├── agent-browser/             # Isolated browser automation workflow
│   ├── brainstorming/             # Discovery and design before implementation
│   └── writing-plans/             # Detailed implementation plans after approval
├── scripts/                    # Dashboard, bridge, and diagnostic engines
│   ├── setup_server.py         # Python Threaded HTTP server (:8765)
│   ├── setup_dashboard.html    # Obsidian/Zinc responsive dashboard UI
│   ├── preflight_check.py      # High-performance parallel diagnostic engine
│   ├── google_drive_sync.py    # Google Drive document ingestion tool
│   └── whatsapp_bridge/        # Node.js Baileys client bridge (:4114)
├── apps/                       # Frontends, SPAs, and client applications
├── services/                   # Backend services, APIs, and background workers
├── packages/                   # Shared monorepo packages and libraries
└── memory/                     # Persistent agent telemetry and coworking
    ├── daily_logs/             # Chronological work logs (YYYY-MM-DD.md)
    └── cowork/                 # Active locks, blackboard, and handoffs
```

## Templates, skills, and repository pre-flight

The portable operating model is documented in [docs/TEMPLATE_CUSTOMIZATION.md](docs/TEMPLATE_CUSTOMIZATION.md). The vendored skills, source revisions, and routing rules are documented in [docs/EXTERNAL_SKILLS.md](docs/EXTERNAL_SKILLS.md). Before changing or operating a repository, follow [docs/REPOSITORY_PREFLIGHT.md](docs/REPOSITORY_PREFLIGHT.md).

## Community and safety

Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md); conduct is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report vulnerabilities privately through [SECURITY.md](SECURITY.md), use [SUPPORT.md](SUPPORT.md) for public support boundaries, and review [third-party notices](THIRD_PARTY_NOTICES.md) before redistributing vendored skills. The OS treats connector credentials, local state, pages, retrieved documents, and third-party instructions as untrusted until an operator has explicitly authorized the relevant action.

### v2.0.0 release scope

v2.0.0 is a documentation and governance release. It does not claim runtime hardening, connector isolation, performance validation, or production deployment. Treat the setup server and optional bridges as local-only until a later runtime release implements and validates the controls described in the policies.

---

## 🤝 Multi-Agent Cowork Protocol

When running multiple autonomous agents or subagents concurrently, Agent Workspace OS prevents race conditions via an atomic file-based state machine:

1. **Anti-Collision Locks**: Before modifying files in `apps/` or `services/`, the agent registers an exclusive lock in `memory/cowork/active_tasks.json`.
2. **Shared Blackboard**: When an agent discovers a root-cause bug or validates a database schema migration, it publishes a structured note to `memory/cowork/blackboard.json`.
3. **Formal Handoffs**: When transitioning tasks between sessions or agents, a Markdown transition report is archived in `memory/cowork/handoffs/`.

---

## 🛠️ Supported Agents

Agent Workspace OS is model-agnostic and runtime-agnostic:
- **Anthropic Claude Code / Claude Desktop**
- **Google Antigravity / Gemini CLI**
- **Cursor IDE (Composer & Background Agents)**
- **OpenAI Codex / ChatGPT CLI**
- **Hermes Agent Suite**
- **GitHub Copilot Workspace**
- **Windsurf Cascade**

---

## 🚀 Changelog

### v2.0.0 (2026-09-17)
- **Safe operating contract**: Added explicit authorization, least-privilege connector, browser isolation, trusted-content, and update rules for agents and operators.
- **Transparent scope**: Documents this as a governance release; runtime security hardening and production validation are not part of v2.0.0.
- **Community governance**: Added security reporting, support boundaries, release policy, and a documentation index.
- **Reproducible maintenance**: Added factual validation requirements and contribution/PR criteria for provenance, branches, and unexecuted checks.
- **External skills**: Cataloged upstream sources, revisions, licenses, routing, and update procedure for the vendored skills.

### v1.1.0 (2026-09-14)
- **1-Click Launchers**: Added `start.bat` (Windows) and `start.sh` (macOS/Linux) for instant dashboard opening.
- **Setup & Control Dashboard Server v2**: Zero-dependency Python server (`scripts/setup_server.py`) with dark Obsidian/Zinc interface and live SSE streaming installation.
- **WhatsApp Client Bridge**: Dual-mode bridge (Monitor & React) with QR code pairing for listening and dispatching tasks directly from WhatsApp chats.
- **High-Performance Concurrent Preflight**: Parallel tool discovery (`scripts/preflight_check.py`) using `ThreadPoolExecutor` and direct local config inspection (`<4.2s`).
- **Google Drive Synchronizer**: Direct ingestion of meeting transcripts and Google Docs into workspace memory (`scripts/google_drive_sync.py`).
- **3 New Canonical Skills**: `.skills/whatsapp-monitor-react`, `.skills/google-drive-sync`, and `.skills/environment-preflight-tooling`.
- **Zero Native Dialogs**: Universal dark glassmorphic toast notification system.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

