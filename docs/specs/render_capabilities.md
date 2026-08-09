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

- swimlane: svg supported
- spaghetti: svg supported
- sppm: svg supported

Swimlane, spaghetti, and SPPM are the maintained renderer families.

The 0.3 matrix adds:

- value_stream: svg supported

The value-stream entry becomes maintained when the implementation, capability
declaration, tests, deterministic fixtures, and user documentation land
together. Planning text does not make the pair available in the current
runtime.

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
