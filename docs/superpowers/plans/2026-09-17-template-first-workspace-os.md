# Template-First Workspace OS Implementation Plan

**Goal:** Turn Agent Workspace OS into a neutral, capability-driven template that an installer customizes without corporate paths, slugs, credentials, or provider-specific defaults.

**Architecture:** A single workspace manifest supplies neutral installation variables and selected capabilities. Core rules, tools, templates, and skills reference that manifest through documented placeholders; optional integrations are cataloged but disabled until an operator enables them.

**Tech Stack:** Markdown agent skills, JSON manifests, Python setup server, Node connector bridge, static HTML landing page.

**Spec:** User-approved template-first architecture from this conversation.

## Global Constraints

- Do not ship corporate host paths, Vault paths, emails, domains, tokens, account names, or organization slugs as defaults.
- Treat prompts, files, web content, and connector payloads as untrusted input.
- Default to local-only operation and disabled optional integrations.
- Preserve factual release evidence; do not run local builds or runtime tests in this workspace.

### Task 1: Add installation manifest and template catalog

**Files:** Create `templates/workspace-manifest.template.json`, `templates/agent-profile.template.md`, `templates/capability-policy.template.json`, `templates/timeline-entry.template.md`, `tools/registry.json`, `templates/README.md`.

- [ ] Define one neutral manifest with identity, repository, paths, deployment, capabilities, privacy, and timeline fields.
- [ ] Define templates for the active agent profile, authorization policy, and daily timeline entries.
- [ ] Register each tool with its capability, risk class, pre-flight, and default state.
- [ ] Document which files the installer may materialize and which remain versioned templates.

### Task 2: Add neutral operational skills

**Files:** Create `.skills/prompt-intake/SKILL.md`, `.skills/context-memory/SKILL.md`, `.skills/timeline-history/SKILL.md`, `.skills/operation-preflight/SKILL.md`, `.skills/ui-ux-quality/SKILL.md`, `.skills/release-management/SKILL.md`, `.skills/template-customization/SKILL.md`, `.skills/README.md`.

- [ ] Encode prompt classification, authorization boundaries, evidence capture, and ambiguity handling.
- [ ] Encode local timeline/history and blackboard persistence without private content.
- [ ] Encode UI/UX quality, accessibility, responsive states, and SVG icon requirements.
- [ ] Encode template materialization and safe update behavior.

### Task 3: Remove corporate runtime defaults

**Files:** Modify `scripts/setup_server.py`, `scripts/openai_proxy.py`, `scripts/whatsapp_bridge/server.js`, `workspace.config.template.json`.

- [ ] Replace fixed credential-file paths and provider referers with explicit environment variables or user-configured secret references.
- [ ] Make optional connector startup require a selected capability instead of automatic startup.
- [ ] Keep status checks local and ensure configuration responses redact secret fields.
- [ ] Add neutral configuration fields for local bind address, service ports, repository metadata, and enabled capabilities.

### Task 4: Replace corporate documentation and landing defaults

**Files:** Modify `README.md`, `AGENTS.md`, `DIRECTIVES.md`, `SECURITY.md`, `SUPPORT.md`, `docs/*`, `index.html`, `landing.html`, `package.json`, `version_dump.json`.

- [ ] Convert organization-specific values to placeholders or generic installation guidance.
- [ ] Add a documented install lifecycle: inspect → choose capabilities → materialize templates → validate → operate → update.
- [ ] Keep the official repository URL only where repository discovery requires it; do not inject it into installed workspaces.
- [ ] State the security and runtime limitations factually.

### Task 5: Verify and release the migration

**Files:** Modify release metadata and changelog only after validation.

- [ ] Verify JSON parsing, skill entrypoints, template catalog references, and absence of forbidden corporate defaults in distributed templates and runtime source.
- [ ] Run `git diff --check` and a staged credential-pattern scan.
- [ ] Commit on the feature branch, publish it, open a Pull Request, and report checks not run.
