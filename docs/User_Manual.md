# FLO User Manual

This manual explains how to write FLO models, validate them, and generate outputs for visualization and automation.

## 1) What FLO Is

FLO is a domain-specific, declarative language for modeling business processes.

FLO provides:
- Deterministic compilation to canonical IR
- Structural and semantic validation
- DOT and JSON exports
- Flowchart, swimlane, spaghetti-map, and SPPM DOT projections

FLO does not provide:
- Workflow execution
- Scheduling or orchestration
- Runtime simulation

## 2) Requirements

- Python 3.14+
- Graphviz `dot` (optional, only needed for SVG generation)

## 3) Install and Run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run FLO on a file (default output is DOT to stdout):

```bash
flo examples/reference/linear.flo
```

You can also use explicit subcommands:

```bash
flo run examples/reference/linear.flo
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

transitions:
  - source: start
    target: collect_docs
  - source: collect_docs
    target: finish
```

Notes:
- Use stable `id` values because transitions and diagnostics reference them.
- `decision` steps should define outcomes to branch flow.

## 4.1) Terminology

FLO enables us to represent a business process as a [directed graph](https://en.wikipedia.org/wiki/Directed_graph#:~:text=In%20mathematics%2C%20and%20more%20specifically%20in%20graph,edges%2C%20often%20called%20arcs.%20A%20directed%20graph.).
Each node in the graph represents a *step* in the process and we join the steps together with *transitions*.

## 4.1.1) File Composition (Includes)

Large models can be split into multiple files with top-level include directives.

Extension convention:
- Use `.flo` for both entry files and included fragments.
- Parsing is extension-agnostic: any included file that contains a valid YAML mapping is accepted.

Supported include keys:
- `includes`: list of file paths
- `include`: single file path (alias)

Paths are resolved relative to the current file.

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

## 4.2) Node Kinds

The current schema-aligned node kinds are:

- `start`: the single process entry point
- `task`: a general human or system work step
- `system_task`: an explicitly system-owned task
- `queue`: a queue/buffer step (requires queue metadata in current validation)
- `wait`: an explicit wait/hold step (rendered with a dedicated wait symbol)
- `decision`: a branch point with at least two outgoing transitions
- `subprocess`: a collapsed child-process step
- `end`: a terminal step

Optional common node fields:
- `name`: display label for the node
- `lane`: swimlane grouping key
- `location`: location ID for spatial/movement analysis
- `workers`: optional list of worker IDs used by the step
- `equipment`: optional list of equipment IDs used by the step
- `note`: short human note for review/context (rendered only when notes are enabled)
- `inputs`: list of input item IDs/names consumed by the step
- `outputs`: list of output item IDs/names produced by the step
- `subnodes`: optional nested step list for `subprocess` nodes (flattened during compilation)
- `metadata`: machine-facing metadata map (see below for recognized keys)

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

transitions:
  - source: start
    target: prep
  - source: prep
    target: gather
  - source: gather
    target: mix
  - source: mix
    target: end
```

Time-related node metadata fields (for example `cycle_time`, `wait_time`, `lead_time`) should use:

- `value`: number >= 0
- `unit`: one of `s`, `min`, `hr`, `d` (`m` is still accepted for backwards compatibility)

The `value_class` field classifies a step by its Lean value contribution:

- `VA` — value-adding
- `RNVA` — required non-value-adding
- `NVA` — non-value-adding
- `unknown` — unclassified (default when omitted)

The `description` field is a free-text string providing a human-readable explanation of what the step does. It is displayed in the SPPM info box and is available as a pass-through field in other renderers.

The following metadata keys are recognized and validated by FLO. Any other keys are passed through to the IR without validation and can be used for custom tooling.

| Key | Type | Description |
|---|---|---|
| `cycle_time` | time object | Active processing time for the step |
| `wait_time` | time object | Idle time before the step begins |
| `lead_time` | time object | Total elapsed time including wait |
| `value_class` | `VA`\|`RNVA`\|`NVA`\|`unknown` | Lean value classification |
| `description` | string | Human-readable explanation of the step |
| `queue_policy` | string | Queue discipline (e.g. `fifo`, `lifo`) — `queue` nodes |
| `buffer_capacity` | integer | Maximum queue depth — `queue` nodes |

Example with both fields:

```yaml
steps:
  - id: wash
    kind: task
    name: Wash
    workers:
      - Staff
    metadata:
      value_class: VA
      cycle_time:
        value: 30
        unit: min
      wait_time:
        value: 18
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

## 4.3) Transition Forms

FLO supports these transition forms:

- Explicit transition list: `transitions` with `source` and `target`
- Outcome transitions from decisions: `outcomes` mapping under a `decision` step
- Optional transition labels: `outcome` and/or `label` fields
- Optional transition metadata: `metadata` object on each transition

Examples:

```yaml
transitions:
  - source: start
    target: assess
  - source: assess
    target: approve
    outcome: approved
  - source: assess
    target: reject
    outcome: rejected
  - source: reject
    target: end
    label: "stop process"
    metadata:
      handoff: true
```

Decision-outcome form:

```yaml
steps:
  - id: approved
    kind: decision
    name: Approved?
    outcomes:
      yes: finish
      no: collect_docs
```

## 4.4) Process Metadata, Materials, Equipment, Locations, and Workers

Process-level KPI and resource data should be stored in metadata.

- Canonical IR location: `process.metadata`
- Recommended place for KPIs: `process.metadata` (for example cycle time, yield)
- Top-level `materials`, `equipment`, `locations`, and `workers` collections are supported in FLO source and are preserved under `process.metadata` in the exported schema JSON.
- A resource collection can be either:
  - A flat list of resource items.
  - A grouped object where each key maps to another collection (list or grouped object). This allows nested grouping.
- Grouped objects can include an optional `name` field for a human-readable label.

For material quantities, use one of two quantity shapes:

- Discrete count: `kind: count`, integer `value`, `unit: each` (optional `qualifier`, for example `large`)
- Continuous SI-style measure: `kind: measure`, numeric `value`, and metric `unit` from `mg|g|kg|ml|l|mm|cm|m`

The same quantity contract can be used for `equipment` and `workers` when counts or measured quantities are useful. `locations` can include quantity, but most models use IDs, names, and location metadata.

For spatial analysis and spaghetti-map rendering, locations can include optional spatial coordinates:

- `metadata.spatial.x`: numeric x coordinate
- `metadata.spatial.y`: numeric y coordinate
- `metadata.spatial.unit`: optional unit (`mm|cm|m|in|ft`)
- `kind`: optional semantic location kind used for spaghetti-map shape styling

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

Grouping example for materials:

```yaml
materials:
  dry:
    name: Dry Ingredients
    items:
      - id: flour
        name: Flour
        quantity:
          kind: measure
          value: 250
          unit: g
      - id: sugar
        name: Sugar
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
          quantity:
            kind: measure
            value: 100
            unit: g
    eggs:
      name: Eggs
      items:
        - id: egg
          name: Egg
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

materials:
  - id: egg
    name: Egg
    quantity:
      kind: count
      value: 2
      unit: each
      qualifier: large
  - id: flour
    name: Flour
    quantity:
      kind: measure
      value: 250
      unit: g
      canonical_value: 0.25
      canonical_unit: kg

equipment:
  - id: oven
    name: Convection Oven
    quantity:
      kind: count
      value: 1
      unit: each

locations:
  - id: main_kitchen
    name: Main Kitchen
    metadata:
      site_code: HQ-01

workers:
  - id: baker
    name: Baker
    quantity:
      kind: count
      value: 1
      unit: each

steps:
  - id: start
    kind: start
  - id: end
    kind: end

transitions:
  - source: start
    target: end
```

## 4.5) Diagram Types and When to Use Them

FLO can render a process model as several different diagram types, each suited to a different analysis goal:

| Diagram | Flag | Best for |
|---|---|---|
| Flowchart | `--diagram flowchart` (default) | General process documentation, decision flows |
| Swimlane | `--diagram swimlane` | Handoff analysis — requires `lane` on steps |
| Spaghetti map | `--diagram spaghetti` | Movement/travel path analysis — requires `location` on steps |
| SPPM | `--diagram sppm` | Lean process performance — uses `value_class`, `cycle_time`, `wait_time`, `workers` |

### SPPM (Standard Process Performance Map)

SPPM renders a left-to-right (or top-to-bottom with `--orientation tb`) process map where each step is color-coded by its Lean value classification:

- **Green** — Value-adding (`VA`)
- **Yellow** — Required non-value-adding (`RNVA`)
- **Red** — Non-value-adding (`NVA`)

Each step node has a colored header (the step name) and a white info sub-box showing: description, cycle time, workers, and wait time — whichever are populated.

SPPM-relevant fields per step:
- `metadata.value_class`: controls node color
- `metadata.cycle_time`: shown in info box as `CT:`
- `metadata.wait_time`: shown in info box as `WT:`
- `metadata.description`: shown as the first line of the info box
- `workers`: shown as `Workers:` in info box

The default theme uses stoplight colors. Alternative themes:
- `--sppm-theme print` — high-contrast fills suitable for black-and-white printing
- `--sppm-theme monochrome` — grayscale only

SPPM DOT output must be piped through Graphviz `dot` to produce an image:

```bash
flo run washnfold.flo --diagram sppm | dot -Tpng -o washnfold.png
flo run washnfold.flo --diagram sppm --orientation tb | dot -Tsvg -o washnfold.svg
```

## 4.6) Understanding the Output Pipeline

All `--export dot` (and default) output is Graphviz DOT source — plain text describing a graph. To produce an image you must pipe it through the `dot` program from the Graphviz package:

```bash
# PNG
flo run model.flo | dot -Tpng -o output.png

# SVG (scales cleanly for web/PDF)
flo run model.flo | dot -Tsvg -o output.svg

# Write DOT to file directly
flo run model.flo -o output.dot
```

`flo compile` emits canonical schema-shaped JSON (FLO IR) — useful for downstream tools that consume the structured graph rather than an image.

`flo export --export json` is equivalent to `flo compile`.

## 5) Core CLI Commands

For composed models, keep entry and included files as `.flo` files; see Section 4.1.1 for include conventions.

## 5.1 Run

Parse, compile, validate, and render/export output.

```bash
flo run path/to/model.flo
```

Equivalent shorthand:

```bash
flo path/to/model.flo
```

## 5.2 Validate

Only validate model correctness.

```bash
flo validate path/to/model.flo
```

## 5.3 Compile

Compile to canonical schema-shaped JSON.

```bash
flo compile path/to/model.flo
```

## 5.4 Export

Export as DOT, JSON, ingredients text, or inferred movement report.

```bash
flo export path/to/model.flo --export dot
flo export path/to/model.flo --export json
flo export path/to/model.flo --export ingredients
flo export path/to/model.flo --export movement
```

## 6) Options

Common options:
- `-o, --output <file>`: write output to file
- `-v, --verbose`: verbose logging
- `--export {dot,json,ingredients,movement}`: choose output format

Render options (DOT only):
- `--diagram {flowchart,swimlane,spaghetti,sppm}`
- `--spaghetti-channel {both,material,people}`
- `--spaghetti-people-mode {worker,aggregate}`
- `--sppm-theme {default,print,monochrome}`
- `--layout-wrap {auto,off}`
- `--sppm-step-numbering {off,node,edge}`
- `--sppm-label-density {full,compact,teaching}`
- `--sppm-wrap-strategy {word,balanced,hard}`
- `--sppm-truncation-policy {ellipsis,clip,none}`
- `--layout-max-width-px <int>` (positive integer)
- `--layout-target-columns <int>` (positive integer)
- `--sppm-max-label-step-name <int>` (positive integer)
- `--sppm-max-label-workers <int>` (positive integer)
- `--sppm-max-label-ctwt <int>` (positive integer)
- `--sppm-output-profile {default,book,web,print,slide}`
- `--profile {default,analysis}`
- `--detail {summary,standard,verbose}`
- `--orientation {lr,tb}`
- `--show-notes`
- `--subprocess-view {expanded,parent-only}`
- `--render-to <file>`: render directly to an image file via Graphviz `dot` (e.g. `output.png`, `output.svg`, `output.pdf`). Requires Graphviz to be installed. Supported extensions: `.png`, `.svg`, `.pdf`, `.eps`, `.ps`. When used, nothing is written to stdout.

Examples:

```bash
flo run examples/reference/swimlane.flo --export dot --diagram swimlane
flo run examples/reference/linear.flo --export dot --detail summary
flo run examples/reference/linear.flo --export dot --orientation tb
flo run examples/reference/chocolate_chip_cookies.flo --export dot --subprocess-view parent-only
flo run examples/reference/chocolate_chip_cookies.flo --export dot --diagram spaghetti
flo run examples/reference/chocolate_chip_cookies.flo --export dot --diagram spaghetti --spaghetti-channel people
flo run examples/reference/chocolate_chip_cookies.flo --export dot --diagram spaghetti --spaghetti-channel people --spaghetti-people-mode worker --profile analysis
flo run examples/reference/washnfold.flo --export dot --diagram sppm
flo run examples/reference/washnfold.flo --export dot --diagram sppm --sppm-theme print
flo run examples/reference/washnfold.flo --export dot --diagram sppm --orientation lr --layout-wrap auto --layout-target-columns 6
flo run examples/reference/washnfold.flo --export dot --diagram sppm --orientation tb --layout-wrap auto --layout-target-columns 5
flo run examples/reference/washnfold.flo --diagram sppm --render-to washnfold_sppm.png
flo run examples/reference/washnfold.flo --diagram sppm --render-to washnfold_sppm.svg
flo run examples/reference/linear.flo --export json
flo run examples/reference/chocolate_chip_cookies.flo --export ingredients
flo run examples/reference/chocolate_chip_cookies.flo --export movement
```

Important:
- Render-only flags are invalid with non-DOT export modes.
- If you pass render-only flags (`--diagram`, `--spaghetti-channel`, `--spaghetti-people-mode`, `--layout-wrap`, `--layout-max-width-px`, `--layout-target-columns`, any `--sppm-*` render option, `--render-to`, `--profile`, `--detail`, `--orientation`, `--show-notes`, or `--subprocess-view`) together with JSON, ingredients, or movement export, FLO returns usage error code `1`.
- Wrapped SPPM layout is orientation-aware: with `--orientation lr` it wraps into rows (snake down), and with `--orientation tb` it wraps into columns (snake right).

Renderer policy decisions:
- Rework edges are always dashed.
- Rework classification precedence is explicit metadata first (`rework` boolean,
  then `edge_type: rework`), inferred back-edge fallback second.
- Cross-lane rework uses composite behavior (cross-lane routing + dashed styling).
- Layout fit modes are policy-defined as fit-preferred and fit-strict; readability
  is prioritized over geometric symmetry.

SPPM preset/config defaults:
- Built-in `--sppm-output-profile` presets set baseline SPPM defaults for orientation,
  wrapping, and density (`book`, `web`, `print`, `slide`).
- If a `diagrams.toml` file exists beside the source `.flo` file (or in the current
  working directory), FLO loads `[sppm]` defaults automatically.
- Precedence is: CLI flags > `diagrams.toml` explicit `[sppm]` keys >
  `diagrams.toml` preset overrides (`[sppm.presets.<profile>]`) > built-in profile defaults.

## 7) Input and Output Streams

FLO supports POSIX-style streams:

- Input path `-` means read from stdin
- Output path `-` means write to stdout

Examples:

```bash
cat examples/reference/linear.flo | flo -
flo run examples/reference/linear.flo -o -
```

## 8) Exit Codes

- `0`: success
- `1`: usage/argument error
- `2`: parse error
- `3`: compile error
- `4`: validation error
- `5`: render/export IO error
- `70`: internal error

## 9) Validation Rules (v0.1)

Current semantic constraints include:
- Exactly one `start` node
- At least one `end` node
- All transition endpoints must resolve to declared node IDs
- Every non-`start` node must have at least one predecessor
- Every non-`end` node must have at least one successor
- Every node reachable from `start`
- Every node can reach at least one `end`
- Every `decision` has at least two outgoing transitions

## 10) Diagrams and Rendering

DOT output can be rendered to SVG with Graphviz:

```bash
flo run examples/reference/linear.flo --export dot -o /tmp/linear.dot
dot -Tsvg /tmp/linear.dot -o /tmp/linear.svg
```

Swimlane rendering:

```bash
flo run examples/reference/swimlane.flo --export dot --diagram swimlane -o /tmp/swimlane.dot
dot -Tsvg /tmp/swimlane.dot -o /tmp/swimlane.svg
```

## 11) Build All Example Artifacts

Regenerate DOT/SVG for all examples:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_all.py
```

Include intentionally invalid fixtures:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_all.py --include-invalid
```

Output is written under `renders/` with the same relative structure as `examples/`.

The build includes both the default and top-down chocolate chip cookie artifacts:
- `renders/reference/chocolate_chip_cookies.dot`
- `renders/reference/chocolate_chip_cookies.svg`
- `renders/reference/chocolate_chip_cookies_topdown.dot`
- `renders/reference/chocolate_chip_cookies_topdown.svg`

## 12) Common Workflows

## 12.1 Author and validate quickly

```bash
flo validate path/to/model.flo
```

## 12.2 Generate diagram for review

```bash
flo run path/to/model.flo --export dot --diagram flowchart -o review.dot
dot -Tsvg review.dot -o review.svg
```

## 12.3 Generate machine-readable JSON for downstream tooling

```bash
flo export path/to/model.flo --export json -o model.json
```

## 13) Troubleshooting

Problem: "Render options ... require DOT output"
- Cause: DOT-only flags were used with JSON export.
- Fix: remove render flags or switch to `--export dot`.

Problem: validation errors like missing predecessor/successor
- Cause: disconnected or dangling nodes.
- Fix: ensure every non-start has incoming flow and every non-end has outgoing flow.

Problem: SVG not generated
- Cause: Graphviz `dot` is missing.
- Fix: install Graphviz and re-run render command.

## 14) Reference Files

Useful project references:
- `README.md`
- `docs/CLI_Error_Contract.md`
- `docs/design/IR.md`
- `schema/flo_ir.json`
- `examples/README.md`

---

If you want, the next revision can be split into two manuals:
- A short Quickstart (2-3 pages)
- A full Reference Guide (complete command and schema details)
