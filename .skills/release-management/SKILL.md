---
name: release-management
description: Prepare a traceable release through versioning, evidence, review, tagging, and factual release notes.
---

# Release management

Use a dedicated branch and a reviewable Pull Request. Update version metadata, changelog, migration notes, and documentation together. Record which checks ran, which did not, and why. Review the staged diff for secrets, generated runtime state, and third-party provenance before publishing.

Merge only through the approved repository process. Create a tag and public release only after the merged commit is verified as the intended target. A documentation-only release must not claim runtime validation, hardening, or deployment.
