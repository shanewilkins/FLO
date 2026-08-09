# SPPM Renderer Design

Status: accepted

## Purpose

Define the current decomposition of FLO's ELK-backed, FLO-owned direct-SVG
SPPM renderer. Normative SPPM meaning lives in `docs/specs/sppm.md`.

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

- `src/flo/render/_svg_sppm.py`
  Direct-SVG entrypoint and final artifact assembly.
- `src/flo/render/layout_core/`
  ELK contracts, request construction, runtime adapter, normalized layout
  results, ports, corridors, routing, and the locked SPPM strategy.
- `src/flo/render/_svg_sppm_nodes.py`
  SPPM node presentation.
- `src/flo/render/_svg_sppm_edges.py`
  Edge, label, and callout presentation.
- `src/flo/render/_svg_sppm_rows.py`
  Mainline and rework-row display alignment and diagnostics.
- `src/flo/render/_sppm_projection.py`
  Top-level, child-map, and inline projection behavior.
- `src/flo/render/_sppm_publication.py` and
  `src/flo/render/_sppm_publication_support.py`
  SPPM publication-plan integration.
- `src/flo/render/_sppm_node_content.py`, `_sppm_text.py`, and
  `_sppm_themes.py`
  Content, text, and theme policy.

## Ownership rules

- ELK owns requested graph placement and routed geometry.
- SPPM layout normalization owns the normative row and boundary constraints
  described by `docs/specs/sppm.md`.
- SVG modules render supplied geometry and may apply only deterministic
  presentation transforms that do not create competing route policy.
- Publication planning owns page context; a future Typst compositor owns
  multi-page document composition.

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
- Keep SPPM-only semantics in `_sppm_*` and `_svg_sppm*` modules.
- Preserve deterministic layout diagnostics and golden-artifact gates.
- Route multi-page publication work toward the shared publication model and
  Typst composition, not SVG-page emulation.
