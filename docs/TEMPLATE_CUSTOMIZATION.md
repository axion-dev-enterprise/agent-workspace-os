# Template Customization

Agent Workspace OS ships as a neutral distribution. The repository contains reusable rules and examples; the active workspace belongs to its installer.

## First-run contract

1. Copy `templates/workspace-manifest.template.json` to `workspace/workspace-manifest.json` and replace every `{{PLACEHOLDER}}`.
2. Copy `templates/capability-policy.template.json` to `workspace/capability-policy.json`. Keep every external capability disabled until its owner grants authorization.
3. Copy `templates/agent-profile.template.md` and complete the operating role, owner, safety boundary, and preferred communication style.
4. Configure credential *references* only. Supply values through the chosen local secret manager or process environment.
5. Keep the repository templates unchanged. Runtime state belongs under `workspace/` and `memory/`, which must be excluded from version control when it contains local data.

## Portable operating model

`AGENTS.md` and `DIRECTIVES.md` define shared behavior. The installed manifest supplies workspace-specific values. `tools/registry.json` declares available tools and their required preflight checks. `.skills/` contains vendor-neutral operating skills. `templates/timeline-entry.template.md` supplies the append-only history format.

## Connector activation

Messaging, browser mutation, source-control publishing, deployments, cloud drives, and model proxies are optional capabilities. Enable one only after recording the owner, scope, credential reference, authorization condition, and rollback path in the local capability policy.
