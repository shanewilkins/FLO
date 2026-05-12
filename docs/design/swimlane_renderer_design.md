# Swimlane Renderer Design

## Why This Exists

Swimlane diagrams organize process steps into horizontal or vertical lanes,
typically representing roles, departments, or systems involved in the process.
This specification clarifies visual conventions and behavioral expectations so
swimlane rendering remains maintainable and consistent as features evolve.

## Visual Conventions

### Lane Organization

Swimlanes group nodes by the `lane` field in the process model:

- Each lane becomes a cluster subgraph in Graphviz.
- Lanes are ordered by first occurrence in the node list.
- Unlaned nodes appear outside any cluster (in the base graph).
- Cross-lane edges are marked as unconstrained so they may route flexibly.

### Node Rendering

Nodes display with their node kind as the DOT shape:

- `start` → diamond (or ellipse)
- `task` → rectangle
- `system_task` → rectangle (same visual as task)
- `queue` → rectangle with queue icon/label
- `decision` → diamond
- `end` → ellipse

Subprocess nodes that are collapsed (`parent_only` view) show a composite label
indicating detail-map availability.

### Edge Routing

Swimlane uses shared edge routing from `_graphviz_dot_edge_routing.py`:

- Normal edges route as straight lines or splines (Graphviz-determined).
- Boundary edges (across layout wrapping) use corridor markers.
- Rework edges (backward flow) use dashed styling and corridor routing.
- Cross-lane edges are unconstrained to allow flexible routing.

### Subprocess Projection

When `subprocess_view` is set to `parent_only`, subprocess nodes remain visible
as composite nodes, but their child nodes are collapsed and replaced by
collapsed-parent references.

## Layout Behavior

- Default rankdir: `TB` (top-to-bottom, swimlanes vertical)
- With `--orientation lr`: `LR` (left-to-right, swimlanes horizontal)
- Wrapping: supported via `layout_wrap` options (chunked planner)
- When wrapping is active, splines use orthogonal routing for deterministic boundary behavior

## Renderer Boundary Model

Swimlane rendering follows the shared renderer architecture:

1. **Input normalization**
   Extract nodes, edges, and lane assignments from canonical IR or dict input.

2. **Graph assembly**
   Build lane cluster hierarchy, apply subprocess projection, coordinate
   edge routing and layout planning.

3. **Node and edge presentation**
   Render lane clusters, nodes with kind-based shapes, edges with routing
   directives (normal, boundary corridor, rework).

4. **Lane boundary annotations**
   Render vertical/horizontal lane boundary markers and labels.

## Current Module Layout

- `src/flo/render/_graphviz_dot_swimlane.py`
  Swimlane entrypoint, lane grouping, and cluster rendering.
- `src/flo/render/_graphviz_dot_common.py`
  Shared helpers: node/edge extraction, subprocess projection, cluster assembly.
- `src/flo/render/_graphviz_dot_edge_routing.py`
  Shared edge routing (normal, boundary corridor, rework) used by swimlane
  and flowchart.

## Edge Cases and Policies

### Missing Lane Metadata

If a node lacks a lane assignment:
- The node is rendered outside any cluster.
- It remains reachable and renderable.
- A future enhancement may assign it to a default lane or issue a diagnostic.

### Cross-Lane Edges Without Wrapping

Edges that cross lanes are marked `constraint=false` so they can route
flexibly without distorting lane cluster geometry.

### Subprocess Nesting in Swimlanes

Subprocess nodes show their composite label and are clustered with their
parent lane. Child nodes are hidden when `parent_only` is active.

## Guidance for Swimlane Extensions

Future swimlane work should:

- Keep lane cluster assignment separate from lane-agnostic shared routing.
- Use shared edge routing for boundary/rework handling.
- Reuse shared subprocess projection logic.
- Avoid introducing swimlane-specific edge attributes into shared modules.
