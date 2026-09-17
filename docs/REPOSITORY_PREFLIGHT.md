# Repository Pre-flight

Run this checklist before modifying, committing, publishing, or operating the configured repository. It is deliberately read-only until the final authorization gate.

## 1. Establish the target

- Confirm the working directory is the intended checkout and that `origin` matches `workspace.repository_url` in the local manifest.
- Read `AGENTS.md`, `DIRECTIVES.md`, `WORKFLOW.md`, and the relevant protocol before acting.
- Record the exact user request and identify whether it authorizes only analysis or also an external mutation.

## 2. Inspect Git state

```powershell
git status --short
git branch --show-current
git remote -v
git config --get user.name
git config --get user.email
```

Expected identity is the installer-configured `git.user_name` and `git.user_email`. A dirty worktree belongs to its author: preserve it, identify overlapping files, and do not reset, checkout, stash, or overwrite it without authorization.

## 3. Validate vendored skills

Every declared external skill must contain a readable `SKILL.md` and be listed in [EXTERNAL_SKILLS.md](EXTERNAL_SKILLS.md). Review its declared tools and instructions before use. The required installed set is:

```text
.skills/web-design-guidelines/SKILL.md
.skills/agent-browser/SKILL.md
.skills/brainstorming/SKILL.md
.skills/writing-plans/SKILL.md
```

The catalog's revision is the provenance record. It is not a promise that upstream behavior remains unchanged after that revision.

## 4. Choose the operating path

| Requested work | Required path |
| --- | --- |
| New feature or behavior change | `brainstorming` → approved design → `writing-plans` → implementation |
| UI review or UI implementation | `web-design-guidelines`, plus the applicable project design rules |
| Browser inspection or testing | `agent-browser` in an isolated session, with authorized domains only |
| Deployment, Docker, data migration, or remote action | Follow `.skills/execution-preflight-learning/SKILL.md` and perform the relevant tenant/whoami probe first |

## 5. Final mutation gate

Only after the preceding checks may an authorized mutation proceed. Before a commit or external action, verify the precise target, confirm the required credentials belong to the intended tenant without printing secrets, and inspect the staged diff for `.env`, keys, tokens, generated runtime data, or user-private files.

This repository has no GitHub Actions workflow at the time this document was added. Do not report CI validation unless an actual remote run exists. The root workspace policy also prohibits local builds and test runs; use the approved CI/CD path when validation is required.
