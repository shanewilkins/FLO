# Spaghetti Map

Purpose: define what a spaghetti map means in FLO and which behavior is part of
its normative contract.

## Intent

A spaghetti map is FLO's movement-visualization diagram.

It shows how materials, people, or both move across physical or logical
locations associated with a process. Its primary use is operational analysis,
layout review, and waste identification rather than step-by-step work
instruction.

## Required inputs

A spaghetti map depends on two layers of information:

1. Canonical FLO process structure for inferring movement paths.
2. Spatial or location metadata for positioning movement-route endpoints.

If spatial metadata is incomplete, FLO follows the deterministic partial or
strict policy below. It never invents coordinates.

## Normative characteristics

A spaghetti map in FLO must satisfy the following characteristics:

1. Movement-oriented representation
   - The diagram represents inferred movement between locations, not the full
     control-flow graph.

2. Channel-aware rendering
   - FLO must support movement views for material, people, or both.
   - These views are derived from canonical `consumes` and `produces`,
     `performed_by`, and location semantics rather than only legacy aliases.

3. Location-based topology
   - Nodes represent locations or movement-relevant places, not arbitrary FLO
     step shapes.

4. Analysis/rendering separation
   - Movement inference belongs to analysis semantics; the renderer visualizes
     that inferred movement surface.

5. Graceful degradation
   - Default mode renders complete positioned routes and identifies omitted
     data explicitly.
   - Strict mode rejects any selected route with an unpositioned endpoint.
   - Absent performer-specific metadata degrades predictably according to the
     selected aggregation mode.

## Current missing-spatial behavior

Current 0.2 direct-SVG behavior applies after channel selection and movement inference.
Every selected route endpoint must have numeric spatial coordinates.
If any selected route has an unpositioned endpoint, FLO fails with a render error and emits no SVG artifact.
FLO does not synthesize coordinates or invoke automatic graph layout.

## 0.3 planned missing-spatial policy

### Default partial mode

- A route is renderable only when both endpoint locations have numeric spatial
  coordinates.
- 0.3 FLO renders all renderable selected routes and omits selected routes with one
  or two unpositioned endpoints.
- An incomplete result emits the stable `spaghetti-missing-spatial` warning to
  `stderr`.
- The warning lists missing location IDs in sorted order and reports omitted
  location and route counts.
- The SVG includes a visible `Partial map` notice with the omitted counts so a
  detached artifact cannot be mistaken for complete spatial evidence.
- If no selected route remains renderable, FLO fails with a render error and
  emits no misleading empty map.

### Strict mode

Strict mode fails before artifact emission if any selected route has an
unpositioned endpoint. Diagnostics use the same stable code and deterministic
location ordering as partial mode.

### Prohibited fallback

The 0.3 implementation must not synthesize coordinates, approximately place
missing locations, or invoke automatic graph layout for a spaghetti map.
Such placement would imply spatial evidence the model does not contain.

## Non-goals

A spaghetti map is not:

- a publication-first work instruction document
- a canonical serialization of process structure
- a simulation of travel time by itself
- a substitute for facility CAD or detailed layout engineering

## Relationship to other documents

- Diagram meaning is defined here.
- Renderer structure and implementation boundaries belong in
  `docs/design/renderers/spaghetti.md`.
- Movement analysis behavior belongs in the analysis implementation and any
  future movement-analysis spec.
- Core process semantics belong in `docs/specs/core_language.md`.
