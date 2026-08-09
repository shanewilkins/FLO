# Flowchart Renderer Compatibility Note

Status: historical

## Purpose

Record the final compatibility posture for the deprecated flowchart renderer.
This file is historical implementation context, not a foundation for future
renderer work.

Normative 0.1.x behavior remains in `docs/specs/flowchart.md` until the renderer
is removed in 0.2.0.

## Final implementation posture

The compatibility renderer uses the same FLO-owned direct-SVG and ELK
request/result seams as maintained graph families. It exists only to preserve
0.1.x behavior and emit migration guidance.

No new flowchart-specific layout, styling, publication, or configuration work
should be added.

## Removal contract

The 0.2.0 change removes:

- the flowchart capability-matrix entry
- the flowchart CLI diagram choice
- the compatibility renderer and its dedicated tests
- active user documentation that presents flowchart as a supported choice

Release notes must point users to:

- swimlane for responsibility-oriented process maps
- SPPM for rich operational and Lean process maps

Historical changelog and migration references may remain when clearly labeled
as historical.

## References

- `docs/specs/flowchart.md`
- `docs/ROADMAP.md`
- `docs/design/adr/render_stack_elk_svg_typst.md`
