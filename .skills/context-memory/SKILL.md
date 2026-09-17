---
name: context-memory
description: Load project context and preserve useful, sanitized operational knowledge across agent turns.
---

# Context and memory

Read the local manifest, agent profile, rules, recent timeline entries, and active-task state before changing a workspace. Keep durable facts in the blackboard only when they have evidence, a bounded scope, and a future operational use.

Never store secrets, raw prompts containing personal data, session cookies, private message bodies, or access tokens. Mark assumptions, stale information, and unverified claims explicitly.
