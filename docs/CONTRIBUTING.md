# Contributing to Agent Workspace OS

Thank you for your interest in improving Agent Workspace OS! We welcome contributions from human engineers and autonomous AI agents alike.

## How to Contribute
1. **Fork the repository** on GitHub.
2. **Create a feature branch**; do not commit directly to `main`. Use `feat/`, `fix/`, `docs/`, `chore/`, or `release/` followed by a concise slug.
3. **Ensure Zero Clutter**: Do not leave temporary scripts or test logs in the repository root.
4. **Follow the Rulebook**: Adhere strictly to the guidelines defined in `AGENTS.md` and `DIRECTIVES.md`.
5. **Run the Repository Pre-flight**: Follow [`docs/REPOSITORY_PREFLIGHT.md`](docs/REPOSITORY_PREFLIGHT.md) before modifying or publishing changes.
6. **Open a Pull Request** using the provided PR template.

## Before Opening a Pull Request

- Run [the repository pre-flight](docs/REPOSITORY_PREFLIGHT.md) and describe the target, scope, and validation actually performed.
- Update the relevant README, protocol, or reference when behavior changes.
- Do not add credentials, private workspace state, generated connector sessions, local telemetry, or copied third-party skills without recorded provenance and license.
- Report vulnerabilities privately through [SECURITY.md](SECURITY.md), not through public issues.

## Review Expectations

Maintainers review scope, backwards compatibility, security boundaries, documentation, provenance, and evidence. A check that was not run must be marked as not run with its reason; it must never be reported as passing.

## Quality Standards
All contributions must pass the [5 Mandatory Quality Gates](.skills/cicd-quality-gate/SKILL.md):
- Zero linting or typechecking errors.
- Clean execution logs (no unhandled exceptions).
- Responsive UI standards (no horizontal scrollbars, real SVG icons, no system emojis).
- Zero test data pollution.
