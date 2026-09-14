# SETUP_AGENT_DIRECTIVE.md — Universal AI Agent Directive

> **ATTENTION AI AGENT (Claude Code, Antigravity, Cursor, Codex, Hermes, Copilot, Windsurf):**  
> You are operating inside a repository governed by **Agent Workspace OS**.  
> Follow this deterministic protocol with zero hesitation and zero ambiguity.

---

## 🎯 Immediate Decision: Setup vs Update vs Task

```
                                 [Workspace Check]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     `workspace.config.json`                       `workspace.config.json`
          DOES NOT EXIST                                ALREADY EXISTS
                 │                                               │
                 ▼                                               ▼
      Run [SETUP_PROTOCOL.md]                     Check User Intent in Prompt
   (Conduct 6-question onboarding                 ┌──────────────┴──────────────┐
     or apply smart defaults)                     ▼                             ▼
                                          "update" / "sync"             "task" / "build"
                                                  │                             │
                                                  ▼                             ▼
                                       Run [UPDATE_PROTOCOL.md]       1. Check active_tasks.json
                                     (Pull upstream commits,          2. Acquire task lock
                                      preserve user config)           3. Follow AGENTS.md rules
```

---

## 🚀 Quick Execution Guide for Agents

### If User asks for "Setup" or "Initialize":
1. Read **[SETUP_PROTOCOL.md](SETUP_PROTOCOL.md)**.
2. Ask the 6 simple onboarding questions (or if user said "use defaults", apply sensible defaults automatically).
3. Create `workspace.config.json` from `workspace.config.template.json`.
4. Replace `{{PLACEHOLDER}}` tags in `AGENTS.md` and `DIRECTIVES.md`.
5. Initialize the canonical folder tree (`apps/`, `services/`, `packages/`, `docs/`, `memory/cowork/`).
6. Append entry to `memory/daily_logs/YYYY-MM-DD.md` and confirm completion.

### If User asks for "Update" or "Sync":
1. Read **[UPDATE_PROTOCOL.md](UPDATE_PROTOCOL.md)**.
2. Run `git fetch origin main`.
3. Review changes and merge non-destructively, **preserving 100% of user config and secrets**.
4. Sync memory in `memory/cowork/blackboard.json` and daily logs.

### If User asks to develop a feature or solve an issue:
1. Always check `memory/cowork/active_tasks.json` to prevent collisions.
2. Follow **[AGENTS.md](AGENTS.md)**:
   - **Zero Root Clutter**: Never drop loose test files in root.
   - **Zero False Positives**: Verify code empirically (HTTP 200, real DOM, syntax check).
   - **Zero Native Dialogs**: Use custom dark toasts, never `alert()` or `confirm()`.
   - **Daily Timeline**: Chronologically record all steps in `memory/daily_logs/YYYY-MM-DD.md`.
