---
name: template-customization
description: Materialize a personalized local workspace from neutral templates without changing the upstream distribution.
---

# Template customization

Read `templates/workspace-manifest.template.json`, the local capability policy, and the requested installation scope. Collect only the values required for the selected capabilities. Show the values that will be persisted, keep credentials outside versioned configuration, and create generated files only in the target workspace.

Replace placeholders only in copied active files. Preserve upstream templates, leave optional integrations disabled by default, and write a sanitized setup entry to the local timeline after successful materialization.
