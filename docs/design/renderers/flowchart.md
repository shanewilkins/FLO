# Flowchart Renderer Design

Status: accepted

## Why This Exists

Flowchart diagrams provide a simple, control-flow-focused visualization of a
process: nodes represent steps, edges represent flow transitions. This
specification clarifies visual conventions and default policies so flowchart
remains the baseline diagram type and a reference for other renderers.

## Visual Conventions

### Node Rendering

Nodes are rendered with shapes matching their kind:

- `start` → ellipse (circle)
- `task` → rectangle
- `system_task` → rectangle (same visual as task, semantic difference noted in metadata)
- `queue` → rectangle (same visual as task, labeled as queue in node name/metadata)
- `decision` → diamond
- `end` → ellipse (circle)

Node labels show the step name from the model.

### Edge Rendering

Edges represent control flow transitions:

- Normal edges: solid lines with optional outcome labels (if `--detail` is not "summary").
- Rework edges (backward flow): dashed lines, styled to distinguish from forward flow.
- Boundary edges (across layout wrapping): corridor routing with continuation markers.

### Subprocess Representation

When a node is a subprocess:
- The node displays a composite label indicating it contains nested steps.
- By default (expanded view), subprocess children are nested in a cluster subgraph.
- With `--subprocess-view parent-only`, subprocess nodes are collapsed and children
  are hidden, showing only parent references.

## Layout Behavior

- Default rankdir: `TB` (top-to-bottom)
- With `--orientation lr`: `LR` (left-to-right)
- Wrapping: supported via `layout_wrap` options (chunked planner)
- When wrapping is active, splines use orthogonal routing for deterministic boundary behavior

## Renderer Boundary Model

Flowchart rendering follows the shared renderer architecture:

1. **Input normalization**
   Extract nodes, edges, and subprocess relationships from canonical IR or dict input.

2. **Graph assembly**
   Apply subprocess projection, coordinate edge routing, set layout directives
   (rankdir, splines, spacing).

3. **Node and edge presentation**
   Render nodes with kind-based shapes and edges with outcome labels (if verbose).

4. **Subprocess clustering**
   Render subprocess children as nested clusters when not in `parent-only` view.

## Current Module Layout

- `src/flo/render/_graphviz_dot_flowchart.py`
  Flowchart entrypoint and node/edge assembly.
- `src/flo/render/_graphviz_dot_common.py`
  Shared helpers: node/edge extraction, subprocess projection, cluster assembly.
- `src/flo/render/_graphviz_dot_edge_routing.py`
  Shared edge routing (normal, boundary corridor, rework) used by flowchart
  and swimlane.

## Edge Cases and Policies

### Unreachable Nodes

Flowchart renders all nodes declared in the model:
- Unreachable nodes (no incoming edges) appear in the diagram.
- A future analysis layer may flag them as diagnostics (not a render concern).

### Missing Outcome Labels

When a decision node lacks explicit outgoing edge labels:
- Edges are rendered with generic labels (Graphviz default or empty).
- A diagnostic may warn about missing decision outcome clarity.

### Decision Node Without Outgoing Edges

This is a model-level concern (validation), not a rendering concern:
- The node still renders.
- Validation passes the diagnostics upstream.

### Subprocess Nesting Depth

Flowchart clusters subprocess children recursively:
- Deep nesting is allowed and styled consistently.
- Cluster labels indicate hierarchy level (optional future enhancement).

## Shared Infrastructure Usage

Flowchart uses shared edge routing to handle:
- Boundary corridors for wrapped diagrams.
- Rework edge styling and routing.
- Edge constraint and weight management for layout control.

This allows swimlane and flowchart to evolve independently while maintaining
consistent boundary/rework behavior.

## Guidance for Flowchart Extensions

Future flowchart work should:

- Keep it simple: default to basic node/edge rendering.
- Use shared edge routing for boundary and rework cases.
- Reuse shared subprocess projection.
- Avoid adding flowchart-specific attributes to shared modules.
- Document any new layout options or subprocess policies clearly.

## Relationship to Other Renderers

Flowchart is the simplest renderer and serves as a baseline:

- Swimlane adds lane clustering on top of flowchart's node/edge foundation.
- Spaghetti replaces control flow with inferred movement paths and spatial layout.
- SPPM adds publication bands, publication-driven styling, and detailed metrics.

All renderers can share edge routing, subprocess projection, and layout planning
infrastructure from the core.
