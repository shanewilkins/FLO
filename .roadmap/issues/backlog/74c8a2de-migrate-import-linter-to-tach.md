---
id: 74c8a2de
title: Migrate import-linter to Tach
headline: Express module dependencies and public interfaces with Tach while preserving architecture protections.
priority: low
status: todo
archived: false
issue_type: other
milestone: null
labels: [tooling, architecture]
remote_ids: {}
created: '2026-11-13T00:00:00-06:00'
updated: '2026-11-13T00:00:00-06:00'
assignee: null
estimated_hours: null
due_date: null
depends_on: []
blocks: []
github_issue: null
---

# Migrate import-linter to Tach

Deferred tooling improvement; outside the critical path and not assigned to a
release milestone. Pre-commit performance is acceptable at the current project
size. The motivation is clearer architectural rules through explicit module
dependencies and public interfaces, rather than speed.

## Acceptance Criteria

- Translate the existing forbidden-import contracts and sibling-cycle checks to
  deliberate Tach module boundaries and dependency rules.
- Prove equivalent protection with deliberate violations, including indirect
  dependency paths, new modules, relative imports, and cycles at the currently
  enforced depth.
- Configure source roots, unconfigured-module handling, and `TYPE_CHECKING`
  imports explicitly so defaults do not weaken coverage.
- Run both tools during migration; remove import-linter only after parity is
  demonstrated, updating dependencies, the lockfile, pre-commit, policy tests,
  and relevant documentation.
- Assess Tach interfaces for cross-package public API enforcement while
  preserving the intent of existing private-import policy checks.
- Retain `scripts/architecture_boundaries.py` for responsibility checks beyond
  import relationships.

## Notes

Review generated dependency configuration against the intended architecture;
do not treat `tach sync` output as the desired policy automatically.
