---
id: 534bbd16
title: Integrate sizing verification with dimension system
headline: Revisit sizing verification once reusable dimension primitives are in place.
priority: low
status: todo
archived: false
issue_type: other
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-05T18:57:04.277819+00:00'
updated: '2026-05-05T19:42:36.398236+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- ff18b5c7
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

# Integrate sizing verification with dimension system

Revisit SPPM sizing verification after multi-unit dimensions exist and tighten the validation workflow.

## Why

Basic sizing verification already exists, but it is limited by pixel-only assumptions and Graphviz layout behavior. Once the shared dimension system lands, sizing validation should be tightened and better integrated.

## Acceptance Criteria

- Sizing verification can consume the shared dimension model.
- Validation logic is clearer about intended dimensions versus rendered approximations.
- The workflow is robust enough for regular regression checking.

## Notes

This is intentionally a follow-up issue rather than part of the initial dimension-system implementation.
