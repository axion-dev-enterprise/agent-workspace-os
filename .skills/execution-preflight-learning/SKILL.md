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

### Case 4: Remote Docker build over Tailscale SSH
- **Failure Mode**: A remote `docker build -f services/api/Dockerfile ... <absolute-release-context>` resolves the Dockerfile path against the SSH shell working directory and fails with `lstat services: no such file or directory`.
- **Remedy**: Resolve both inputs explicitly on the remote host: `-f /opt/axion/isabela/releases/<release>/services/api/Dockerfile` and context `/opt/axion/isabela/releases/<release>`. Confirm the allowlisted release files exist before rebuilding.

### Case 5: Disposable container smoke teardown
- **Failure Mode**: `docker stop` returns while a `--rm` container is still being removed, so an immediate `docker ps -a` assertion can fail even though a later read shows no container.
- **Remedy**: Cleanup the exact unique smoke container with `docker rm -f <smoke-name>` and verify that exact name is absent. Never broaden cleanup to unrelated containers. Mount an ephemeral writable directory for storage health checks so the smoke validates all configured dependencies without mounting or writing production documents.

### Case 6: Playwright E2E collides with an active Next.js preview
- **Failure Mode**: The default E2E ports may already be owned by a user preview, and starting a second `next dev` may then fail on the shared `.next` lock even after changing ports.
- **Remedy**: Inspect both configured ports and the active Next process before starting tests. Preserve the running preview. Build the E2E web app with `ISABELA_E2E_DIST_DIR` under `temp/`, `ISABELA_API_ORIGIN` pointing at the exact isolated API port that Playwright will start, then run Playwright with `ISABELA_E2E_PRODUCTION=1` and distinct `ISABELA_E2E_API_PORT` / `ISABELA_E2E_WEB_PORT`. The Next rewrite target is evaluated at build time; a different build/runtime port produces `ECONNREFUSED`. Production mode also avoids cold dynamic-route compilation exceeding dev-mode assertion defaults. Remove only temporary build/test artifacts after confirming the server processes stopped.

---

## 3. Continuous Error Learning Protocol
When an agent encounters a new failure mode:
1. **Stop Immediately**: Never execute more than 1 retry without modifying the underlying cause.
2. **Post to Shared Memory**: Publish the lesson to `memory/cowork/blackboard.json` with category `ERROR_LESSON_LEARNED`.
3. **Update Daily Log**: Record the root cause and remedy in `memory/daily_logs/YYYY-MM-DD.md`.
4. **Update This Skill**: Append the new failure mode to this document so future agents avoid the mistake.

### Case 7: Workspace utility invoked from the wrong base directory
- Failure mode: A root utility such as `scripts/vault_loader.py` is invoked while the shell is in a nested app path, or a root-relative path is mistakenly prefixed with `../../` while already at `C:/workspace`.
- Remedy: Confirm the active directory with `Get-Location`; resolve the utility from the canonical workspace root or use its verified absolute path. Before trying again, distinguish nested-app cwd from workspace-root cwd. Never dump credentials while diagnosing loader behavior.

### Case 8: Windows package-manager shim launched through Python subprocess
- Failure mode: `subprocess.run(["npm", ...])` cannot resolve `npm` from Python on Windows because the entry point is `npm.cmd`; this fails before npm or Wrangler starts.
- Remedy: Keep the command fixed and non-interactive, then use PowerShell's resolved npm command directly or invoke `npm.cmd` through `COMSPEC`/`shell=True`. Confirm the shim path first; do not repeat or rebuild when the child process never launched.

### Case 9: Compose CLI absent and nested Tailscale SSH quoting
- Failure mode: Docker Compose validation on Windows failed because Docker CLI was not installed; a remote shell command also failed its first `test` guard because nested PowerShell/SSH quoting changed the command before execution. No Docker or VPS mutation occurred in either failure.
- Remedy: Check `Get-Command docker.exe` before invoking Compose. When the project has a YAML parser, validate syntax and structural invariants with it. For remote shell commands, authenticate the exact target with `tailscale ssh <user>@<host> whoami`, pass the complete remote script as one PowerShell single-quoted argument, and verify host guards before side effects. Check `$?` and command presence; `$LASTEXITCODE` can remain unset after PowerShell reports a missing command.

### Case 10: Python interpolation collides with SQL format placeholders
- Failure mode: Python `%` formatting interpreted PostgreSQL's `format(... %L ...)` placeholder while composing a credential-provisioning statement. The script stopped before invoking `psql`; only the generated secret had already been safely stored in the local categorized Vault.
- Remedy: Prefer parameterization or an f-string with a strictly validated generated secret; otherwise escape SQL percent signs for the Python formatter. Transmit credential-bearing SQL over stdin, suppress raw database errors, and verify that the database command was not reached before retrying.

### Case 11: Next production E2E built with a different API port
- Failure mode: Playwright started the isolated API on one port while the previously built Next production server kept a rewrite target for another port, causing repeated `ECONNREFUSED` during `/api/health` checks.
- Root cause: `ISABELA_API_ORIGIN` is consumed by `next.config.js` during `next build`; changing only `ISABELA_E2E_API_PORT` at test time cannot update the built rewrite.
- Remedy: Set `ISABELA_API_ORIGIN` to the exact `ISABELA_E2E_API_PORT` before the isolated production build, then pass the same API port to Playwright. Confirm the API and web ports are free before starting.

### Case 12: Prometheus boolean CLI flags
- Failure mode: `prom/prometheus` v3.15 exited repeatedly with `unexpected false` when passed `--web.enable-lifecycle=false`.
- Root cause: this flag is boolean and the CLI parser treats the explicit `false` token as an unexpected positional argument; false is already the default.
- Remedy: Omit the flag when the default is desired. Validate config and rules with `promtool` before starting the long-running service; inspect the exact container logs before retrying.

### Case 13: Validating root-owned release mounts as an unprivileged image user
- Failure mode: one-shot `promtool` could not read config files mounted from the mode-restricted release directory.
- Root cause: the image runs as a non-root user while release directories/files are intentionally inaccessible to that UID.
- Remedy: For read-only validation only, use a disposable container with `--user 0:0`, `--network none`, a read-only bind mount, and the same resource limits; never loosen release-directory permissions to accommodate a validator.

### Case 14: Nested quoting for remote `node -e`
- Failure mode: a read-only Tailscale SSH probe reached Node with escaped quote characters still present and failed to parse JavaScript.
- Root cause: PowerShell string interpolation plus the SSH remote-shell layer changed quoting before Node received the script.
- Remedy: Put the remote shell program in a PowerShell single-quoted here-string and call Tailscale SSH once with that value. Keep the Node source's own quotes literal; verify exit status before following with other probes.

### Case 15: Tailscale SSH stdin archive and newly mounted runtime module
- Failure mode: Python `tarfile` in gzip read mode rejected the non-seekable SSH stdin stream; on the next attempt, a `node --check` ran before Compose mounted a newly added source file. The deployment gate detected both failures and restored the preflight files; service health was rechecked before continuing.
- Root cause: `r:gz` needs a seekable stream, and the runtime syntax check assumed the new bind mount was already active.
- Remedy: Read the bounded archive into `io.BytesIO` before opening it, validate the exact allowlist and hashes, apply the Compose mount, validate Compose, recreate only the named service, then run syntax and health gates. On failure, restore the exact file/config backups and verify service health before another attempt.

### Case 16: Isolated Playwright runner encounters an occupied default API port
- Failure mode: Production E2E refused to start because Node already listened on `127.0.0.1:4106`; the runner correctly had `reuseExistingServer=false`.
- Root cause: A local project service already owned the default API port.
- Remedy: Identify the owning PID without terminating it, confirm separate API/web ports are free, and set `ISABELA_E2E_API_PORT`, `ISABELA_E2E_WEB_PORT`, `ISABELA_E2E_DIST_DIR`, and `ISABELA_E2E_REPORT_DIR` to isolated paths under `temp/`. Verify both ports are free and remove only the temporary `tsconfig` includes added by Next.

### Case 17: Live structured-output smoke differs from production prompt/token budget
- Failure mode: A minimal OpenRouter check hit the completion limit or returned provenance rejected by the application validator.
- Root cause: The diagnostic used a shorter prompt and smaller token cap than the actual worker, so it did not reproduce the model instructions governing generated/source attribution.
- Remedy: For a provider compatibility probe, send only synthetic content but use the exact production system prompt, JSON Schema, provider requirement, and a realistic bounded token budget. Validate the same provenance invariants as the application; never treat HTTP 200 alone as a valid suggestion.
