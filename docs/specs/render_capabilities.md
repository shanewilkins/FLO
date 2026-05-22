# FLO Render Capabilities

Purpose: define the normative projection capability contract for diagram and
render-backend combinations.

## Scope

This specification defines which diagram surfaces are supported by each render
backend and how unsupported combinations must be handled.

Core language semantics are out of scope; this spec only covers projection
capability.

## Capability Matrix

Current support matrix:

- flowchart: graphviz supported, svg supported
- swimlane: graphviz supported, svg unsupported
- spaghetti: graphviz supported, svg supported
- sppm: graphviz supported, svg supported

## Runtime Contract

When a user requests a diagram and backend pair:

1. If the pair is supported, rendering may proceed.
2. If the pair is unsupported, FLO must fail early with a usage-level CLI error.
3. FLO must not silently downgrade or switch backends for unsupported requests.

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
