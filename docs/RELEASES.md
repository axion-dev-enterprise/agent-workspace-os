# Release and validation policy

## Versioning

Agent Workspace OS uses semantic versioning. Increment the major version for incompatible governance or operating-contract changes, the minor version for backward-compatible features, and the patch version for compatible corrections.

## Release checklist

1. Start from a clean, reviewed release branch and fetch the intended base branch.
2. Confirm the Git identity, remote, version fields, changelog, and applicable documentation.
3. Run the applicable quality gates from `DIRECTIVES.md`; record each command and result. Mark a gate as not run when the environment or policy prevents it.
4. Review the staged diff for secrets, user state, generated sessions, and unlicensed third-party material.
5. Merge through a reviewed Pull Request, create an annotated tag, and publish release notes that state scope, compatibility, validation, and limitations.

## Documentation-only releases

A documentation-only release does not imply runtime validation, performance validation, security certification, or production deployment. Its release metadata must say so explicitly.
