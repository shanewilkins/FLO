# Publication Model

The shared publication model sits above canonical IR and below renderer-specific output such as DOT, SVG, or later PDF views.

The initial contract is intentionally small:

- `PublicationPlan` represents one publication set.
- `PublicationSeries` represents a top-level map or future child/artifact series.
- `PublicationPage` represents one page within a series.
- `PublicationCanvas` represents page bounds, outer margins, the usable canvas, and named content regions.
- `PublicationArtifactSlot` reserves future child-map or artifact outputs without forcing hierarchy behavior into this issue.

Named page formats are now part of the shared planner surface.

- Supported built-in presets are `letter`, `a4`, `legal`, and `tabloid`.
- Each preset resolves shared width, height, and default margins.
- Renderers should reference these presets by name rather than hardcoding page geometry.
- To add a new preset, extend the shared registry in `src/flo/render/_publication.py` and document the new canonical name and aliases here.

Publication readability diagnostics are also shared.

- Non-strict publication requests may fall back with an explicit warning diagnostic.
- Strict publication requests must fail instead of silently switching the requested mode.
- SPPM adopts this policy first for projection/readability fallbacks, and later renderers should reuse the same warning-vs-error distinction.

Band content is split into shared context versus renderer semantics.

- Shared `context_rows` carry reusable page-aware metadata such as page number, series identity, parent-map references, child-map references, and continuation references.
- Renderer-specific `rows` and `notes` still carry semantic content such as SPPM metrics, captions, or process metadata.
- Renderers should render `context_rows` when present, but single-page output stays unchanged when no shared page context applies.

Footer metric policy follows the same split:

- Renderer-owned structural metrics such as counts may be derived inside FLO at render time.
- Process-performance metrics such as cycle time, wait time, and changeover time should come from model metadata or an analysis layer, not from the publication planner.
- Render-time rows remain the escape hatch for externally computed KPIs when a caller wants to override or extend the footer.
- The publication model should never guess at metric meaning; it only transports and places the values supplied by the renderer.

## Geometry

Margins are part of page geometry, not content regions.

- Page bounds describe the outer page or canvas.
- Margins carve out a usable canvas inside those bounds.
- Named content regions such as `header`, `body`, and `footer` live inside the usable canvas.

This keeps page geometry separate from semantic content placement.

## SPPM-first adoption

The first live adopter is SPPM.

- SPPM now builds an in-memory publication plan before rendering its header band.
- The current rendered header remains visually stable.
- The plan already exposes child-map slots for subprocess nodes via existing detail-map references.

## Deferred work

This issue does not implement full pagination, footer rendering, or hierarchical child-map output.

Those later slices should build on this model rather than adding new renderer-specific layout structures.