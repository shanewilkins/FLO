# ADR: Render Geometry And Overflow

Status: accepted

## Context

FLO emits direct SVG diagrams and will add composed multi-page SPPM
publications.
Users need physical and pixel sizing for report, slide, print, and embedded
uses without silent clipping or unrequested changes to diagram readability.

Existing wrapping and page-format options do not distinguish an exact canvas,
an expanded standalone graphic, a scaled diagram, and a paginated publication.

## Decision

Geometry resolves through one renderer-neutral contract with positive `px`,
`in`, `cm`, and `mm` dimensions normalized at 96 px per inch using deterministic
half-up rounding.

- A request with both width and height declares an exact canvas.
- A request with one dimension derives the other from the natural artifact
  aspect ratio.
- A named publication page format supplies exact page bounds and margins.
- A natural render with no requested dimensions keeps renderer-owned bounds.

If a natural diagram does not fit exact requested bounds, the default overflow
policy is `error`.
FLO emits no artifact and reports the natural and requested geometry.
It never silently clips, scales, or paginates process content.

Users select an alternative behavior explicitly:

- `expand` is supported for standalone SVG only and enlarges the final canvas
  to contain the natural diagram at its original scale.
- `scale` fits supported standalone SVG output within the requested bounds and
  reports the applied scale.
  A strict readability policy rejects a scale below the renderer's documented
  minimum text and line thresholds.
- `paginate` is supported only by composed publication outputs, initially SPPM
  via Typst.
  It preserves publication scale and creates a page series with stable step
  references and continuation anchors.

All resolved geometry, selected policy, derived dimensions, and applied scale
are inspectable in the artifact or publication provenance.

## Consequences

Exact dimensions are reliable for automation and publication because overflow
is an actionable failure by default.
Standalone SVG consumers may deliberately choose `expand` when natural-size
readability matters more than a fixed canvas.
Scaling and pagination remain visible author choices rather than renderer
heuristics.

The implementation must retain current wrapping controls as layout inputs, not
reinterpret them as overflow policy.

## Alternatives Rejected

### Silent scale-to-fit

Rejected because it can make labels and semantic marks unreadable without a
visible user choice.

### Silent pagination

Rejected because page boundaries, continuation context, and reading order are
part of publication meaning.

### Visible SVG overflow outside an unchanged canvas

Rejected because embedding hosts may clip it and because it violates an exact
canvas request.