# SPPM Renderer Design

Status: accepted

## Purpose

Define the current decomposition of FLO's ELK-backed, FLO-owned direct-SVG
SPPM renderer. Normative SPPM meaning lives in `docs/specs/sppm.md`.

## Architecture validation and effective clarification

The [validation report](../architecture_validation.md) closes AF-001–003 through
R1–R3b. One production sequence produces engine, routed, and final-scene values;
SVG consumes the final scene. Clean candidate acceptance remains R4 work. The
[finalization ADR](../adr/render_layout_finalization.md) records the accepted split.

## Renderer boundary model

SPPM is split into four concerns.

1. Semantic normalization and projection
   - Normalize canonical IR, subprocess projection, rework semantics, themes,
     labels, and publication intent.
2. Layout request and result
   - Build SPPM-specific ELK constraints and normalize ELK output into the
     backend-neutral layout contract.
3. SVG presentation
   - Render nodes, ports, orthogonal edges, labels, callouts, lanes, and
     annotations from final geometry.
4. Publication planning
   - Build page, band, continuation, and future child-map context without
     turning the SVG emitter into a document compositor.

Graphviz and DOT are not part of the active SPPM renderer path and must not be
reintroduced as layout or publication fallbacks.

## Current module layout

- `src/flo/render/sppm/renderer.py`
  Production orchestration, explicit precomputed-engine adapter, and stage observation.
- `src/flo/render/sppm/layout.py`
  SPPM-owned ELK request construction, node measurement, continuation-token
  decoration, rework callouts, wrapping, and layout adapter.
- `src/flo/render/layout_core/`
  ELK contracts, execution, normalized layout results, ports, corridors,
  routing, and geometry strategies.
- `src/flo/render/sppm/nodes.py`
  SPPM node presentation.
- `src/flo/render/sppm/scene.py`, `geometry.py`, `edge_geometry.py`,
  `edge_layout.py`, and `attachments.py`
  Finalize node/routes, shape attachments, labels/callouts/tokens, occupied bounds,
  publication bands, and diagnostic outcomes before emission.
- `src/flo/render/sppm/svg.py` and `edge_svg.py`
  Serialize final scene and connector/annotation geometry with supplied paint.
- `src/flo/render/sppm/edges.py`
  Explicit intermediate route/token compatibility adapters for stage-level tests;
  the production emitter cannot depend on them.
- `src/flo/render/sppm/rows.py`
  Mainline and rework-row display alignment and diagnostics.
- `src/flo/render/sppm/projection.py`
  Top-level, child-map, and inline projection behavior.
- `src/flo/render/sppm/publication.py` and
  `src/flo/render/sppm/publication_support.py`
  SPPM publication-plan integration.
- `src/flo/render/sppm/content.py` and `src/flo/render/sppm/text.py`
  SPPM content and text policy. Shared resolved themes remain outside the
  renderer package; the legacy SPPM theme model is compatibility input only.

## Ownership rules

- ELK supplies algorithmic graph placement and routed geometry.
- SPPM-owned layout policy and finalization own the normative row, boundary,
  attachment, and annotation constraints described by `docs/specs/sppm.md`.
- SVG emission consumes finalized geometry and applies paint, typography, and
  coordinate serialization. Formatting and supplied viewport transforms are
  permitted; moving nodes, rebuilding routes, and choosing annotation positions
  are competing layout policy and belong before emission.
- Publication planning owns page context; the Typst compositor owns multi-page
  document composition. Full publication acceptance remains a later belt gate.

## Footer metric policy

Structural metrics such as step and edge counts may be derived in FLO.
Process-performance metrics such as cycle time, wait time, changeover time,
rework rate, and externally calculated KPIs must come from model metadata or an
analysis layer.

The renderer must not invent absent metrics. A richer KPI surface belongs in a
separate report rather than an ever-growing footer.

## Decision and queue visual policy

- Decision diamonds use a dedicated high-contrast theme role.
- Outcome labels remain neutral enough not to compete with nodes.
- Queue triangles use the warning role and keep queue name and wait time
  legible.
- VA, RNVA, and NVA map to the shared success, warning, and danger roles.
- Print themes preserve semantic distinction with print-safe contrast.

## Extension rules

- Keep the public entrypoint thin.
- Add shared behavior to backend-neutral contracts or SVG primitives.
- Keep SPPM-only semantics inside `src/flo/render/sppm/`.
- Preserve deterministic layout diagnostics and golden-artifact gates.
- Route multi-page publication work toward the shared publication model and
  Typst composition, not SVG-page emulation.
