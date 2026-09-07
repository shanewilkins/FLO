# FLO

FLO is a declarative plain-text language for process-improvement professionals
modeling business processes.

It allows you to define processes in a minimal, versioned format and
compile them into a canonical graph representation (FLO IR) for
visualization and analysis.

The same model can serve visual review and downstream analysis tools without
being trapped in a proprietary modeling application.

Start here: `docs/Quickstart.md`

Complete reference: `docs/User_Manual.md`

Supported platforms and trust assumptions: `docs/SUPPORT.md`

------------------------------------------------------------------------

## Vision: From Process Documentation To Organizational Observability

FLO's MVP is a way to represent a process clearly: define it in plain text,
compile it into a canonical graph, validate it, and generate diagrams and
analysis artifacts. Process models are explicit, versioned, diffable, and
usable by both people and tools.

Over time, FLO is intended to become a layer of organizational observability.
The goal is not to replace an ERP, CRM, HRIS, spreadsheet, or the people who
operate an organization. Those remain the implementation. FLO makes the
architecture legible around them.

That longer-term model could connect processes to organizational capabilities,
interfaces, dependencies, ownership, and contracts—making it possible to
query how work is structured, analyze dependencies and impact, and understand
how a change may propagate through the organization. In that sense, the
direction is from documenting individual processes to making the system
discoverable and organizational change safer.

The principle is:

> Don't build another ERP. Build the layer that makes the organization
> observable.

The current language and FLO IR are the foundation for that direction. The
vision is deliberately broader than the current v0.x implementation; current
capabilities and non-goals are described below.

------------------------------------------------------------------------

## Development Workflow (uv)

FLO uses `uv` as the canonical developer tool for environment management,
dependency sync, running commands, builds, and publish.

From the repository root:

```bash
npm ci --ignore-scripts --no-audit --no-fund
uv sync --dev
```

Run FLO locally:

```bash
uv run flo render examples/reference/linear.flo --diagram sppm
```

Run quality gates:

```bash
uv run pre-commit run --all-files
```

Build distributions:

```bash
uv run python scripts/vendor_elkjs.py
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
-   Graph projections: swimlane, spaghetti map, SPPM, and value stream map\
-   SVG and JSON exports\
-   Ingredients list and movement report exports\
-   Stable foundation for analytics

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

## Governance And Sources Of Truth

FLO assigns authority by domain rather than using one total document
hierarchy:

- product outcomes and release commitments: `docs/requirements/`
- language, CLI, diagram, and public-interface meaning: `docs/specs/`
- serialized structure: `schema/`
- scope and privacy boundaries: `docs/policy/`
- durable decision rationale: `docs/design/adr/`
- user workflows: `docs/Quickstart.md` and `docs/User_Manual.md`

The complete governance model and change classes are defined in
`docs/GOVERNANCE.md`.

------------------------------------------------------------------------

## Current Semantic Constraints (v0.1)

This is a summary only. Normative semantics live in `docs/specs/core_language.md`.

- Exactly one `start` node.
- At least one `end` node.
- All edge endpoints must resolve to declared node IDs.
- Every non-`start` node must have at least one predecessor.
- Every non-`end` node must have at least one successor.
- Every node must be reachable from `start`.
- Every node must be able to reach at least one `end` node.
- `decision` nodes must have at least two outgoing transitions.
- `wait_time` is valid only on `queue` nodes.

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
