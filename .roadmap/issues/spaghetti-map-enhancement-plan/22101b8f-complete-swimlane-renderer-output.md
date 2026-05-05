---
id: 22101b8f
title: Complete swimlane renderer output
headline: Deliver lane-aware DOT output that satisfies the remaining v0.1 renderer
  acceptance.
priority: high
status: blocked
archived: false
issue_type: feature
milestone: spaghetti-map-enhancement-plan
labels: []
remote_ids: {}
created: '2026-05-05T17:17:29.675033+00:00'
updated: '2026-05-05T22:54:06.938859+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 07cb2436
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

# Complete swimlane renderer output

Finish swimlane renderer support so FLO can emit lane-aware DOT with stable IDs, labels, and decision labeling suitable for v0.1 acceptance.

## Why

The roadmap still treats `flo render --style swimlane` as an incomplete acceptance target, but it fits better alongside the dedicated renderer work for spaghetti and related diagram surfaces. This keeps v0.1 focused on core IR/compiler/export promises and treats swimlane as a renderer milestone that should follow shared platform work.

## Acceptance Criteria

- `flo render --style swimlane <file>` produces valid DOT output.
- Lane clustering is represented clearly and deterministically.
- Node IDs, labels, and decision labels render in the swimlane output.
- Existing example and integration coverage exercise the swimlane path.

## Notes

Keep the swimlane renderer grounded in canonical IR inputs only, and sequence it after the shared renderer-platform milestone where practical.
