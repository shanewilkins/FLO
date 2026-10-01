---
id: 8c4f9d21
title: Fix wrapped SPPM cluster label leak and continuation routing
headline: Keep wrapped SPPM pages readable by removing chunk-as-cluster artifacts
  and aligning continuation routing with the intended reading direction.
priority: high
status: closed
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
- 048bbcb1
- 7b3865ba
- e7d428a4
blocks: []
actual_start_date: '2026-05-10T00:00:00+00:00'
actual_end_date: '2026-05-10T00:00:00+00:00'
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

## Fix wrapped SPPM cluster label leak and continuation routing

Correct the wrapped SPPM output path so wrapped rows do not render as visible Graphviz clusters and continuation connectors follow the intended wrapped reading flow.

## Why

The current wrapped SPPM output duplicates the process header inside each wrapped chunk and routes off-page continuation edges through an awkward shared gutter. The result is visually noisy and makes the reference artifacts look broken even when the underlying model data is correct.

## Acceptance Criteria

- Wrapped SPPM rows no longer render as visible cluster boxes or repeat the process header band inside each chunk.
- Wrapped LR output preserves a coherent left-to-right reading contract across rows without forcing contradictory global rank direction and port choices.
- Continuation labels and connectors remain readable and stable across regenerated reference artifacts.
- The wash-n-fold wrapped reference render is updated and covered by a regression-oriented check where practical.

## Notes

Use `renders/reference/washnfold_sppm_wrap800.dot` as the concrete repro artifact. Treat this as a renderer/layout defect in the wrapped SPPM path, not a data-model issue.
