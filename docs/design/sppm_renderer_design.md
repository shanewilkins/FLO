# SPPM Renderer Design

## Why This Exists

The original SPPM DOT renderer started as a pragmatic single-file implementation.
That was acceptable while the renderer was still proving out the semantics of SPPM,
but it became a maintenance hotspot once publication bands, wrap planning,
continuation logic, and richer label behavior accumulated.

This note records the intended renderer shape so future work can extend the
system without growing another god module.

## Renderer Boundary Model

An SPPM renderer should be split into four concerns:

1. Input normalization
Normalize canonical IR or dict-like process inputs into a single internal render
shape. This is the only layer that should need to understand both input forms.

2. Graph assembly
Coordinate wrap plans, routing plans, publication plans, theme resolution, and
DOT line assembly. This layer should orchestrate other renderer modules rather
than owning detailed node or band formatting.

3. Node and edge presentation
Convert normalized render data into DOT node and edge fragments. Node rendering,
label construction, and edge rendering should remain separate so diagram
variants can reuse or replace them independently.

4. Publication-backed bands and annotations
Render graph-level or sink-level presentation elements such as headers,
footers, captions, legends, and future page-aware bands. This keeps document
chrome separate from core graph topology.

## Current Module Layout

- `src/flo/render/_graphviz_dot_sppm.py`
  Thin public entrypoint for SPPM DOT rendering.
- `src/flo/render/_sppm_graph_builder.py`
  Graph assembly and orchestration.
- `src/flo/render/_sppm_render_data.py`
  Input normalization and shared render-data helpers.
- `src/flo/render/_sppm_node_render.py`
  Node-level DOT rendering primitives.
- `src/flo/render/_sppm_band_render.py`
  Publication-backed header and footer rendering.
- Existing focused modules such as `_sppm_edge_render.py`, `_sppm_label_html.py`,
  `_sppm_routing.py`, and `_sppm_publication.py`
  Continue to own their current focused concerns.

## Deliberate Non-Goals For This Refactor

- Changing the current normalized dict-shaped render data.
- Redesigning canonical IR around renderer needs.
- Changing public render behavior or SPPM output semantics.

Those remain separate concerns so this refactor can improve legibility without
quietly expanding scope.

## Footer Metric Policy

The footer band is intentionally narrow: it should surface a small set of
canonical process metrics that help a reader understand flow health without
turning the footer into a full analytics dashboard.

Approved footer metrics for SPPM:

| Metric | Intended audience | Computation/source |
| --- | --- | --- |
| Step count | Operators and reviewers | Derived inside FLO from rendered node count on the active page/map. |
| Edge count | Operators and reviewers | Derived inside FLO from rendered edge count on the active page/map. |
| Handoff count | Improvement analysts | Derived inside FLO from edge or step metadata when a handoff marker exists; otherwise omitted. |
| Rework count / rework rate | Improvement analysts | Derived in FLO analysis surfaces from rework-classified edges or telemetry-backed analysis; footer only renders the value when supplied. |
| Cycle time | Improvement analysts | Precomputed in model metadata or provided at render time; renderer does not infer it from geometry. |
| Wait time | Improvement analysts and supervisors | Precomputed in model metadata or provided at render time; renderer only formats the supplied value. |
| Changeover time | Improvement analysts and supervisors | Precomputed in model metadata or provided at render time; renderer only formats the supplied value. |
| Value-class mix summary | Lean coaches and reviewers | Derived from node metadata when value-class tags are present; otherwise omitted. |

Policy rules:

- Structural metrics belong in FLO itself and can be derived at render time.
- Process-performance metrics belong in the model metadata or analysis layer.
- Render-time footer rows remain the escape hatch for externally computed KPIs.
- The footer should not invent metrics that are absent from metadata or analysis inputs.
- If a diagram needs a richer KPI table, that should become a separate report,
  not an ever-growing footer.

This keeps the footer useful for at-a-glance publication output while avoiding
quiet duplication of the broader analytics layer.

## Guidance For Future Renderers

Future renderers should prefer the same shape:

- keep one thin public entrypoint
- isolate input normalization
- keep graph assembly orchestration separate from presentation primitives
- keep document bands and publication chrome separate from graph topology

That gives FLO a renderer architecture that can grow by adding focused modules,
not by enlarging a single entrypoint file.
