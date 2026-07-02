# Renderer Architecture Boundaries

Status: accepted

## Purpose

Define where renderer features must live so SPPM can evolve without coupling
future renderer work to SPPM-only semantics.

## Boundary Map

### Backend-neutral renderer core

- `src/flo/render/_publication.py`
  Renderer-independent publication contracts and page/band model.

Rule: backend-neutral modules must not import SVG or SPPM renderer modules.

### SPPM-specific renderer modules

- `src/flo/render/_svg_sppm.py`
- `src/flo/render/_sppm_*.py`

Examples of SPPM-only semantics:

- queue triangle semantics and queue-specific visual policy
- SPPM rework conventions and anchor token derivation
- SPPM publication conventions (step numbering, SPPM-specific footer content)

### Swimlane-specific responsibilities

- `src/flo/render/_svg_swimlane.py`
  Swimlane lane presentation and swimlane-specific SVG layout behavior.

Swimlane should consume shared routing/label/publication primitives where
possible and own only swimlane-only visual semantics.

## Feature Placement Rules

Use this decision order for new renderer work:

1. If behavior is backend-neutral and valid for more than one renderer,
  implement in backend-neutral shared core.
2. If behavior is specific to SPPM semantics, implement in `_sppm_*` modules.
3. If behavior is specific to swimlane visual semantics, implement in
  `_svg_swimlane.py` (or a swimlane-only helper).
4. If uncertain, prefer shared contracts and thin renderer adapters over
   copy/paste.

## Migration Notes

- Keep extracting renderer-agnostic placement/label policy into shared modules.
- Keep renderer entrypoints thin and orchestration-focused.
- Do not reintroduce Graphviz or DOT renderer modules.
- Add or update policy tests whenever a new shared module is introduced.

## References

- `docs/design/renderers/sppm.md`
- `docs/design/adr/render_stack_elk_svg_typst.md`
- `docs/design/render_platform_target_architecture.md`
- `.roadmap/issues/renderer-platform-completeness/d4183d06-renderer-architecture-boundary-shared-core-vs-sppm-specific-vs-swimlane-specific.md`