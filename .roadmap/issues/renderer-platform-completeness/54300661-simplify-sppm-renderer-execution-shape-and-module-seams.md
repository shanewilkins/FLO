---
id: '54300661'
title: Simplify SPPM renderer execution shape and module seams
headline: Assess and reduce SPPM renderer complexity by clarifying stage boundaries
  and extracting reusable se
priority: medium
status: todo
archived: false
issue_type: other
milestone: renderer-platform-completeness
labels:
- architecture,sppm,refactor
remote_ids: {}
created: '2026-05-11T17:23:11.883040+00:00'
updated: '2026-05-11T17:27:09.475967+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 5fbc5f50
- f620fe69
blocks: []
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

Assess and reduce SPPM renderer complexity by clarifying stage boundaries and extracting reusable seams without changing semantics.\n\nScope\n- Separate semantic planning, DOT emission, and SVG postprocess responsibilities.\n- Remove duplicate geometry/text policy logic where possible.\n- Improve module-level contracts for easier testing and maintenance.\n\nAcceptance Criteria\n- Complexity and file-length gates remain green with margin.\n- Existing semantic/regression tests pass unchanged.\n- Architecture note maps the final stage/seam boundaries.\n- Refactor does not alter rendering semantics for reference artifacts.\n\nBoundary Reference\n- See `docs/design/renderer_architecture_boundaries.md` for shared-core vs SPPM-only module placement rules.
