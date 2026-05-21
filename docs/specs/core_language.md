# FLO Core Language

Purpose: define the normative meaning of FLO's canonical process model and the
minimum semantic rules that implementations must enforce.

## Intent

FLO defines a canonical, graph-shaped process model that is independent of any
single rendering surface.

This model is the semantic foundation for validation, visualization, analysis,
and downstream integrations. Renderers, exporters, and CLI commands operate on
this shared meaning rather than inventing alternate process semantics.

## Source document conventions

The FLO source format uses a small set of top-level conventions before content
is compiled into the canonical process model.

1. Version declaration
   - A FLO source document must declare `spec_version`.
   - The current supported language version is `"0.1"`.

2. Composed source documents
   - FLO source documents may include other source files via top-level include
     directives.
   - `includes` is the canonical list form.
   - `include` is a supported single-value alias.

3. Include resolution
   - Include paths are resolved relative to the current source file.
   - Include cycles are invalid.
   - Duplicate step identifiers introduced by composition are invalid.

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
- `queue`
- `wait`
- `decision`
- `subprocess`

Other node families may be added later, but this set defines the current
normative baseline.

Current node-family intent:

- `queue` represents explicit waiting or buffering before work begins.
- `wait` represents an explicit hold state without implying active work.
- `subprocess` represents a collapsible child-process boundary in the source
   model and may be projected differently by renderers.

## Timing semantics

FLO distinguishes waiting and active setup or work time because they represent
different process facts and should not be collapsed into one metric.

Normative timing-placement rules:

1. Queue delay belongs on queue nodes
   - `metadata.wait_time` is valid only on `queue` nodes.

2. Active work and setup time belong on work nodes
   - `metadata.cycle_time`, `metadata.crossover_time`, and alias fields such as
     `transfer_time` or `changeover_time` belong on work nodes such as `task`,
     `system_task`, and `subprocess`.

3. Queue nodes are delay-only nodes
    - Queue nodes must not carry active work or setup-time fields such as
       `cycle_time`, `crossover_time`, `transfer_time`, or `changeover_time`.

4. Authors should model waiting structurally
   - If a process includes substantial waiting before work begins, authors
     should represent that waiting with an explicit `queue` node rather than
     attaching `wait_time` directly to the downstream work step.

These rules preserve the semantic distinction between queueing delay and
changeover or processing time.

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

11. Queue metadata validation
    - If `metadata.buffer_capacity` is present on a queue node, it must be an
       integer greater than or equal to `1`.
    - `metadata.queue_policy` is optional under the current v0.1 implementation
       and may be used by downstream analysis or future queueing models.

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
- The CLI/interface contract lives in `docs/specs/cli_error_contract.md`.
- Timing rationale and modeling background are further explained in
   `docs/design/wait-time-vs-changeover-time-semantics.md`, but this file owns
   the normative rule.
- The historical design note in `docs/design/IR.md` is explanatory background
   only; this file is the normative semantic source.
