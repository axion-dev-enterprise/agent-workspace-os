---
name: operation-preflight
description: Verify target, authorization, identity, state, and rollback conditions before an external or difficult-to-reverse action.
---

# Operation pre-flight

Before a mutation, identify the exact target and effect. Check the local capability policy, workspace state, credentials' account/tenant identity, current branch and diff when Git is involved, and relevant service health when infrastructure is involved.

Fetch and inspect changes before merge or rebase. Stop on a dirty worktree, missing authorization, failed identity check, ambiguous destination, or failed prerequisite. Diagnose the failure before one corrected retry; never delete configuration or caches to force progress.
