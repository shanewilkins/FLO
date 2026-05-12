---
id: 9c2e4b7a
title: Refactor SPPM showcase subprocess into explicit mainline steps
headline: Rework the showcase process flow so subprocess internals are visible in
  realistic, readable mainline sequencing.
priority: high
status: todo
archived: false
issue_type: other
milestone: renderer-platform-completeness
labels:
- sppm,showcase,subprocess
remote_ids: {}
created: '2026-05-12T18:40:00+00:00'
updated: '2026-05-12T18:40:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks:
- 6f1ad0c3
actual_start_date: null
actual_end_date: null
progress_percentage: null
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

Refactor `examples/reference/sppm_feature_showcase.flo` so the subprocess path is represented as explicit, readable process steps in the main flow rather than relying on opaque inline subnodes.

Why

The current showcase demonstrates many features, but subprocess internals are still too compressed to communicate where work, quality checks, and handoffs occur. A clearer mainline narrative is needed before wrapped multi-page continuation examples can be trusted as reference output.

Scope

- Remove or minimize hidden inline `subnodes` in the showcase process section.
- Add explicit transitions for the subprocess path (for example assessment, execution, and quality gate steps) while preserving overall process semantics.
- Keep the example coherent and production-like rather than synthetic feature stacking.
- Update rendered reference artifacts tied to the showcase where applicable.

Acceptance Criteria

- The showcase process section reads as a coherent operational sequence with explicit subprocess-related steps.
- The resulting diagram remains readable in both default and publication-oriented output settings.
- Existing renderer behavior is unchanged; this is a showcase-model and artifact update.
- Regression checks or integration tests cover the intended output shape where practical.
