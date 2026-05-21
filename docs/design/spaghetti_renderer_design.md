# Spaghetti Renderer Design

Status: accepted renderer design note

## Why This Exists

Spaghetti diagrams visualize material and people movement paths through a process,
useful for lean manufacturing analysis and facility layout optimization. This
specification clarifies how FLO infers and renders movement flows so the diagram
remains a reliable analysis tool.

## Visual Conventions

### Spatial Layout

Spaghetti diagrams use position-based layout (neato):

- Nodes represent locations (inferred from node lane assignments).
- Location positions are derived from explicit spatial metadata in the process model.
- Edges represent movement flows (material, people, or both).
- Flow lines are routed with spline interpolation over explicit node positions.

### Channel Selection

Users may choose which movement types to visualize via `--spaghetti-channel`:

- `material` — shows material movement paths only.
- `people` — shows people/worker movement paths only.
- `both` — shows both material and people flows (default).

### People Movement Aggregation

When visualizing people movements, users control aggregation via `--spaghetti-people-mode`:

- `aggregate` — combines all worker movements by location pair (default).
- `worker` — breaks down flows by individual worker role (when available).

### Location Nodes

Location nodes are styled as filled circles with labels showing location names.
Flow edges are labeled with edge counts or movement frequency when available.

## Renderer Boundary Model

Spaghetti rendering follows a distinct pattern from swimlane/flowchart:

1. **Movement inference**
   Extract implicit material and people movement paths from the process IR
   using analysis helpers (`infer_material_movements`, `infer_people_movements`).

2. **Movement aggregation**
   Combine individual movements into location-pair routes, optionally grouped
   by worker.

3. **Location and boundary extraction**
   Extract explicit spatial/location metadata from the process model to
   position nodes and render facility boundaries (if present).

4. **Graph assembly and rendering**
   Assemble location nodes and movement edges, apply spatial layout directives,
   and render boundary overlays (rectangles, polygons from metadata).

## Current Module Layout

- `src/flo/render/_graphviz_dot_spaghetti.py`
  Spaghetti entrypoint, movement aggregation, and spatial graph assembly.
- `flo.compiler.analysis`
  Movement inference and aggregation (reusable for other tools).

## Edge Cases and Policies

### Missing Spatial Metadata

If a location lacks explicit spatial coordinates:
- The node is still rendered but position is inferred by Graphviz layout.
- Boundary overlays that require spatial metadata are skipped gracefully.
- A diagnostic may warn users about missing spatial data for optimal visualization.

### No Movements Inferred

If a process has no material or people movements (e.g., purely administrative):
- The diagram renders with location nodes but no edges.
- It indicates that movement analysis is not applicable to the process.
- Users can still export the location topology.

### Boundary Overlays

Facility boundaries are optional metadata (`layout_boundary` or `boundary` fields):
- Rectangle boundaries define min/max coordinates.
- Polygon boundaries define explicit point sequences.
- Boundaries are rendered as subgraph cluster boxes or polygon shapes.

### Worker Identity in People Movement

Worker-level aggregation requires staffing metadata (`staff_role` or similar).
When metadata is absent:
- People movements fall back to location-pair aggregation.
- A diagnostic notes missing staffing data for granular analysis.

## Analysis vs. Rendering Separation

Movement inference and aggregation are part of the analysis layer (not the
renderer). This allows:

- Reuse of movement analysis for other tools (reports, metrics, simulations).
- Decoupling of spatial visualization from movement computation.
- Future support for different spatial backends (not just Graphviz).

## Guidance for Spaghetti Extensions

Future spaghetti work should:

- Keep movement inference in the analysis layer.
- Keep spatial metadata extraction and boundary rendering separate.
- Use Graphviz's neato layout for position-driven diagrams.
- Avoid baking spatial semantics into shared renderer modules.
- Support future backends (e.g., SVG, D3) by separating analysis from rendering.
