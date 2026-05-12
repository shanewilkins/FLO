---
id: '54300661'
title: Simplify SPPM renderer execution shape and module seams
headline: Assess and reduce SPPM renderer complexity by clarifying stage boundaries and extracting reusable seams
priority: medium
status: done
archived: false
issue_type: other
milestone: renderer-platform-completeness
labels:
- architecture,sppm,refactor
remote_ids: {}
created: '2026-05-11T17:23:11.883040+00:00'
updated: '2026-05-12T20:36:06+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 5fbc5f50
- f620fe69
blocks: []
actual_start_date: null
actual_end_date: '2026-05-12T20:36:06+00:00'
progress_percentage: 100
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches:
- master
git_commits:
- 0f7af79
- 83f28c8
- b0b3aa9
- 5e8ff0b
- b60db88
completed_date: '2026-05-12T20:36:06+00:00'
comments: []
github_issue: null
---

Assess and reduce SPPM renderer complexity by clarifying stage boundaries and extracting reusable seams without changing semantics.

Scope
- Separate semantic planning, DOT emission, and SVG postprocess responsibilities.
- Remove duplicate geometry/text policy logic where possible.
- Improve module-level contracts for easier testing and maintenance.

Acceptance Criteria
- Complexity and file-length gates remain green with margin.
- Existing semantic/regression tests pass unchanged.
- Architecture note maps the final stage/seam boundaries.
- Refactor does not alter rendering semantics for reference artifacts.

## Baseline Snapshot

Baseline report script:

- scripts/report_sppm_refactor_baseline.py
- reusable implementation: src/flo/core/_sppm_refactor_baseline.py

Current measurements captured on 2026-05-12:

| File | Lines | Max line | >100 chars | Functions | Longest function | Complexity |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| src/flo/render/_sppm_graph_builder.py | 141 | 140 | 3 | 3 | build_sppm_graph:78 | build_sppm_graph(9), _sppm_graph_spacing(6), _resolve_rankdir(4) |
| src/flo/render/_sppm_node_render.py | 216 | 128 | 10 | 9 | render_sppm_node:39 | render_sppm_node(12), _render_sppm_task_node(6), _render_sppm_queue_triangle(4) |
| src/flo/render/_sppm_routing.py | 556 | 117 | 6 | 11 | _build_non_rework_route:93 | _build_non_rework_route(9), _build_rework_first_segment_attrs(9), _build_boundary_corridor_route(7) |
| src/flo/render/_sppm_publication.py | 307 | 129 | 9 | 14 | build_sppm_publication_plan:82 | _build_sppm_header_rows(12), _build_sppm_child_slots(11), build_sppm_publication_plan(7) |
| src/flo/render/_sppm_band_render.py | 132 | 128 | 12 | 10 | build_sppm_header:25 | _edge_source_ids(6), _footer_end_nodes(5), _footer_terminal_nodes(5) |
| src/flo/render/_sppm_edge_render.py | 248 | 116 | 7 | 9 | _render_sppm_secondary_line_constraints:66 | _accumulate_rework_edge(12), _render_sppm_secondary_line_constraints(10), _render_sppm_edge(9) |

## Layer Violations

- None detected.

## DRY Violations

- No normalized cross-file clone groups detected in the tracked SPPM modules.

Boundary Reference
- See docs/design/renderer_architecture_boundaries.md for shared-core vs SPPM-only module placement rules.

## Closeout Summary

Final measured state after refactor slices:

| File | Lines | Longest function | Complexity hotspots |
| --- | ---: | --- | --- |
| src/flo/render/_sppm_graph_builder.py | 130 | build_sppm_graph:65 | _sppm_graph_spacing(6), _resolve_rankdir(4), build_sppm_graph(4) |
| src/flo/render/_sppm_node_render.py | 146 | render_sppm_node:39 | render_sppm_node(12), _render_sppm_task_node(6), _resolve_sppm_value_style(4) |
| src/flo/render/_sppm_routing.py | 524 | build_sppm_routing_plan:78 | _build_rework_first_segment_attrs(9), _build_boundary_corridor_route(7), _build_sppm_edge_route(7) |
| src/flo/render/_sppm_publication.py | 110 | build_sppm_publication_plan:82 | build_sppm_publication_plan(7) |
| src/flo/render/_sppm_band_render.py | 132 | build_sppm_header:25 | _edge_source_ids(6), _footer_end_nodes(5), _footer_terminal_nodes(5) |
| src/flo/render/_sppm_edge_render.py | 139 | _render_sppm_edge:28 | _render_sppm_edge(9), _render_sppm_spine_constraints(9), _escape_sppm_route_attrs(4) |

Validation outcome:

- Quality gates green (ruff, pydocstyle, pyright, file length, radon, vulture, import-linter, pytest).
- Layer violations: none detected.
- DRY violations: no normalized cross-file clone groups detected in tracked SPPM modules.
- Rendering semantics preserved under existing regression suites.