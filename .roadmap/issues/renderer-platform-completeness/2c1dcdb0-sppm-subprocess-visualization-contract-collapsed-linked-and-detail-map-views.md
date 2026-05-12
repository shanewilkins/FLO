---
id: 2c1dcdb0
title: SPPM subprocess visualization and discovery contract
headline: Define clear subprocess visualization and discovery semantics so parent
  and detail maps are easy to navigate.
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,subprocess,renderer,contract
remote_ids: {}
created: '2026-05-11T17:23:05.941884+00:00'
updated: '2026-05-12T18:40:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 47ad9c62
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

Define clear subprocess visualization and discovery semantics so parent maps and detail maps are easy to navigate and understand.

Why

SPPM subprocess support exists, but the contract is still ambiguous around when subprocesses are collapsed versus expanded, how detail-map references are surfaced, and what discovery cues indicate hidden complexity. Locking this contract removes ambiguity for renderer behavior and examples.

Scope

- Specify collapsed subprocess node presentation and required metadata callouts.
- Standardize link/anchor conventions between parent and detail-map outputs.
- Define detection/discovery cues (for example metadata-driven indicators) that help authors identify subprocess candidates without changing core authoring semantics.
- Keep showcase implementation details in dedicated showcase issues so this issue remains a contract/design slice.

Acceptance Criteria

- Subprocess nodes communicate scope and linkage consistently.
- Parent/detail-map references are stable and deterministic.
- Discovery cues for subprocess candidates are documented and test-covered where feasible.
- Documentation includes concrete examples and expected visuals for collapsed and linked variants.
