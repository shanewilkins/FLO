# FLO

FLO is a declarative language for modeling organizational flow.

It allows you to define processes in a minimal, versioned format and
compile them into a canonical graph representation (FLO IR) for
visualization and analysis.

User documentation: `docs/User_Manual.md`

------------------------------------------------------------------------

## Development Workflow (uv)

FLO uses `uv` as the canonical developer tool for environment management,
dependency sync, running commands, builds, and publish.

From the repository root:

```bash
uv sync --dev
```

Run FLO locally:

```bash
uv run flo run examples/reference/linear.flo
```

Run quality gates:

```bash
uv run pre-commit run --all-files
```

Build distributions:

```bash
uv build
```

Publish (token auth):

```bash
uv publish dist/flo_lang-<version>*
# username prompt: __token__
# password prompt: pypi-<token>
```

------------------------------------------------------------------------

## Example

``` yaml
spec_version: "0.1"

process:
  id: onboarding_v1
  name: Client Onboarding
  version: 1
  owner:
    id: ops_mgr
    name: Ops Manager
  business_units:
    - id: sales
      name: Sales
    - id: ops
      name: Operations

steps:
  - id: start
    kind: start
    name: Start

  - id: collect_docs
    kind: task
    name: Collect Documents
    lane: sales

  - id: verify
    kind: task
    name: Verify Documents
    lane: ops

  - id: approved
    kind: decision
    name: Approved?
    outcomes:
      yes: finish
      no: collect_docs

  - id: finish
    kind: end
    name: Complete
```

------------------------------------------------------------------------

## What FLO Provides

-   Deterministic compilation to FLO IR\
-   Structural and semantic validation\
-   Graph projections: flowchart, swimlane, spaghetti map, SPPM\
-   DOT and JSON exports\
-   Ingredients list and movement report exports\
-   Stable foundation for analytics

------------------------------------------------------------------------

## What FLO Does Not Provide

-   Workflow execution\
-   Task scheduling\
-   Orchestration\
-   Simulation engines (v0.x)

------------------------------------------------------------------------

## Architecture

-   `src/flo/` --- compiler, validators, renderers, and CLI\
-   `schema/` --- JSON schemas for FLO IR and types\
-   `examples/` --- canonical reference examples\
-   `tests/` --- unit, integration, and conformance tests\
-   `docs/` --- user manual and design documents

Downstream projects depend on FLO IR.

------------------------------------------------------------------------

## Source of Truth Hierarchy

- Structural contract SSOT: `schema/flo_ir.json`
- Semantic SSOT: `docs/design/IR.md`
- User-facing summary: `README.md`

Hierarchy policy and update workflow are defined in
`docs/design/SSOT_Hierarchy.md`.

------------------------------------------------------------------------

## Current Semantic Constraints (v0.1)

- Exactly one `start` node.
- At least one `end` node.
- All edge endpoints must resolve to declared node IDs.
- Every non-`start` node must have at least one predecessor.
- Every non-`end` node must have at least one successor.
- Every node must be reachable from `start`.
- Every node must be able to reach at least one `end` node.
- `decision` nodes must have at least two outgoing transitions.

------------------------------------------------------------------------

## Versioning

FLO follows semantic versioning at the spec level.

-   v0.x: rapid iteration\
-   v1.0: language stability

------------------------------------------------------------------------

## Philosophy

FLO treats processes as first-class artifacts:

-   Explicit\
-   Versioned\
-   Portable\
-   Validatable

It is a small language by design.

------------------------------------------------------------------------

## Schema Contract & Migration

As of v0.1 the compiler emits a schema-shaped canonical IR and the
runtime enforces that contract. The compiler must set `IR.schema_aligned`
to `True` and `IR.to_dict()` will produce the top-level mapping with
`process`, `nodes`, and `edges` fields required by the authoritative
JSON Schema in `schema/flo_ir.json`.

If you are upgrading from an earlier development version that relied on
an internal IR translator, update any custom compiler integrations to
emit the schema-shaped IR directly. The translator was intentionally
removed; CI now validates example outputs using the same schema and
will fail when the contract is violated.
