# FLO Core Language

Purpose: define the normative meaning of FLO source documents, the canonical
compiled process model, and the minimum semantic rules that implementations
must enforce.

## Intent

FLO is a declarative process language.
Authors describe process facts such as ordered steps, branch points, waiting,
ownership, and supporting metadata.

Implementations compile that authored process description into a canonical,
graph-shaped process model that is independent of any single rendering surface.

This compiled model is the semantic foundation for validation,
visualization, analysis, and downstream integrations.
Renderers, exporters, and CLI commands operate on this shared meaning rather
than inventing alternate process semantics.

## Source document conventions

The FLO source format uses a small set of top-level conventions before authored
process content is compiled into the canonical process model.

## Authoring model

FLO's normative source-authoring model is process-first rather than graph-first.

1. Ordered steps are the primary source form
    - Authors normally declare a `steps` list in business sequence order.
    - When no explicit top-level `transitions` or `edges` list is provided,
       implementations must synthesize default control flow between adjacent
       non-`end` steps.

2. Branching is declared locally
    - A branching step, usually a `decision`, should declare `outcomes` that map
       branch labels to target step identifiers.
    - These outcome declarations compile into directed control-flow edges in the
       canonical process model.

3. Explicit transitions are optional
    - Top-level `transitions` or `edges` may be used for advanced,
       non-local, or compatibility-oriented control-flow authoring.
    - When an explicit transitions list is present, it is the authoritative
       control-flow declaration for that source document.

4. Graph structure is compiled semantic form
    - Nodes and edges remain the canonical internal and serialized process
       structure.
    - In normal authoring, that graph is derived from the process description
       rather than authored directly.

### Top-level conventions

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

The canonical compiled FLO process model includes the following entity
families:

1. Process
   - A named, versionable process definition with stable identity and optional
     metadata.

2. Node
   - The compiled representation of a process step or control point.

3. Edge
   - A compiled directed relationship between nodes representing control flow.

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
   - Every authored step or compiled node must have a unique identifier within
     the process.

2. Single entry point
   - Exactly one `start` node is required.

3. At least one termination point
   - At least one `end` node is required.

4. Explicit transition precedence
   - If a top-level `transitions` or `edges` list is present, implementations
     must treat that list as the authoritative source of control flow for the
     document rather than also synthesizing default sequential edges.

5. Implicit sequential synthesis
   - If no top-level `transitions` or `edges` list is present,
     implementations must synthesize a sequential edge from each non-`end`
     step to the next step in source order.
   - A step with non-empty `outcomes` must not also receive an additional
     implicit sequential edge solely from adjacency.

6. Outcome-based branching synthesis
   - `outcomes` declarations must compile into outgoing edges from the
     declaring step to the named target steps.

7. Edge endpoint validity
   - Every compiled edge source and target must resolve to a declared node.

8. Decision branching minimum
   - Every `decision` node must have at least two outgoing compiled edges.

9. Predecessor rule
   - Every non-`start` node must have at least one predecessor.

10. Successor rule
    - Every non-`end` node must have at least one successor.

11. Reachability from start
    - Every node must be reachable from the `start` node.

12. Reachability to termination
    - Every node must be able to reach at least one `end` node.

13. Cycles are allowed
    - Cycles are permitted in the process graph; they are not invalid solely
      because they are cyclic.

14. Queue metadata validation
    - If `metadata.buffer_capacity` is present on a queue node, it must be an
      integer greater than or equal to `1`.
    - `metadata.queue_policy` is optional under the current v0.1 implementation
      and may be used by downstream analysis or future queueing models.

## Serialization relationship

The canonical compiled process model is conceptually prior to any single
serialization.

- `schema/flo_ir.json` defines the authoritative serialized structural contract.
- Implementations may use typed objects internally.
- JSON output is a serialization of the canonical compiled model, not a
   separate source of semantic truth.

## Scope boundaries

FLO core language semantics cover:

- process structure
- step identity and compiled node identity
- authored control-flow declarations and compiled control-flow rules
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
- The historical design note in `docs/design/history/IR.md` is explanatory background
   only; this file is the normative semantic source.
