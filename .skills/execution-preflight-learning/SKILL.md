---
name: execution-preflight-learning
description: "Protocolo canônico de Pre-flight Checks e aprendizado contínuo de erros de execução para agentes de IA. Previne retries cegos, deploys sem linking (ex: Vercel sem .vercel), destruição indevida de caches e vazamento de tokens."
---

# Execution Pre-flight & Error Learning Skill

## 1. Principle: Check Before You Strike
Autonomous coding agents often fall into **Blind Retry Loops**: when an execution fails, they retry the exact same failing command or destroy local caches (like `.vercel` or `.next`), wasting minutes and worsening the problem.

> **MANDATORY RULE**: No agent shall execute remote deployments, heavy builds, or state mutations without running deterministic local **Pre-flight Checks** first.

---

## 2. Common Execution Failure Modes & Pre-flight Checklists

### Case 1: Cloud Deployments (e.g. Vercel Unlinked Deploy)
- **Failure Mode**: The agent runs `vercel deploy` blindly without checking if the repository has an active project link (`.vercel/project.json`), triggering failed anonymous builds or missing environment variables.
- **Prohibited Anti-Patterns**:
  1. 🚫 **Deleting Caches/Configs**: Running `rm -rf .vercel` to "retry". This deletes the project linking itself!
  2. 🚫 **Blind Retries**: Re-running `vercel deploy --temporary` repeatedly without addressing the root cause.
  3. 🚫 **Credential Leaks**: Running `echo $env:TOKEN` or `echo $TOKEN` in the terminal to inspect secrets.
- **Mandatory Pre-flight Checklist**:
  1. Verify `.vercel/project.json` exists. If missing, run `vercel link --yes` or `vercel pull --yes`.
  2. Verify if prebuilt deployment is required: `vercel build --prod` followed by `vercel deploy --prebuilt --prod`.
  3. Never delete `.vercel` in a retry loop.

### Case 2: Git Remote Operations
- **Failure Mode**: Pushing to an unconfigured remote or with divergent history.
- **Mandatory Pre-flight Checklist**:
  1. Verify Git user name and email are configured.
  2. Verify current branch (`git branch --show-current`).
  3. Run `git fetch` before pushing to verify no upstream divergence.

### Case 3: Docker & Background Containers
- **Failure Mode**: Port binding collision or missing environment variables.
- **Mandatory Pre-flight Checklist**:
  1. Check if the exposed port is already occupied (`netstat` / `ss`).
  2. Check if `.env` exists and contains required keys before running `docker compose up -d`.

---

## 3. Continuous Error Learning Protocol
When an agent encounters a new failure mode:
1. **Stop Immediately**: Never execute more than 1 retry without modifying the underlying cause.
2. **Post to Shared Memory**: Publish the lesson to `memory/cowork/blackboard.json` with category `ERROR_LESSON_LEARNED`.
3. **Update Daily Log**: Record the root cause and remedy in `memory/daily_logs/YYYY-MM-DD.md`.
4. **Update This Skill**: Append the new failure mode to this document so future agents avoid the mistake.
