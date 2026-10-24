# FLO Render Capabilities

Purpose: define the normative projection capability contract for supported
diagram render surfaces.

## Scope

This specification defines which diagram surfaces are supported by each render
backend and how unsupported combinations must be handled.

Core language semantics are out of scope; this spec only covers projection
capability.

## Capability Matrix

Current support matrix:

| Diagram | Backend | Current tier | Release acceptance boundary |
| --- | --- | --- | --- |
| swimlane | svg | maintained | Yellow Belt 0.5 |
| spaghetti | svg | maintained | Yellow Belt 0.5 |
| sppm | svg | stable for single-page White Belt; maintained beyond that scope | White Belt 0.4 |
| value_stream | svg | maintained | Green Belt 0.6 |

Swimlane, spaghetti, SPPM, and value stream are the maintained renderer
families.

## Runtime Contract

When a user requests a diagram and backend pair:

1. If the pair is supported, rendering may proceed.
2. If the pair is unsupported, FLO must fail early with a usage-level CLI error.
3. FLO must not silently downgrade or switch backends for unsupported requests.
4. The only supported render backend is `svg`.

## Authority

Machine-readable runtime matrix is implemented in:

- src/flo/render/capability_matrix.py

This document is the normative human-readable specification that mirrors the
runtime matrix.

## Diagnostics Contract

Unsupported projection requests must emit actionable messages that include:

- requested diagram
- requested backend
- supported backends for that diagram

This keeps CLI behavior scriptable and understandable for both local use and CI.

## Single-page SPPM compatibility and promotion

The White Belt acceptance surface covers canonical process projection, LR/TB
orientation, decision and queue shapes, work cards, explicit rework and handoffs,
subprocess projection, parallel structure, timing labels, built-in themes, and
single-page SVG geometry. Dedicated generic-branch geometry, multi-page
publication, and child-map publication acceptance remain outside this promotion.

- Identical canonical input, resolved options, renderer/ELK versions, and supported
  platform must yield identical SVG bytes. Equivalent physical size requests
  resolve consistently at 96 CSS pixels per inch.
- Explicit width/height requests use px, in, cm, or mm. Default safe fitting
  preserves aspect ratio and fails below the 0.75 fit scale; authors can explicitly
  choose expansion or unrestricted scaling. Unrestricted scaling is not a
  legibility guarantee.
- A patch may improve layout and typography with reviewed golden changes. Exact
  coordinates and font-dependent glyph bounds are not cross-version compatibility
  promises; process identities, edges, labels, and measured timing meanings must
  remain intact.
- Built-in themes retain non-color cues: distinct queue/decision shapes, labeled
  branches, dotted correction connectors, and visible VA/RNVA/NVA class text when
  a work card declares that class. The monochrome SPPM surface uses neutral grays.
- Semantic validation, final-SVG geometry, deterministic artifacts, theme contrast,
  physical sizing, installed-package, and SVG-consumer checks are acceptance
  gates. Passing goldens alone does not promote a renderer.

Single-page promotion is supported by the
[candidate acceptance record](../design/white_belt_candidate_acceptance.md),
including clean Linux/macOS installed-wheel and browser glyph measurements.
Broader publication surfaces retain their existing maintained status.
