---
id: e4d655b4
title: SPPM label length policy and truncation matrix
headline: Formalize and implement max-length/wrapping/truncation policy per SPPM label
  surface.\n\nScope\n- De
priority: medium
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,text,ux
remote_ids: {}
created: '2026-05-11T17:22:35.634128+00:00'
updated: '2026-05-11T17:27:04.263722+00:00'
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

Formalize and implement max-length/wrapping/truncation policy per SPPM label surface.\n\nScope\n- Define limits and wrap/truncation behavior for: task names, decision text, queue badges, edge labels, footer/header text.\n- Harmonize policy with existing CLI truncation controls and output profiles.\n- Add edge-case fixtures for long labels.\n\nAcceptance Criteria\n- Policy table is documented and test-backed.\n- Long labels never destabilize layout unexpectedly.\n- Behavior is deterministic for each truncation policy mode.\n- Showcase includes at least one long-label stress example.
