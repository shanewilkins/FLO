# Swimlane Renderer Design

Status: accepted

## Why This Exists

Swimlane diagrams organize process steps into horizontal or vertical lanes,
typically representing roles, departments, or systems involved in the process.
This specification clarifies visual conventions and behavioral expectations so
swimlane rendering remains maintainable and consistent as features evolve.

Current implementation status:

- Swimlane is a maintained direct-SVG diagram family.
- Layout is built through the FLO-owned ELK request/result seam in
   `src/flo/render/layout_core/`.
- Graphviz-era DOT behavior is retained only as historical context or
   compatibility background where older notes still mention it.

## Visual Conventions

### Lane Organization

Swimlanes group nodes by the `lane` field in the process model:

- Each lane becomes an ELK grouping container and an SVG lane frame.
- Declared lanes keep declaration order when present.
- Lane IDs discovered from node assignments are appended by first node
   occurrence.
- Unlaned nodes are assigned to a synthetic `unassigned` lane so they remain
   visible in the responsibility view.
- Cross-lane edges remain explicit SVG edges between the laid-out nodes.

### Node Rendering

Swimlane is an SPPM projection organized into responsibility lanes.
It inherits SPPM node shapes, typography, themes, standard-detail labels, and
edge and rework conventions.
Queue nodes are theme-colored triangles with a visible queue name and wait time.
Decision nodes retain the shared pale-primary diamond treatment.

Subprocess nodes that are collapsed (`parent_only` view) show a composite label
indicating detail-map availability.

### Edge Routing

Swimlane routes edges through ELK geometry normalized into FLO's
backend-neutral `LayoutResult` contract:

- Normal edges use ELK edge sections rendered by shared SVG edge primitives.
- Edge labels come from outcome or label metadata on the canonical edge.
- Rework and richer process-map affordances should use the same shared SVG edge
   primitives as other maintained diagram families.
- Cross-lane edges are rendered as ordinary process transitions whose endpoints
   happen to sit in different lane frames.

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

2. **ELK request assembly**
   Build ordered lane, node, and edge contracts, apply subprocess projection,
   and validate renderer-visible namespaces.

3. **Layout normalization**
   Execute the ELK adapter and normalize response geometry into lane frames,
   node bounds, and routed edge paths.

4. **SVG presentation**
   Render lane frames, kind-based node shapes, edge paths, and labels with
   shared SVG primitives.

Lane grouping, lane frames, and lane-aware placement are swimlane-specific.
Where those placement constraints conflict with SPPM mainline or rework-row
placement, lane layout takes precedence without changing transition semantics.

## Current Module Layout

- `src/flo/render/_svg_swimlane.py`
   Direct-SVG swimlane artifact entrypoint.
- `src/flo/render/layout_core/elk.py`
   Swimlane ELK request building, request serialization, execution, and result
   normalization.
- `src/flo/render/layout_core/elk_support.py`
   Shared node, edge, lane, and subprocess projection helpers for ELK-backed
   diagram families.
- `src/flo/render/_svg_shared_primitives.py`
   Shared SVG lane, node, edge, marker, and definition primitives.

## Edge Cases and Policies

### Missing Lane Metadata

If a node lacks a lane assignment:

- The node is included in a synthetic `unassigned` lane.
- It remains reachable and renderable.
- A future enhancement may issue a diagnostic when this weakens responsibility
   analysis.

### Cross-Lane Edges Without Wrapping

Edges that cross lanes remain normal process transitions in the request model.

The renderer should keep them visually understandable without allowing lane
grouping to redefine handoff semantics.

### Subprocess Nesting in Swimlanes

Subprocess nodes show their composite label and are clustered with their
parent lane. Child nodes are hidden when `parent_only` is active.

## Guidance for Swimlane Extensions

Future swimlane work should:

- Keep lane cluster assignment separate from lane-agnostic shared routing.
- Use shared SVG edge primitives for boundary/rework handling.
- Reuse shared subprocess projection logic.
- Avoid introducing swimlane-specific edge attributes into shared modules.
