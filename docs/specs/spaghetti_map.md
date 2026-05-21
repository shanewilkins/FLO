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
2. Spatial or location metadata for positioning locations when available.

If spatial metadata is incomplete, FLO may still render a usable map, but the
diagram becomes less exact as a layout artifact.

## Normative characteristics

A spaghetti map in FLO must satisfy the following characteristics:

1. Movement-oriented representation
   - The diagram represents inferred movement between locations, not the full
     control-flow graph.

2. Channel-aware rendering
   - FLO must support movement views for material, people, or both.

3. Location-based topology
   - Nodes represent locations or movement-relevant places, not arbitrary FLO
     step shapes.

4. Analysis/rendering separation
   - Movement inference belongs to analysis semantics; the renderer visualizes
     that inferred movement surface.

5. Graceful degradation
   - Missing spatial metadata or absent worker-specific metadata should degrade
     the output predictably rather than invalidate the entire render.

## Non-goals

A spaghetti map is not:

- a publication-first work instruction document
- a canonical serialization of process structure
- a simulation of travel time by itself
- a substitute for facility CAD or detailed layout engineering

## Relationship to other documents

- Diagram meaning is defined here.
- Renderer structure and implementation boundaries belong in
  `docs/design/spaghetti_renderer_design.md`.
- Movement analysis behavior belongs in the analysis implementation and any
  future movement-analysis spec.
- Core process semantics belong in `docs/specs/core_language.md`.
