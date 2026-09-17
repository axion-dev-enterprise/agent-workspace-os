# Security Policy

## Supported release

Security fixes are maintained on the latest released version of Agent Workspace OS. Include the version, operating system, and the minimal safe reproduction when reporting a problem.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Send a concise report to `axionenterprise777@gmail.com` with the subject `Agent Workspace OS security report`.

Include the affected version, component or file, impact, reproduction steps that do not expose third-party data, and any suggested mitigation. Do not send API keys, passwords, session cookies, private message content, payment data, or live destructive payloads.

The maintainers will acknowledge the report, assess scope, and coordinate a fix or disclosure path. Public disclosure should wait until maintainers confirm that users have a remediation path.

## Security boundaries

Agent Workspace OS can coordinate local tools and optional connectors. It does not grant permission to access an account, send messages, submit forms, deploy software, purchase anything, or expose a local service to a network. Operators must explicitly authorize those actions and configure credentials outside version control.

v2.0.0 is a governance release. It does not harden the existing setup server or connector runtime. Keep those services on a trusted local machine and do not expose them to an untrusted network until a runtime hardening release has implemented and validated the controls in `AGENTS.md` and `DIRECTIVES.md`.

For contributor requirements, read [AGENTS.md](AGENTS.md), [DIRECTIVES.md](DIRECTIVES.md), and [docs/REPOSITORY_PREFLIGHT.md](docs/REPOSITORY_PREFLIGHT.md).
