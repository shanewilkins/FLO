# Value Stream Renderer Design

Status: accepted

## Purpose

Describe the implementation boundary of the maintained value-stream-map
renderer. Normative diagram behavior lives in
`docs/specs/value_stream_map.md`.

## Ownership

`src/flo/render/value_stream/renderer.py` owns the value-stream projection and
direct-SVG artifact emission. It consumes canonical process IR plus the typed
value-stream analysis projection; it does not dispatch through, inherit from,
or import another renderer.

Material and information flows remain distinct renderer semantics. Missing
optional data is represented honestly and never replaced with invented flow,
timing, or geometry.

The package may consume renderer-neutral artifact, option, theme, and SVG
mechanics. Behavior becomes shared infrastructure only after its contract is
independent of value-stream-map meaning and useful to another renderer.

## Enforcement

The executable renderer registry is the single dispatch and capability source.
Import contracts forbid value stream from importing SPPM, swimlane, or
spaghetti, and artifact tests cover deterministic full and partial-data output.
