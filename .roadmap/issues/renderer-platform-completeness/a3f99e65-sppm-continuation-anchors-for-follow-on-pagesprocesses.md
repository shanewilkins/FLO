---
id: a3f99e65
title: SPPM continuation anchors for follow-on pages/processes
headline: Introduce first-class continuation anchors so SPPM diagrams can deterministically
  reference second-p
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,renderer,semantics
remote_ids: {}
created: '2026-05-11T17:22:30.602130+00:00'
updated: '2026-05-11T17:27:02.190631+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
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

Introduce first-class continuation anchors so SPPM diagrams can deterministically reference second-page or follow-on processes.\n\nScope\n- Add a continuation anchor visual style and stable reference token semantics.\n- Support anchor metadata in render inputs/IR mapping.\n- Ensure deterministic placement/labeling in DOT and SVG outputs.\n\nAcceptance Criteria\n- Feature showcase includes at least one continuation anchor example.\n- Anchor ID/token is stable across repeated renders.\n- Reference edge labels remain deterministic and test-covered.\n- Exported SVG and DOT preserve continuation semantics.
