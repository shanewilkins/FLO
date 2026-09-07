# FLO Reference Guide

This reference explains the complete FLO authoring, validation, rendering, and
export surface. New users should begin with `docs/Quickstart.md`.

Normative language semantics and CLI contracts live under `docs/specs/`.
This manual is user-facing guidance and examples; when it summarizes a rule,
the spec remains authoritative.

For the documentation map, see `docs/README.md`.
For governance, change classes, and domain-specific authority, see
`docs/GOVERNANCE.md`.
For normative product and technical requirements, see `docs/requirements/`.
For the project framing and modeling principles, see `docs/FLO_Manifesto.md`.

## 1) What FLO Is

FLO is a domain-specific, declarative language for modeling business processes.
Authors normally write ordered steps and local branch outcomes.
FLO then compiles that source into canonical IR for validation, analysis, and rendering.

FLO provides:

- Deterministic compilation to canonical IR
- Structural and semantic validation
- Schema-shaped JSON export for downstream tools
- Human-readable ingredient and movement exports
- Swimlane, spaghetti-map, SPPM, and value-stream-map diagram rendering

FLO does not provide:

- Workflow execution
- Scheduling or orchestration
- Runtime simulation

## 2) Requirements

- Python 3.14+

## 3) Install and Run

From the repository root:

```bash
uv sync --dev
```

Run FLO on a file.
The default output format is direct SVG to stdout. New work should explicitly
select a maintained diagram family.

```bash
uv run flo examples/reference/linear.flo --diagram sppm
```

Preferred modern entry points:

```bash
uv run flo export examples/reference/new_semantics.flo -o new_semantics.json
uv run flo render examples/reference/new_semantics.flo --export svg --render-to new_semantics.svg --diagram sppm
```

You can also use explicit subcommands:

```bash
uv run flo render examples/reference/linear.flo --diagram sppm
```

Common developer commands:

```bash
uv run pre-commit run --all-files
uv run pytest -q
uv build
```

## 4) Your First FLO File

Every FLO file should begin with `spec_version`. The only current valid value is `"0.1"`. It is used by the parser to select the correct language version and will gate breaking changes in future releases.

Minimal example:

```yaml
spec_version: "0.1"

process:
  id: onboarding_v1
  name: Client Onboarding

steps:
  - id: start
    kind: start
    name: Start

  - id: collect_docs
    kind: task
    name: Collect Documents

  - id: finish
    kind: end
    name: Complete
```

Notes:

- Use stable `id` values because outcomes, optional explicit transitions, and diagnostics reference them.
- When `transitions` are omitted, FLO connects adjacent non-`end` steps in source order.
- `decision` steps should define `outcomes` to branch flow.

## 4.1) Terminology

FLO lets you describe a business process in the order work happens.
In the common case, each authored step becomes a node in the compiled model and adjacent steps become control-flow edges automatically.
When the process branches, the branching step declares `outcomes` that point to the next relevant steps.
The compiled result is still a directed graph, but authors usually do not need to build that graph edge-by-edge.

## 4.1.1) File Composition (Includes)

Large models can be split into multiple files with top-level include directives.

Extension convention:

- Use `.flo` for both entry files and included fragments.
- Parsing is extension-agnostic: any included file that contains a valid YAML mapping is accepted.

Supported include keys:

- `includes`: list of file paths
- `include`: single file path (alias)

Paths are resolved relative to the current file. The entry file's directory is
the trust root: absolute paths, `..` traversal, and symlinks are accepted only
when their resolved target remains inside that directory.

```yaml
spec_version: "0.1"

includes:
  - chocolate_chip_cookies/materials.flo
  - chocolate_chip_cookies/locations.flo
  - chocolate_chip_cookies/process.flo
```

Composition behavior:

- Includes are loaded first, then the current file is merged last.
- Duplicate step IDs across included files are rejected.
- Include cycles are rejected.
- A source file is limited to 1,000,000 UTF-8 bytes; composition is limited to
  256 included files, 32 include levels, and 8,000,000 total source bytes.
- FLO does not retrieve includes over the network. These boundaries support
  trusted local authoring, not arbitrary hosted uploads.

## 4.2) Step Kinds and Canonical Step Fields

The current schema-aligned step kinds are:

- `start`: the single process entry point
- `task`: a general work step
- `system_task`: an explicitly system-owned task
- `queue`: a queue or buffer step
- `wait`: an explicit hold state
- `decision`: a branch point with at least two outgoing outcomes
- `subprocess`: a collapsed child-process step
- `parallel_split`: the start of concurrent control flow
- `parallel_join`: the synchronization point for concurrent control flow
- `end`: a terminal step

Canonical common step fields:

- `name`: display label for the step
- `lane`: swimlane grouping key
- `location`: location id for spatial and movement analysis
- `performed_by`: list of person resource ids performing the step
- `uses`: list of equipment resource ids used by the step
- `consumes`: list of item ids consumed by the step
- `produces`: list of item ids produced by the step
- `note`: short human note for review or context
- `subnodes`: optional nested step list for `subprocess` nodes
- `metadata`: machine-facing metadata map

Compatibility aliases remain accepted in v0.1.

- `workers` maps to `performed_by`
- `equipment` maps to `uses`
- `inputs` maps to `consumes`
- `outputs` maps to `produces`

Subprocess child-node example:

```yaml
steps:
  - id: start
    kind: start
  - id: prep
    kind: subprocess
    name: Prep Phase
    subnodes:
      - id: gather
        kind: task
        name: Gather Inputs
      - id: mix
        kind: task
        name: Mix Inputs
  - id: end
    kind: end
```

Time-related node metadata fields (for example `cycle_time`, `wait_time`, `lead_time`) should use:

- `value`: number >= 0
- `unit`: one of `s`, `min`, `hr`, `d` (`m` is still accepted for backwards compatibility)

This scalar form is the current executable contract.
FLO must preserve an omitted or invalid timing field separately from a valid measured zero; a missing queue wait does not mean zero minutes.

### Accepted future measurement-profile contract

FLO 0.5 will replace the scalar form through a deliberate pre-1.0 breaking change.
The accepted profile contract will preserve multiple externally calculated statistics without making FLO the event repository or statistical-computation system.

The planned shape is conceptually:

```yaml
cycle_time:
  basis: observed
  primary: mean
  analysis_input: mean
  sample:
    count: 39
    unit: order_activity_occurrence
    cohort_ref: representative-friday-orders
    window:
      start: 2026-08-01T00:00:00Z
      end: 2026-08-31T23:59:59Z
  evidence_ref: representative-friday-91
  statistics:
    - method: mean
      value: 30.4
      unit: min
    - method: median
      value: 30.3
      unit: min
    - method: percentile
      parameters:
        percentile: 90
        interpolation: linear
      value: 33.8
      unit: min
```

This example documents an accepted direction, not syntax accepted by the current parser.
The implementing release will publish the exact schema and migration procedure.

`basis` will distinguish observed, simulated, estimated, planned, and target profiles.
`primary` will select the compact display result.
`analysis_input` will separately select the numeric result available to modeled static timing.
FLO will not infer either selector or assume that an unlabeled duration is an average.

Core methods will include count, sum, minimum, maximum, mean, median, mode, percentile, and standard deviation.
Parameterized methods will record definitions such as percentile interpolation and sample or population standard deviation.
Namespaced methods such as `lss4py:trimmed_mean` will allow producer-specific extensions without expanding FLO's core method vocabulary.

FLO will validate, preserve, and project supplied profiles.
Packages such as `lss4py`, governed worksheets, or other analytics systems will calculate them and retain the authoritative event or row-level evidence.
An `evidence_ref` will identify that external evidence without causing FLO to fetch or embed it.

The `value_class` field classifies a step by its Lean value contribution:

- `VA` — value-adding
- `RNVA` — required non-value-adding
- `NVA` — non-value-adding
- `unknown` — unclassified (default when omitted)

The `description` field is a free-text string providing a human-readable explanation of what the step does. It is displayed in the SPPM info box and is available as a pass-through field in other renderers.

Queue and task timing constraint:

- `wait_time` is valid only on `queue` nodes.
- `cycle_time`, `crossover_time`, `transfer_time`, and `changeover_time` are valid on work nodes such as `task`, `system_task`, and `subprocess`.
- If `wait_time` appears on a work node, compiler validation fails and the model must be restructured by inserting a queue node.

The following metadata keys are recognized and validated by FLO. Other keys are
currently preserved in IR for custom tooling. The approved requirement is to
emit non-fatal warnings for unknown keys without rejecting or dropping them;
implementation alignment is tracked in the technical requirements catalog.

| Key | Type | Description |
| --- | --- | --- |
| `cycle_time` | time object | Active processing time for the step |
| `wait_time` | time object | Queue delay before work begins — `queue` nodes only |
| `lead_time` | time object | Total elapsed time including wait |
| `value_class` | `VA`\|`RNVA`\|`NVA`\|`unknown` | Lean value classification |
| `description` | string | Human-readable explanation of the step |
| `queue_policy` | string | Queue discipline (e.g. `fifo`, `lifo`) — `queue` nodes |
| `buffer_capacity` | integer | Maximum queue depth — `queue` nodes |

Pattern: task with queue delay

Bad (rejected by compiler):

```yaml
steps:
  - id: wash
    kind: task
    name: Wash
    metadata:
      cycle_time:
        value: 30
        unit: min
      wait_time:
        value: 18
        unit: min
```

Good (queue + task split):

```yaml
steps:
  - id: wash_queue
    kind: queue
    name: Washer Queue
    metadata:
      wait_time:
        value: 18
        unit: min

  - id: wash
    kind: task
    name: Wash
    performed_by:
      - Staff
    metadata:
      value_class: VA
      cycle_time:
        value: 30
        unit: min
```

Example:

```yaml
steps:
  - id: start
    kind: start
    name: Start
  - id: review_queue
    kind: queue
    name: Review Queue
    metadata:
      queue_policy: fifo
      buffer_capacity: 50
  - id: approved
    kind: decision
    name: Approved?
  - id: finish
    kind: end
    name: Complete
```

## 4.2.1) Modeling Queues and Process Steps

FLO enforces queue/task semantics at compile time to keep process diagnostics correct:

- Queue nodes represent waiting.
- Task-like nodes represent active work and setup/changeover.

Core modeling rules:

- Use `kind: queue` + `metadata.wait_time` for delays caused by unavailable downstream capacity.
- Use `kind: task`/`system_task`/`subprocess` + `metadata.cycle_time` for active work duration.
- Use `metadata.crossover_time` for setup/changeover on work nodes.

Lean alignment:

- Waiting and setup are both non-value-adding, but they are not the same problem.
- Queue reduction methods: pull systems, kanban, takt leveling, WIP limits.
- Changeover reduction methods: SMED, 5S, standard work, cross-training.

Restructuring guide for existing models:

1. Find task-like nodes that contain `metadata.wait_time`.
2. Insert a preceding `queue` node for each waiting segment.
3. Move `wait_time` from the task-like node to the new queue node.
4. Rewire transitions so flow goes through the queue node first.
5. Re-validate: `uv run flo validate <file>.flo`.

Real-world example (before/after):

```yaml
# Before (invalid)
- id: execute_service
  kind: task
  metadata:
    cycle_time: {value: 13, unit: min}
    wait_time: {value: 6, unit: min}

# After (valid)
- id: execute_service_wait_queue
  kind: queue
  metadata:
    wait_time: {value: 6, unit: min}

- id: execute_service
  kind: task
  metadata:
    cycle_time: {value: 13, unit: min}
```

## 4.3) Transition Forms

FLO supports these transition forms:

- Explicit transition list: `transitions` with `source` and `target`
- Outcome transitions from decisions: `outcomes` mapping under a `decision` step
- Optional transition labels: `outcome` and or `label` fields
- Optional transition semantics: `handoff`, `rework`, `edge_type`, and `metadata`

Canonical transition example:

```yaml
items:
  - id: submission
    name: Submission
    kind: information

resources:
  - id: reviewer
    name: Reviewer
    kind: person
  - id: editor
    name: Editor
    kind: person

steps:
  - id: start
    kind: start

  - id: review
    kind: task
    consumes: [submission]
    produces: [submission]
    performed_by: [reviewer]

  - id: decision
    kind: decision
    name: Accepted?
    outcomes:
      yes: publish
      no:
        target: rework
        edge_type: rework
        rework: true

  - id: rework
    kind: task
    consumes: [submission]
    produces: [submission]
    performed_by: [editor]

  - id: publish
    kind: end

transitions:
  - source: start
    target: review
  - source: review
    target: decision
    handoff: true
    metadata:
      handoff_type: responsibility
  - source: decision
    target: publish
    outcome: yes
  - source: decision
    target: rework
    outcome: no
    edge_type: rework
    rework: true
  - source: rework
    target: review
    edge_type: rework
    rework: true
```

Parallel-flow example:

```yaml
steps:
  - id: split
    kind: parallel_split
    name: Split Preparation

  - id: prep_a
    kind: task

  - id: prep_b
    kind: task

  - id: join
    kind: parallel_join
    name: Join Preparation

transitions:
  - source: split
    target: prep_a
  - source: split
    target: prep_b
  - source: prep_a
    target: join
  - source: prep_b
    target: join
```

## 4.4) Process Metadata, Items, Resources, and Locations

Process-level KPI and resource data should be stored in metadata.

- Canonical IR location: `process.metadata`
- Recommended place for KPIs: `process.metadata` (for example cycle time, yield)
- Top-level `items`, `resources`, and `locations` are the canonical process-level collections in FLO source and are preserved under `process.metadata` in exported schema JSON.
- Legacy `materials`, `equipment`, and `workers` collections are still accepted in v0.1 as compatibility aliases.
- A resource collection can be either:
  - A flat list of resource items.
  - A grouped object where each key maps to another collection (list or grouped object). This allows nested grouping.
- Grouped objects can include an optional `name` field for a human-readable label.

For material quantities, use one of two quantity shapes:

- Discrete count: `kind: count`, integer `value`, `unit: each` (optional `qualifier`, for example `large`)
- Continuous SI-style measure: `kind: measure`, numeric `value`, and metric `unit` from `mg|g|kg|ml|l|mm|cm|m`

The same quantity contract can be used for canonical `items` and `resources` when counts or measured quantities are useful.
`locations` usually use ids, names, optional kinds, and location metadata rather than quantity.

For spatial analysis and spaghetti-map rendering, locations can include optional spatial coordinates:

- `metadata.spatial.x`: numeric x coordinate
- `metadata.spatial.y`: numeric y coordinate
- `metadata.spatial.unit`: optional unit (`mm|cm|m|in|ft`)
- `kind`: optional semantic location kind used for spaghetti-map shape styling

Spaghetti rendering uses deterministic partial mode by default: routes whose
two endpoints are positioned are rendered, incomplete routes are omitted, and
both stderr and the SVG identify the result as partial. Use
`--spaghetti-strict-spatial` to reject any selected route with an unpositioned
endpoint. FLO never invents coordinates or substitutes graph layout.

Recommended domain-neutral kinds:

- `storage`: inventory/holding areas
- `operation`: general work/procedure areas
- `processing`: machine or transformation areas
- `staging`: buffer/queue/wait areas
- `support`: cleaning/inspection/service areas
- `transit`: hallways/transfer/conveyor paths

Compatibility aliases are still recognized (for example: `prep` -> `operation`, `heat` -> `processing`, `cooling` -> `staging`, `wash` -> `support`). Unknown kinds keep the default spaghetti node style.

Spaghetti maps can also render an optional area boundary overlay from process metadata:

- `process.metadata.layout_boundary`: boundary object
- Rectangle form: `x`, `y`, `width`, `height` (where `x,y` is the lower-left origin)
- Polygon form: `points` list with `x,y` vertices
- Optional `label` (or `name`) for boundary caption

Rectangle example:

```yaml
process:
  id: kitchen_flow
  name: Kitchen Flow
  metadata:
    layout_boundary:
      type: rectangle
      x: -1.0
      y: -1.0
      width: 8.0
      height: 6.0
      label: Kitchen Boundary
```

Polygon example:

```yaml
process:
  id: kitchen_flow
  name: Kitchen Flow
  metadata:
    layout:
      boundary:
        type: polygon
        name: Production Area
        points:
          - {x: 0.0, y: 0.0}
          - {x: 8.0, y: 0.0}
          - {x: 8.0, y: 4.0}
          - {x: 0.0, y: 4.0}
```

Example:

```yaml
locations:
  - id: prep_bench
    name: Prep Bench
    kind: operation
    metadata:
      spatial:
        x: 3.0
        y: 2.0
        unit: m
```

Grouping example for canonical items:

```yaml
items:
  dry:
    name: Dry Ingredients
    items:
      - id: flour
        name: Flour
        kind: material
        quantity:
          kind: measure
          value: 250
          unit: g
      - id: sugar
        name: Sugar
        kind: material
        quantity:
          kind: measure
          value: 120
          unit: g
  wet:
    name: Wet Ingredients
    dairy:
      name: Dairy
      items:
        - id: butter
          name: Butter
          kind: material
          quantity:
            kind: measure
            value: 100
            unit: g
    eggs:
      name: Eggs
      items:
        - id: egg
          name: Egg
          kind: material
          quantity:
            kind: count
            value: 2
            unit: each
            qualifier: large
```

Example:

```yaml
spec_version: "0.1"

process:
  id: chocolate_chip_cookies
  name: Chocolate Chip Cookie Process
  metadata:
    cycle_time_seconds:
      target: 14400
    yield_fraction:
      target: 0.96

items:
  - id: order_ticket
    name: Order Ticket
    kind: information
    quantity:
      kind: count
      value: 1
      unit: each
  - id: dough
    name: Dough
    kind: material
    quantity:
      kind: measure
      value: 2
      unit: kg

resources:
  - id: baker
    name: Baker
    kind: person
    quantity:
      kind: count
      value: 1
      unit: each
  - id: oven
    name: Convection Oven
    kind: equipment
    quantity:
      kind: count
      value: 1
      unit: each

locations:
  - id: main_kitchen
    name: Main Kitchen
    kind: operation
    metadata:
      site_code: HQ-01

steps:
  - id: start
    kind: start
  - id: mix
    kind: task
    consumes: [order_ticket, dough]
    produces: [dough]
    performed_by: [baker]
    uses: [oven]
    location: main_kitchen
  - id: end
    kind: end

transitions:
  - source: start
    target: mix
  - source: mix
    target: end
```

## 4.5) Diagram Types and When to Use Them

FLO can render a process model as several different diagram types, each suited to a different analysis goal:

| Diagram | Flag | Best for |
| --- | --- | --- |
| Swimlane | `--diagram swimlane` | Handoff analysis — requires `lane` on steps |
| Spaghetti map | `--diagram spaghetti` | Movement/travel path analysis — requires `location` on steps |
| SPPM | `--diagram sppm` | Lean process performance — uses `value_class`, `cycle_time`, queue `wait_time`, and `performed_by` |
| Value stream map | `--diagram value_stream` | Material, information, waiting, and modeled lead-time relationships |

### Value stream map

The maintained value-stream renderer reads canonical item relations and kinds:

- items with `kind: information` form a dashed information-flow surface;
- items with `kind: material` form a solid material-flow surface;
- `consumes` and `produces` anchor each item to process steps; and
- declared cycle, queue-wait, and changeover timing appears on process cards.

For each consumer, FLO links the nearest reachable producer through canonical
process structure. A consume without an upstream producer enters from the
external boundary; a produce without a downstream consumer exits to it. FLO
does not treat control-flow edges alone as item movement.

If either information or material flow is absent, the renderer still emits the
known surface and process cards, but stderr and a visible `Partial map` notice
name the missing surface. Missing optional timing is shown as unavailable; it
is never replaced with zero. Use a spaghetti map instead when the question is
physical travel between positioned locations.

### SPPM (Standard Process Performance Map)

SPPM renders a left-to-right (or top-to-bottom with `--orientation tb`) process map where each step is color-coded by its Lean value classification:

- **Green** — Value-adding (`VA`)
- **Yellow** — Required non-value-adding (`RNVA`)
- **Red** — Non-value-adding (`NVA`)

Each step node has a colored header and a white info sub-box showing available metrics.
Typical fields include description, cycle time, performers, wait time on queue nodes, and changeover time on task-like nodes.

SPPM-relevant fields per step:

- `metadata.value_class`: controls node color
- `metadata.cycle_time`: shown in info box as `CT:`
- `metadata.wait_time`: shown in info box as `WT:` (queue nodes)
- `metadata.crossover_time`: shown in info box as `CO:` (task/system_task/subprocess)
- `metadata.description`: shown as the first line of the info box
- `performed_by`: shown as the performer line in the info box
- `uses`: available for equipment-aware examples and downstream summaries

The current renderer shows one scalar value for each available timing field.
Under the accepted measurement-profile contract, compact output will show the explicitly selected primary statistic and identify its method, such as `Avg CT`, `Median WT`, or `P90 C/O`.
Detailed output will preserve all supported statistics, sample context, basis, and evidence identity.
Machine-readable output will preserve the complete profile even when the selected renderer cannot display every result.

Detailed measurement meaning will not depend on clicking or hovering.
An interactive host may open detail from a process box, while print and composed publication output will provide an equivalent table, callout, appendix, or companion artifact.

The default theme uses stoplight colors. Themes use Bootstrap-compatible semantic
roles: `success` for VA, `warning` for RNVA and queues, `danger` for NVA, and
`primary` for decision control points. FLO owns these tokens and does not import
Bootstrap CSS at runtime.

Alternative themes:

- `--sppm-theme flatly` — Flatly-compatible Bootstrap semantic palette
- `--sppm-theme print` — high-contrast fills suitable for black-and-white printing
- `--sppm-theme monochrome` — grayscale only
- `--sppm-theme <name>` — any custom theme defined under `[sppm.themes.<name>]` in `diagrams.toml`

The preferred 0.3 interface is the shared `--theme <name>` option. It applies
one central theme to SPPM, swimlane, spaghetti, and value-stream SVG output. Built-ins are
`default`, `flatly`, `print`, and `monochrome`. Direct session overrides are
`--background-color`, `--font-family` (a comma-separated fallback list), and
`--typography-scale` (`0.75` through `1.5`).

New reusable themes belong in the top-level registry and can inherit partial
values from one parent:

```toml
[render]
theme = "white_belt"

[themes.white_belt]
extends = "default"

[themes.white_belt.canvas]
background = "#fffdf8"

[themes.white_belt.typography]
font_family = ["Source Sans 3", "Arial", "sans-serif"]
scale = 1.05

[themes.white_belt.roles.queue]
fill = "#FFB74D"
border = "#E65100"
```

For backward compatibility, a custom theme that omits `queue` uses its `rnva`
style for queue triangles.

Custom theme example:

```toml
[sppm.themes.sunrise]
[sppm.themes.sunrise.va]
fill = "#FFF3B0"
border = "#E09F3E"

[sppm.themes.sunrise.rnva]
fill = "#FFD6A5"
border = "#F77F00"

[sppm.themes.sunrise.nva]
fill = "#FFADAD"
border = "#D00000"

[sppm.themes.sunrise.decision]
fill = "#E3EEF7"
border = "#285B8F"

[sppm.themes.sunrise.queue]
fill = "#F39C12"
border = "#C27D0E"
title_fill = "#2C3E50"
info_fill = "#2C3E50"

[sppm.themes.sunrise.unknown]
fill = "#FFFFFF"
border = "#6C757D"

[sppm.themes.sunrise.start_end]
fill = "#FFFFFF"
border = "#343A40"
```

Legacy `--sppm-theme` keeps its historical missing-name fallback. The shared
registry rejects unknown selected themes, unknown parents, inheritance cycles,
invalid colors, empty font lists, out-of-range scales, and unregistered roles
with an actionable option-validation error.

Preferred maintained SPPM rendering path:

```bash
uv run flo render examples/reference/semantic_controls_showcase.flo \
  --export svg \
  --render-to semantic_controls_showcase.svg \
  --diagram sppm
```

## 4.6) Understanding the Output Pipeline

FLO has four main output families.

1. Canonical machine-readable output.

  `flo export` emits schema-shaped JSON by default.

1. Maintained diagram artifacts.

  `flo render --export svg --render-to <file.svg>` emits direct SVG.

1. Operational text outputs.

  `flo render --export ingredients` emits human-readable item and resource summaries.
  `flo render --export movement` emits inferred movement summaries.

1. Static analysis reports.

  `flo inspect` emits concise timing, structural, or model-readiness reports,
  or deterministic JSON with `--format json`.

Canonical JSON example:

```bash
uv run flo export examples/reference/new_semantics.flo -o new_semantics.json
```

Maintained SVG example:

```bash
uv run flo render examples/reference/new_semantics.flo \
  --export svg \
  --render-to new_semantics.svg \
  --diagram sppm
```

Human-readable text export examples:

```bash
uv run flo render examples/reference/new_semantics.flo --export ingredients
uv run flo render examples/reference/chocolate_chip_cookies.flo --export movement
```

## 5) Core CLI Commands

For composed models, keep entry and included files as `.flo` files.
See Section 4.1.1 for include conventions.

## 5.1 Render

Parse, compile, validate, and render or export output.

```bash
uv run flo render path/to/model.flo --diagram sppm
```

Equivalent shorthand:

```bash
uv run flo path/to/model.flo --diagram sppm
```

## 5.2 Validate

Only validate model correctness.

```bash
uv run flo validate path/to/model.flo
```

## 5.3 Inspect

Inspect a validated process using deterministic static analysis. Timing is the
default; structural analysis reports handoffs, handoff candidates, rework,
non-rework path lengths, node kinds, and Lean value-class coverage. Model
inspection summarizes composition, entities, paths, named views, and requested
analysis or diagram readiness.

```bash
uv run flo inspect path/to/model.flo
uv run flo inspect path/to/model.flo --format json -o timing.json
uv run flo inspect path/to/model.flo --analysis structure
uv run flo inspect path/to/model.flo --analysis structure --format json -o structure.json
uv run flo inspect path/to/model.flo --analysis model
uv run flo inspect path/to/model.flo --analysis model --for-analysis timing
uv run flo inspect path/to/model.flo --analysis model --for-diagram spaghetti --format json
```

Timing JSON uses seconds as the canonical unit and includes per-node
contributions, path summaries, timing coverage, and explicit diagnostics.
Cyclic and parallel models do not receive a guessed lead time.

Structural analysis treats explicit handoffs as authoritative and reports an
unmarked lane change only as a candidate. It reports explicit rework separately
from inferred backward edges. Path length means edge count and excludes
identified rework edges; unresolved ordinary cycles and parallel flow produce
diagnostics instead of misleading path-length claims.

Model inspection runs only after successful validation. Readiness reports
`ready`, `partial`, or `unavailable` and distinguishes missing required data,
missing optional data, semantic limitations, and unsupported capabilities.
Entry filenames and includes are portable rather than absolute checkout paths.
`--for-analysis` and `--for-diagram` are accepted only with
`--analysis model`.

## 5.4 Export

Export as JSON by default, or choose SVG, Typst publication source, ingredients text, or movement text.

```bash
uv run flo export path/to/model.flo
uv run flo export path/to/model.flo --export ingredients
uv run flo export path/to/model.flo --export movement
uv run flo export path/to/model.flo --export svg
```

SVG is typically requested from `render` when diagram options or `--render-to` are needed.

## 6) Options

Common options:

- `-o, --output <file>`: write text or JSON output to file
- `-v, --verbose`: verbose logging
- `--export {svg,typst,json,ingredients,movement}`: choose output format

Inspect options:

- `--analysis {timing}`: choose the static analysis; timing is the default
- `--format {text,json}`: choose human-readable text or deterministic JSON

Diagram render options:

- `--diagram {swimlane,spaghetti,sppm,value_stream}`
- `--render-backend {svg}`
- `--spaghetti-channel {both,material,people}`
- `--spaghetti-people-mode {worker,aggregate}`
- `--spaghetti-strict-spatial`
- `--sppm-theme {default,print,monochrome}` or a config-defined theme name
- `--theme <name>`
- `--background-color <color>`
- `--font-family <family[,fallback...]>`
- `--typography-scale <0.75..1.5>`
- `--layout-wrap {auto,off}`
- `--layout-fit {fit-preferred,fit-strict}`
- `--layout-spacing {standard,compact}`
- `--sppm-step-numbering {off,node,edge}`
- `--sppm-label-density {full,compact,teaching}`
- `--sppm-wrap-strategy {word,balanced,hard}`
- `--sppm-truncation-policy {ellipsis,clip,none}`
- `--layout-max-width-px <dimension>`
- `--layout-target-columns <int>`
- `--publication-page-format {letter,a4,legal,tabloid}`
- `--sppm-max-label-step-name <int>`
- `--sppm-max-label-workers <int>`
- `--sppm-max-label-ctwt <int>`
- `--sppm-output-profile {default,book,web,print,slide}`
- `--profile {default,analysis}`
- `--detail {summary,standard,verbose}`
- `--orientation {lr,tb}` (`tb` means top-to-bottom)
- `--show-notes`
- `--subprocess-view {expanded,parent-only}`
- `--sppm-projection {top-level,child-map,inline}`
- `--sppm-focus-subprocess <node-id>`
- `--render-to <file>`

`--render-to` behavior:

- With `--export svg`, FLO writes maintained direct SVG to the target `.svg` file.
- With `--export typst --diagram sppm`, FLO writes Typst source to the target `.typ` file and page-local SVG figure assets beside it.
- Raster and PDF output are not emitted directly by FLO; convert SVG with an external tool if needed.

Examples:

```bash
uv run flo render examples/reference/swimlane.flo --export svg --render-to swimlane.svg --diagram swimlane
uv run flo render examples/reference/new_semantics.flo --export json
uv run flo render examples/reference/chocolate_chip_cookies.flo --export ingredients
uv run flo render examples/reference/chocolate_chip_cookies.flo --export movement
uv run flo render examples/reference/washnfold.flo --export svg --render-to washnfold_sppm.svg --diagram sppm --sppm-output-profile book --layout-target-columns 4
uv run flo render examples/reference/washnfold.flo --export typst --render-to washnfold.typ --diagram sppm --layout-overflow paginate --layout-target-columns 4
```

Important:

- Render-only flags are invalid with JSON, ingredients, or movement export modes.
- If you pass render-only flags together with JSON, ingredients, or movement export, FLO returns usage error code `1`.
- Direct-SVG row wrapping currently applies to unambiguous linear LR SPPM
  sequences. Branching and rework maps remain unwrapped until their continuation
  semantics can be preserved without conflating branches with page rows.
- Wrapped LR SPPM SVG routes each row boundary through a deterministic clear
  corridor from the previous row's bottom port to the next row's top port.

White Belt book asset:

```bash
# Build the reviewed SVG at the default reference-output path.
uv run --locked python scripts/build_white_belt_book_artifact.py

# Copy it directly into a book checkout.
uv run --locked python scripts/build_white_belt_book_artifact.py --output /path/to/book/diagrams/washnfold.svg

# Release/CI check: reject a missing, stale, or manually edited book asset.
uv run --locked python scripts/build_white_belt_book_artifact.py --check --output /path/to/book/diagrams/washnfold.svg
```

The command first regenerates `washnfold_white_belt` and requires it to match
the committed SPPM golden byte-for-byte. It then copies or verifies that exact
generated SVG; the book image must not be edited manually.

SPPM subprocess projection contract:

- `--subprocess-view parent-only` keeps subprocesses collapsed on the parent map and hides nested child nodes.
- `--sppm-projection top-level` is the default SPPM projection and renders the top-level map.
- `--sppm-projection child-map` focuses one subprocess and includes entry and exit context nodes.
- `--sppm-projection inline` tries to expand child steps inline near the parent context.
- Discovery cues for collapsed subprocesses are always explicit in SPPM node labels.

Renderer policy decisions:

- Rework edges are always dashed.
- Rework classification precedence is explicit metadata first and inferred back-edge fallback second.
- Cross-lane rework uses composite behavior.
- Layout fit modes are policy-defined as fit-preferred and fit-strict.

SPPM preset and config defaults:

- Built-in `--sppm-output-profile` presets set baseline SPPM defaults for orientation, wrapping, density, and named page formats.
- If a `diagrams.toml` file exists beside the source `.flo` file or in the current working directory, FLO loads `[sppm]` defaults automatically.
- Precedence is CLI flags, then explicit `diagrams.toml` keys, then preset overrides, then built-in defaults.

SPPM label policy matrix:

- `--sppm-wrap-strategy` selects wrapping behavior.
- `--sppm-truncation-policy` selects overflow behavior.
- Task node names, decision labels, subprocess titles, queue badges, decision and branch labels, and publication header and footer text all use `--sppm-max-label-step-name`.
- Performer-line text uses `--sppm-max-label-workers`.
- CT and WT metric lines and footer metric values use `--sppm-max-label-ctwt`.

SPPM time semantics:

- `wait_time` models queue delay.
- `crossover_time` models setup or changeover time.
- These metrics are intentionally distinct because they imply different operational problems and different improvement methods.
- Work-step shapes display declared setup or changeover as `C/O`; queue shapes
  display queue delay as `WT`.
- When timing is declared for the complete visible process, the footer shows
  cycle, waiting, C/O, and modeled lead time from the same static-analysis
  result used by `flo inspect`. Alternative paths show a range; unresolved
  timing shows `Unavailable` and points to inspect diagnostics.
- Under the accepted future profile contract, static timing will consume only
  an explicit numeric `analysis_input`; it will not calculate descriptive
  statistics or use the primary display result implicitly.
- Arithmetic over selected node statistics remains a modeled timing result and
  is never labeled as an empirical end-to-end mean, median, minimum, maximum,
  or percentile.

## 7) Input and Output Streams

FLO supports POSIX-style streams:

- Input path `-` means read from stdin
- Output path `-` means write to stdout
- Telemetry and debug output is kept off stdout payload streams so SVG, JSON, and text exports remain parse-safe.

Examples:

```bash
cat examples/reference/linear.flo | uv run flo -
uv run flo render examples/reference/linear.flo -o -
cat examples/reference/washnfold.flo | uv run flo inspect - --format json
```

## 8) Exit Codes

This section summarizes the normative CLI contract in `docs/specs/cli_error_contract.md`.

- `0`: success
- `1`: usage/argument error
- `2`: parse error
- `3`: compile error
- `4`: validation error
- `5`: render/export IO error
- `70`: internal error

## 9) Validation Rules (v0.1)

This section summarizes the normative rules in `docs/specs/core_language.md`.

Current semantic constraints include:

- Exactly one `start` node
- At least one `end` node
- All transition endpoints must resolve to declared node IDs
- Every non-`start` node must have at least one predecessor
- Every non-`end` node must have at least one successor
- Every node reachable from `start`
- Every node can reach at least one `end`
- Every `decision` has at least two outgoing transitions
- `parallel_split` nodes need at least two outgoing edges and must reach a `parallel_join`
- `parallel_join` nodes need at least two incoming edges and must be reachable from a `parallel_split`
- Canonical `consumes` and `produces` references must resolve to declared `items` when `items` are present
- Canonical `performed_by` and `uses` references must resolve to declared `resources` with the correct kind when `resources` are present
- `handoff` must be boolean in the structural edge contract
- `wait_time` is only valid on `queue` nodes
- Queue nodes must not carry active work or setup-time fields such as `cycle_time` or `crossover_time`

## 10) Diagrams and Rendering

Preferred maintained SVG rendering:

```bash
uv run flo render examples/reference/new_semantics.flo \
  --export svg \
  --render-to /tmp/new_semantics.svg \
  --diagram sppm
```

Swimlane rendering:

```bash
uv run flo render examples/reference/swimlane.flo \
  --export svg \
  --render-to /tmp/swimlane.svg \
  --diagram swimlane
```

## 11) Build All Example Artifacts

Regenerate curated render artifacts for all examples:

```bash
uv run python scripts/build_all.py
```

Include intentionally invalid fixtures:

```bash
uv run python scripts/build_all.py --include-invalid
```

Output is written under `renders/` with the same relative structure as `examples/`.

The build includes default and variant SVG artifacts, including chocolate chip cookie variants:

- `renders/reference/chocolate_chip_cookies.svg`
- top-to-bottom orientation: `renders/reference/chocolate_chip_cookies_tb.svg`

## 12) Common Workflows

## 12.1 Author and validate quickly

```bash
uv run flo validate path/to/model.flo
```

## 12.2 Generate diagram for review

```bash
uv run flo render path/to/model.flo --export svg --render-to review.svg --diagram sppm
```

## 12.3 Inspect declared timing or structure before interpreting a diagram

```bash
uv run flo inspect path/to/model.flo
uv run flo inspect path/to/model.flo --analysis structure
uv run flo inspect path/to/model.flo --analysis model --for-diagram spaghetti
```

## 12.4 Generate machine-readable JSON for downstream tooling

```bash
uv run flo export path/to/model.flo -o model.json
```

## 13) Troubleshooting

Problem: "Render options ... require a diagram render output"

- Cause: diagram render flags were used with JSON, ingredients, or movement export.
- Fix: remove render flags or switch to `--export svg`.

Problem: validation errors like missing predecessor/successor

- Cause: disconnected or dangling nodes.
- Fix: ensure every non-start has incoming flow and every non-end has outgoing flow.

## 14) Reference Files

Useful project references:

- `README.md`
- `docs/specs/cli_error_contract.md`
- `docs/specs/core_language.md`
- `docs/design/history/IR.md`
- `schema/flo_ir.json`
- `examples/README.md`
