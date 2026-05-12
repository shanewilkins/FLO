---
id: 114c6965
title: Generalize annotation and callout layout
headline: Extract shared placement rules for annotations, callouts, and nearby explanatory boxes.
priority: medium
status: in_progress
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:37.925760+00:00'
updated: '2026-05-12T21:35:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-12T20:54:16+00:00'
actual_end_date: null
progress_percentage: 75
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

# Generalize annotation and callout layout

Extract shared annotation and callout placement logic from renderer-specific implementations so labels and data boxes can be managed consistently.

Boundary reference: `docs/design/renderer_architecture_boundaries.md` (shared-core placement rules).

## Why

Annotation and callout placement is already showing up in renderer-specific postprocessing. Pulling out the reusable placement logic now reduces duplication and avoids baking SPPM quirks into the general rendering stack.

## Acceptance Criteria

- Shared placement rules exist for nearby annotation or callout elements.
- SPPM-specific postprocessing can adopt the shared logic incrementally.
- The shared logic avoids obvious overlaps with primary flow geometry where feasible.
- Renderers that do not use callouts remain unaffected.

## Notes

This issue is about placement mechanics, not about standardizing every annotation visual style across renderers.

## Progress Update (2026-05-12)

- Extracted shared edge-callout placement helper in `src/flo/render/_callout_layout.py`.
- Updated SPPM rework data-box placement to consume shared helper via `src/flo/render/_sppm_rework_databox.py`.
- Added policy/coverage tests for shared callout helper and boundary consumption.
- Extracted shared callout table/text formatting helpers and adopted them in both continuation labels and SPPM rework data-box rendering.
- Added shared overlap-avoidance heuristic (`resolve_callout_near_source`) so callouts move off the center label slot when an edge already has `xlabel` content.
- Wired overlap heuristic into SPPM rework data-box placement and added regression coverage for return-loop branch labels.
- Adopted shared callout placement/offset behavior in a non-SPPM renderer path (`_graphviz_dot_spaghetti.py`) for verbose entity callouts, proving incremental cross-render reuse.
