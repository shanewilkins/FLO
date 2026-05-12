---
id: e4d655b4
title: SPPM label length policy and truncation matrix
headline: Formalize and implement max-length, wrapping, and truncation policy per SPPM label surface
priority: medium
status: in_progress
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm
- text
- ux
remote_ids: {}
created: '2026-05-11T17:22:35.634128+00:00'
updated: '2026-05-12T00:00:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-12T00:00:00+00:00'
actual_end_date: null
progress_percentage: 85
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

Formalize and implement max-length/wrapping/truncation policy per SPPM label surface.

Scope
- Define limits and wrap/truncation behavior for: task names, decision text, queue badges, edge labels, footer/header text.
- Harmonize policy with existing CLI truncation controls and output profiles.
- Add edge-case fixtures for long labels.

Acceptance Criteria
- Policy table is documented and test-backed.
- Long labels never destabilize layout unexpectedly.
- Behavior is deterministic for each truncation policy mode.
- Showcase includes at least one long-label stress example.

Progress Update (2026-05-12)
- Implemented shared policy application for decision labels, queue/subprocess labels, decision/branch edge labels, and publication header/footer fields using existing SPPM wrap/truncation options.
- Added policy documentation in `docs/User_Manual.md` with surface-to-option mapping.
- Added long-label stress reference fixture: `examples/reference/sppm_long_label_stress.flo`.
- Added deterministic policy tests in:
  - `tests/unit/test_render_sppm.py`
  - `tests/unit/render/test_publication.py`
- Focused validation passed:
  - `uv run pytest tests/unit/test_render_sppm.py tests/unit/render/test_publication.py tests/unit/test_render_sppm_queue_and_rework.py -q`
  - `uv run ruff check src/flo/render/_sppm_node_render.py src/flo/render/_sppm_special_node_shapes.py src/flo/render/_sppm_routing.py src/flo/render/_sppm_publication_support.py tests/unit/test_render_sppm.py tests/unit/render/test_publication.py`
