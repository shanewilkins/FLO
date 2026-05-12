---
id: '54300661'
title: Simplify SPPM renderer execution shape and module seams
headline: Assess and reduce SPPM renderer complexity by clarifying stage boundaries
  and extracting reusable se
priority: medium
status: todo
archived: false
issue_type: other
milestone: renderer-platform-completeness
labels:
- architecture,sppm,refactor
remote_ids: {}
created: '2026-05-11T17:23:11.883040+00:00'
updated: '2026-05-11T17:27:09.475967+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 5fbc5f50
- f620fe69
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

Assess and reduce SPPM renderer complexity by clarifying stage boundaries and extracting reusable seams without changing semantics.\n\nScope\n- Separate semantic planning, DOT emission, and SVG postprocess responsibilities.\n- Remove duplicate geometry/text policy logic where possible.\n- Improve module-level contracts for easier testing and maintenance.\n\nAcceptance Criteria\n- Complexity and file-length gates remain green with margin.\n- Existing semantic/regression tests pass unchanged.\n- Architecture note maps the final stage/seam boundaries.\n- Refactor does not alter rendering semantics for reference artifacts.\n\n## Baseline Snapshot\n\nBaseline report script:\n\n- scripts/report_sppm_refactor_baseline.py\n- reusable implementation: src/flo/core/_sppm_refactor_baseline.py\n\nCurrent measurements captured on 2026-05-12:\n\n| File | Lines | Max line | >100 chars | Functions | Longest function | Complexity |\n| --- | ---: | ---: | ---: | ---: | --- | --- |\n| src/flo/render/_sppm_graph_builder.py | 141 | 140 | 3 | 3 | build_sppm_graph:78 | build_sppm_graph(9), _sppm_graph_spacing(6), _resolve_rankdir(4) |\n| src/flo/render/_sppm_node_render.py | 216 | 128 | 10 | 9 | render_sppm_node:39 | render_sppm_node(12), _render_sppm_task_node(6), _render_sppm_queue_triangle(4) |\n| src/flo/render/_sppm_routing.py | 556 | 117 | 6 | 11 | _build_non_rework_route:93 | _build_non_rework_route(9), _build_rework_first_segment_attrs(9), _build_boundary_corridor_route(7) |\n| src/flo/render/_sppm_publication.py | 307 | 129 | 9 | 14 | build_sppm_publication_plan:82 | _build_sppm_header_rows(12), _build_sppm_child_slots(11), build_sppm_publication_plan(7) |\n| src/flo/render/_sppm_band_render.py | 132 | 128 | 12 | 10 | build_sppm_header:25 | _edge_source_ids(6), _footer_end_nodes(5), _footer_terminal_nodes(5) |\n| src/flo/render/_sppm_edge_render.py | 248 | 116 | 7 | 9 | _render_sppm_secondary_line_constraints:66 | _accumulate_rework_edge(12), _render_sppm_secondary_line_constraints(10), _render_sppm_edge(9) |\n\n## Layer Violations\n\n- None detected.\n\n## DRY Violations\n\n- No normalized cross-file clone groups detected in the tracked SPPM modules.\n\nBoundary Reference\n- See docs/design/renderer_architecture_boundaries.md for shared-core vs SPPM-only module placement rules.
