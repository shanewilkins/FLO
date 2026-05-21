# Renderer Architecture Boundaries

Status: accepted (v0.1 renderer-platform-completeness)

## Purpose

Define where renderer features must live so SPPM can evolve without coupling
future renderer work to SPPM-only semantics.

## Boundary Map

### Shared renderer core (renderer-agnostic)

- `src/flo/render/_continuation_labels.py`
  Shared continuation label formatting and boundary-edge label generation.
- `src/flo/render/_graphviz_dot_edge_routing.py`
  Shared edge-routing primitives for boundary/rework corridors used by
  flowchart and swimlane renderers.
- `src/flo/render/_publication.py`
  Renderer-independent publication contracts and page/band model.
- `src/flo/render/layout_core/`
  Shared layout primitives for placement and routing plans.

Rule: shared modules must not import SPPM-specific modules.

### SPPM-specific renderer modules

- `src/flo/render/_graphviz_dot_sppm.py`
- `src/flo/render/_sppm_graph_builder.py`
- `src/flo/render/_sppm_*.py`

Examples of SPPM-only semantics:

- queue triangle semantics and queue-specific visual policy
- SPPM rework conventions and anchor token derivation
- SPPM publication conventions (step numbering, SPPM-specific footer content)

### Swimlane-specific responsibilities

- `src/flo/render/_graphviz_dot_swimlane.py`
  Swimlane cluster/lane presentation and swimlane-specific layout behavior.

Swimlane should consume shared routing/label/publication primitives where
possible and own only swimlane-only visual semantics.

## Feature Placement Rules

Use this decision order for new renderer work:

1. If behavior is valid for more than one renderer, implement in shared core.
2. If behavior is specific to SPPM semantics, implement in `_sppm_*` modules.
3. If behavior is specific to swimlane visual semantics, implement in
   `_graphviz_dot_swimlane.py` (or a swimlane-only helper).
4. If uncertain, prefer shared contracts and thin renderer adapters over
   copy/paste.

## Existing Shared Component Consumed Across Paths

`_continuation_labels.py` is consumed by:

- `src/flo/render/_graphviz_dot_edge_routing.py` (flowchart/swimlane path)
- `src/flo/render/_sppm_continuation_labels.py` (SPPM path)

This is the reference implementation of cross-render reuse for continuation
label policy.

## Migration Notes

- Keep extracting renderer-agnostic placement/label policy into shared modules.
- Keep renderer entrypoints thin and orchestration-focused.
- Add or update policy tests whenever a new shared module is introduced.

## References

- `docs/design/sppm_renderer_design.md`
- `docs/design/adr_render_stack_elk_svg_typst.md`
- `docs/design/render_platform_target_architecture.md`
- `.roadmap/issues/renderer-platform-completeness/d4183d06-renderer-architecture-boundary-shared-core-vs-sppm-specific-vs-swimlane-specific.md`