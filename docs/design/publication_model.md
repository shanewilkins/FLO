# Publication Model

The shared publication model sits above canonical IR and below renderer-specific output such as DOT, SVG, or later PDF views.

The initial contract is intentionally small:

- `PublicationPlan` represents one publication set.
- `PublicationSeries` represents a top-level map or future child/artifact series.
- `PublicationPage` represents one page within a series.
- `PublicationCanvas` represents page bounds, outer margins, the usable canvas, and named content regions.
- `PublicationArtifactSlot` reserves future child-map or artifact outputs without forcing hierarchy behavior into this issue.

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