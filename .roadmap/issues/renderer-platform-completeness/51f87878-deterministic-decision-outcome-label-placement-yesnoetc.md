---
id: 51f87878
title: Deterministic decision outcome label placement (yes/no/etc.)
headline: Define and enforce deterministic placement rules for decision edge outcome
  labels (yes/no/etc.).\n\n
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,layout,labels
remote_ids: {}
created: '2026-05-11T17:22:33.116202+00:00'
updated: '2026-05-11T17:27:03.240231+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 114c6965
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

Define and enforce deterministic placement rules for decision edge outcome labels (yes/no/etc.).\n\nScope\n- Establish placement rules by side/port/direction with fixed offsets.\n- Implement deterministic tie-break logic to prevent drift across runs.\n- Keep labels clear of decision glyphs and key edge paths.\n\nAcceptance Criteria\n- Outcome labels render at deterministic positions for equivalent input.\n- No random drift between repeated builds.\n- Regression tests cover representative decision geometries (LR/TB where applicable).\n- Implementation uses shared callout/annotation mechanics where feasible (dependency).
