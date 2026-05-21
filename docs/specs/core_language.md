# FLO Core Language

Purpose: define the normative meaning of FLO's canonical process model and the
minimum semantic rules that implementations must enforce.

## Intent

FLO defines a canonical, graph-shaped process model that is independent of any
single rendering surface.

This model is the semantic foundation for validation, visualization, analysis,
and downstream integrations. Renderers, exporters, and CLI commands operate on
this shared meaning rather than inventing alternate process semantics.

## Core entities

The canonical FLO process model includes the following entity families:

1. Process
   - A named, versionable process definition with stable identity and optional
     metadata.

2. Node
   - A process step or control point.

3. Edge
   - A directed relationship between nodes representing control flow.

4. Lane
   - An optional grouping surface for nodes, commonly used for role,
     department, or system responsibility.

5. Timing and IO metadata
   - Optional descriptive metadata that enriches nodes without changing the
     fundamental graph model.

## Node types

The current MVP node vocabulary is:

- `start`
- `end`
- `task`
- `system_task`
- `decision`

Other node families may be added later, but this set defines the current
normative baseline.

## Normative semantic rules

An implementation of FLO must enforce these minimum semantic rules:

1. Stable node identity
   - Every node must have a unique identifier within the process.

2. Single entry point
   - Exactly one `start` node is required.

3. At least one termination point
   - At least one `end` node is required.

4. Edge endpoint validity
   - Every edge source and target must resolve to a declared node.

5. Decision branching minimum
   - Every `decision` node must have at least two outgoing edges.

6. Predecessor rule
   - Every non-`start` node must have at least one predecessor.

7. Successor rule
   - Every non-`end` node must have at least one successor.

8. Reachability from start
   - Every node must be reachable from the `start` node.

9. Reachability to termination
   - Every node must be able to reach at least one `end` node.

10. Cycles are allowed
   - Cycles are permitted in the process graph; they are not invalid solely
     because they are cyclic.

## Serialization relationship

The canonical process model is conceptually prior to any single serialization.

- `schema/flo_ir.json` defines the authoritative serialized structural contract.
- Implementations may use typed objects internally.
- JSON output is a serialization of the canonical model, not a separate source
  of semantic truth.

## Scope boundaries

FLO core language semantics cover:

- process structure
- node and edge identity
- basic control-flow rules
- optional lanes and descriptive metadata

FLO core language semantics do not by themselves define:

- renderer-specific visual conventions
- movement-analysis semantics beyond their dependence on the process graph
- simulation behavior
- scheduling or workflow execution

## Relationship to other documents

- Structural serialization authority belongs in `schema/flo_ir.json`.
- Diagram-specific normative meaning belongs in the other files under
  `docs/specs/`.
- The historical design note in `docs/design/IR.md` is explanatory and may
  provide additional context, but this file is the normative semantic source.
