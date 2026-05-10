---
id: b1d3a6ef
title: Fix SPPM mainline rank drift and missing branch labels
headline: Preserve a straight primary SPPM spine in non-wrapped renders and keep
  decision branch semantics visible in reference outputs.
priority: high
status: todo
archived: false
issue_type: other
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-10T00:00:00+00:00'
updated: '2026-05-10T00:00:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 47c38a4e
- ce07a4e0
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

## Fix SPPM mainline rank drift and missing branch labels

Correct the non-wrapped SPPM layout path so rework-lane constraints do not distort the primary spine and decision outcomes remain visible in the rendered reference artifacts.

## Why

The current `sppm_feature_showcase` output bends the mainline diagonally because secondary-line alignment constraints pull key nodes off the intended rank. The same output also drops decision outcome labels that are present in the source model, which makes the showcase a weak reference artifact for SPPM semantics.

## Acceptance Criteria

- Non-wrapped LR SPPM renders keep the primary process spine visually straight unless the model explicitly requires a branch.
- Secondary-line and rework alignment constraints no longer pull mainline decision and task nodes off their intended rank.
- Decision outcome labels such as `yes`/`no` and `pass`/`fail` are visible in the rendered output when present in the source model.
- The `sppm_feature_showcase` reference DOT and SVG artifacts are regenerated and serve as a regression repro for this bug.

## Notes

Use `renders/reference/sppm_feature_showcase.dot` and `renders/reference/sppm_feature_showcase.svg` as the primary repro artifacts. This issue is related to SPPM routing and constraint generation, but it is separate from the wrapped-page continuation defect.
