---
id: 51f87878
title: Deterministic decision outcome label placement (yes/no/etc.)
headline: Define and enforce deterministic placement rules for decision edge outcome
  labels (yes/no/etc.).\n\n
priority: high
status: closed
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,layout,labels
remote_ids: {}
created: '2026-05-11T17:22:33.116202+00:00'
updated: '2026-05-12T20:02:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 114c6965
blocks: []
actual_start_date: '2026-05-12T13:43:25.906485+00:00'
actual_end_date: '2026-05-12T20:02:00+00:00'
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits:
- df4721d
- 7d5f7db
completed_date: '2026-05-12T20:02:00+00:00'
comments:
- Implemented deterministic outcome-label placement via SVG postprocess contract wiring and a dedicated decision-label postprocess module.
- Added regression coverage for east/south/west/north decision exits, repeated-render stability, and guardrails preventing non-decision label movement.
github_issue: null
---

Define and enforce deterministic placement rules for decision edge outcome labels (yes/no/etc.).\n\nScope\n- Establish placement rules by side/port/direction with fixed offsets.\n- Implement deterministic tie-break logic to prevent drift across runs.\n- Keep labels clear of decision glyphs and key edge paths.\n\nAcceptance Criteria\n- Outcome labels render at deterministic positions for equivalent input.\n- No random drift between repeated builds.\n- Regression tests cover representative decision geometries (LR/TB where applicable).\n- Implementation uses shared callout/annotation mechanics where feasible (dependency).

Implementation Notes

- Routing contract now carries decision outcome label edges and expected label text for deterministic SVG postprocessing.
- SVG postprocessing rewrites only decision outcome labels and applies stable side-aware offsets with tie-break ordering.
- Integration and unit regression tests cover deterministic repeated renders and representative directional geometries.
