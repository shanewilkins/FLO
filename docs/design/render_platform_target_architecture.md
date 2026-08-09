# Render Platform Target Architecture

Status: accepted

## Purpose

Define the target split between diagram semantics, layout, rendering, and true
document composition after the former Graphviz-first design.

This document is explanatory. Diagram meaning remains defined by
`docs/specs/`, and publication governance remains defined by `docs/policy/`.

## Decision Summary

FLO should treat rendering as a layered platform rather than a single backend.

Target stack:

- ELK for algorithmic graph layout and routing where a diagram needs it.
- FLO-owned SVG emission as the canonical standalone graphics path.
- Typst as the document compositor for publication-grade paged output.
- Graphviz is deprecated and no longer participates in the active renderer
  path. Historical compatibility context remains in the migration record only.

## Bright-Line Responsibilities

### FLO diagram semantics

FLO owns:

- diagram-specific meaning
- shape policy
- labels and callouts
- continuation semantics
- queue/rework/SPPM conventions
- spatial semantics for spaghetti maps
- page-aware publication intent

Questions that belong to FLO:

- What is a lane, band, continuation, or subprocess reference?
- Which semantic objects must appear in the diagram?
- Which artifacts are standalone figures versus publication pages?

### Layout engine

ELK owns:

- node placement for graph-like diagrams
- port-aware routing
- orthogonal or layered path planning
- hierarchy-aware layout constraints

Questions that belong to ELK:

- Where should a node go?
- Which polyline or routed path satisfies the declared constraints?

ELK does not own pagination, page furniture, or diagram semantics.

### SVG renderer

The SVG renderer owns:

- conversion of positioned diagram geometry into a standalone vector artifact
- typography and paint policy already decided by FLO semantics
- asset export suitable for reports, notebooks, slides, and documentation

The SVG renderer does not decide layout policy or page breaks.

### Typst compositor

Typst owns:

- page size and margins
- repeated headers and footers
- captions and legends
- multi-page figure placement
- composition of figures with surrounding text or notes

Typst does not own graph layout or FLO diagram semantics.

## Why This Split

This split avoids two failure modes:

1. forcing the layout backend to become a publication system
2. forcing the document compositor to become a graph layout engine

The former Graphviz stack showed both pressures: a layout backend was asked to
do publication-adjacent work, while shared renderer code accumulated
backend-specific routing and SVG repair logic.

## True Composition Versus Large Graphics

FLO should support both output classes explicitly.

### Standalone graphics

Use when the user wants a figure for:

- a report
- a Jupyter notebook
- slides
- README or design documentation

Canonical artifact: standalone SVG.

Optional derived artifacts: PNG and PDF.

### Publication documents

Use when the user wants:

- page-aware headers and footers
- deterministic continuation behavior across pages
- semantic page breaks
- captions, legends, side notes, or appendix-like placement
- stable multi-page PDF output

Canonical artifact: Typst-composed document, usually emitted as PDF.

## Proposed Internal Contracts

The renderer platform should standardize a few backend-neutral contracts.

### 1. Diagram model

Purpose: represent the semantic diagram surface before layout/backend lowering.

Suggested contract:

- `DiagramDocument`
- `DiagramNode`
- `DiagramEdge`
- `DiagramBand`
- `DiagramLabel`
- `DiagramCallout`
- `DiagramStyleToken`

Required properties:

- stable semantic IDs
- diagram type
- element roles
- optional page/publication hints
- optional absolute positions for spatial diagrams
- backend-neutral routing intent

### 2. Layout request and result

Purpose: isolate ELK or any future layout engine behind a stable FLO boundary.

Suggested contract:

- `LayoutRequest`
- `LayoutConstraintSet`
- `LayoutResult`
- `RoutedEdgePath`

Required properties:

- node bounds
- port definitions
- layer or lane grouping hints
- edge routing preferences
- final node positions
- final routed paths

For diagrams with explicit coordinates, such as spaghetti, FLO may bypass ELK
and populate `LayoutResult` directly.

### 3. Graphic asset contract

Purpose: standardize standalone outputs independent of the layout backend.

Suggested contract:

- `GraphicAsset`
- `GraphicAssetManifest`

Required properties:

- asset kind (`svg`, `png`, `pdf`)
- intrinsic size
- source diagram ID and variant
- optional accessibility metadata

### 4. Publication contract

Purpose: standardize what the compositor receives.

Suggested contract:

- `PublicationPlan`
- `PublicationSeries`
- `PublicationPage`
- `PublicationPlacement`
- `PublicationFigureRef`

This extends the existing publication model rather than replacing it.

Required properties:

- page format and margins
- repeated page furniture
- semantic continuation metadata
- placement slots for figures and notes
- references to standalone SVG assets

## Proposed Package Boundaries

The current `flo.render` package should move toward the following target shape.

### `src/flo/render/model/`

Backend-neutral diagram model and shared style tokens.

### `src/flo/render/layout/`

Layout contracts plus engine adapters.

Suggested contents:

- `contracts.py`
- `elk.py`
- `fallback.py`

### `src/flo/render/svg/`

SVG emission from final geometry.

Suggested contents:

- `emit.py`
- `text.py`
- `markers.py`
- `shapes.py`

### `src/flo/publish/`

Publication planning and Typst composition.

Suggested contents:

- `model.py`
- `planner.py`
- `typst_emit.py`
- `assets.py`

## Diagram-Family Guidance

### Swimlane

Primary target:

- Diagram model -> ELK -> FLO SVG

Flowchart uses this path only for 0.1.x compatibility and is removed in 0.2.0
rather than carried forward as a target renderer family.

### Spaghetti map

Primary target:

- Diagram model with explicit spatial coordinates -> FLO SVG

Spaghetti does not depend on ELK when location metadata determines placement.
Missing positions follow the accepted partial-or-strict policy: FLO may omit
incomplete routes with explicit diagnostics, but it never invents geometry or
uses graph layout as a spatial fallback.

### SPPM

Primary target:

- Diagram model -> ELK -> FLO SVG fragments -> Typst
  publication composition

SPPM should be treated as publication-first output, not merely as a large graph
that happens to be split into pages.

### Value stream map

Primary target for the planned 0.3 renderer:

- Canonical and analysis-backed diagram model -> ELK -> FLO SVG

Information flow and material flow remain distinct semantic surfaces. Partial
data produces explicit diagnostics; the renderer must not infer that an absent
surface exists.

## Non-Goals

This target architecture does not require:

- a browser runtime
- a commercial diagram engine
- LaTeX or TikZ as the primary diagram backend
- reconstruction of a Graphviz compatibility backend

## References

- `docs/design/artifact_taxonomy.md`
- `docs/design/publication_model.md`
- `docs/design/renderers/boundaries.md`
- `docs/design/renderers/spaghetti.md`
- `docs/design/adr/render_stack_elk_svg_typst.md`
- `docs/design/render_platform_migration_plan.md`
