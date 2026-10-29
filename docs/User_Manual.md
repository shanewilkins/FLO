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
- Node.js 26 (used by direct SVG layout)
- `uv` (recommended installer and developer environment manager)

## 3) Install and Run

Install the released command without cloning the repository:

```bash
python3.14 --version
node --version
uv --version
uv tool install flo-lang
flo --version
```

The package contains the pinned ELK JavaScript bundle. Rendering invokes it
through the local Node.js runtime; end users do not need `npm` or a separate
JavaScript dependency installation.

To contribute or run unreleased source, start from the repository root:

```bash
npm ci --ignore-scripts --no-audit --no-fund
uv sync --dev
```

Run FLO on a file. The default output is an SPPM SVG written to stdout:

```bash
flo examples/reference/linear.flo
```

Preferred modern entry points:

```bash
flo export examples/reference/new_semantics.flo -o new_semantics.json
flo render examples/reference/new_semantics.flo --export svg --render-to new_semantics.svg
```

You can also use explicit subcommands:

```bash
flo render examples/reference/linear.flo --diagram sppm
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

Supported kinds are start, task, system_task, queue, wait, decision, branch,
subprocess, parallel_split, parallel_join and end. Work kinds are task,
system_task and subprocess. Each step declares id/kind; optional common fields
include name, description, lane, subprocess_parent and extensions.

Work supports location, consumes, produces, performed_by, uses, value_class,
cycle_time, wait_time and changeover_time. Queue/wait supports location and
wait_time. Control nodes carry control flow and descriptive context only.
See the exhaustive [field inventory](specs/book_aligned_fields.md).

Only subprocesses support nested `steps`; children compile to flattened nodes
with explicit parent links. Other step kinds reject child lists.

```yaml
steps:
  - {id: start, kind: start}
  - id: preparation
    kind: subprocess
    steps:
      - {id: gather, kind: task, name: Gather inputs}
      - {id: mix, kind: task, name: Mix inputs}
  - {id: end, kind: end}
```

Measurement profiles preserve externally calculated statistics:

```yaml
cycle_time:
  basis: observed
  observation_count: 10
  observation_unit: cases
  primary: median
  analysis_input: mean
  results:
    median: {method: median, value: 5, unit: min}
    mean: {method: mean, value: 6, unit: min}
```

Primary selects display evidence; analysis_input selects analytical evidence.
Without analysis_input, a profile does not contribute an inferred analytical
value. Selected durations require explicit supported units s, m, min, hr or d
and finite nonnegative numeric values. Zero is measured; omission is unmeasured.
Only work kinds accept value_class: VA, RNVA, NVA or explicit unknown. Omission
is unclassified. Process lead_time is a separate supplied profile; modeled lead
time belongs to analysis results.

## 4.2.1) Modeling Queues and Process Steps

Use queue/wait for explicit waiting states. Work steps can independently declare
waiting before work and changeover/setup evidence. A queue that displays the
same work waiting evidence uses a direct reference:

```yaml
steps:
  - {id: start, kind: start}
  - id: staging
    kind: queue
    wait_time: {ref: wash.wait_time}
  - id: wash
    kind: task
    wait_time:
      basis: observed
      primary: mean
      analysis_input: mean
      results:
        mean: {method: mean, value: 30, unit: min}
  - {id: end, kind: end}
```

References resolve only to a work step's wait_time profile and cannot chain.
Analysis avoids double contribution when the owning work evidence is on the
same path. Independent waiting profiles remain independent contributions.

## 4.3) Transition Forms

Adjacent steps connect automatically unless local outcomes/routes or an explicit
transitions list declares the flow. Explicit connections use source and target.
A named decision outcome or branch route can name a target string or an object
with target and transition evidence.

```yaml
transitions:
  - source: receive
    target: inspect
    handoff: {type: responsibility}
  - source: inspect
    target: correct
    outcome: rejected
    rework:
      reason: Incomplete information
      frequency:
        basis: observed
        numerator: 2
        denominator: 10
        observation_unit: cases
```

Each decision has at least two distinct named outcomes. A generic branch has
branch.mode (dispatch, probabilistic, external or unspecified) and may declare
named routes. Parallel split/join expresses concurrency instead of selection.
Only decisions carry outcomes; only branches carry route names. Handoff/rework
are objects whose complete supplied evidence survives export and inspection.

## 4.4) Process Context, Items, Resources, and Locations

Collections belong only under process. IDs are unique across flat or nested
groups. Work refers to item IDs through consumes/produces, to person resources
through performed_by, and equipment resources through uses.

```yaml
process:
  id: preparation
  name: Preparation
  owner: {id: ops, name: Operations}
  version: 2
  items:
    - id: flour
      name: Flour
      kind: material
      quantity: {kind: measure, value: 250, unit: g, canonical_value: 0.25, canonical_unit: kg}
  resources:
    - {id: baker, name: Baker, kind: person}
    - {id: mixer, name: Mixer, kind: equipment}
  locations:
    - id: bench
      name: Preparation bench
      spatial: {x: 3, y: 4, unit: m}
```

Item kinds are material/information; resource kinds are person/equipment.
Quantities are positive integral counts or finite positive measured amounts.
Optional canonical amount/unit must describe the same dimension and amount,
using relative tolerance 1e-9 and absolute tolerance 0. Supported measure units
are mg, g, kg, ml, l, mm, cm and m. Spatial units are mm, cm, m, in and ft;
mixed units normalize for movement distances without changing authored data.

Unknown fields fail. Finite JSON annotations belong under extensions. Display
annotations have one supported location: process.extensions.flo:publication for
footer_metrics, footer_notes and publication_date; edge.extensions.flo:continuation
for outgoing/incoming labels; process.extensions.flo:spaghetti.boundary for an
optional area overlay. Owner and version are first-class process context.
Subprocess extensions may use detail_map_ref to label the detail map.

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

- `value_class`: controls node color
- `cycle_time`: shown in info box as `P/T:`
- `wait_time`: shown in info box as `W/T:` (queue nodes)
- `changeover_time`: shown in info box as `S/T:` (task/system_task/subprocess)
- `description`: shown as the first line of the info box
- `performed_by`: shown as the performer line in the info box
- `uses`: available for equipment-aware examples and downstream summaries

Timing fields require an explicit finite, nonnegative numeric `value` and a
supported `unit` (`s`, `m`, `min`, `hr`, or `d`). Omit unmeasured fields; null,
NaN, infinity, numeric strings, and booleans fail validation. Explicit integer
or floating-point zero is a measurement and stays visible in full and compact
metric views. Missing applicable timings display `?` rather than a blank or
zero: work steps show `P/T: ?`, `W/T: ?`, and `S/T: ?`; queues show `W/T: ?`.
Compact cards group missing metrics on their own line. Teaching views retain
their single primary metric. Missing categories in an
existing timing footer also show `?`. Wait labels convert to minutes. An unavailable modeled lead time
appears as `Unavailable` with a reason in `flo inspect`; it is never shown as
zero. Even with complete timing coverage, cycles and parallel flows can leave
modeled lead time unavailable.

Cards display the explicitly selected primary duration. Canonical JSON and model
inspection retain the full profile, including other statistics, selectors,
basis, sample context and evidence references. `flo inspect --analysis timing`
uses analysis_input rather than silently choosing the displayed result.

A richer detailed publication or interactive measurement view remains planned
under UR-080/TR-111. Current diagrams do not claim to display every statistic
or a method-specific label such as a percentile caption.

The default theme uses stoplight colors. Themes use Bootstrap-compatible semantic
roles: `success` for VA, `warning` for RNVA and queues, `danger` for NVA, and
`primary` for decision control points. FLO owns these tokens and does not import
Bootstrap CSS at runtime.

Alternative themes:

- `--sppm-theme flatly` — Flatly-compatible Bootstrap semantic palette
- `--sppm-theme mpi-lms` — MPI publication and LMS semantic palette
- `--sppm-theme print` — high-contrast fills suitable for black-and-white printing
- `--sppm-theme monochrome` — grayscale only
- `--sppm-theme <name>` — any custom theme defined under `[sppm.themes.<name>]` in `diagrams.toml`

The preferred 0.3 interface is the shared `--theme <name>` option. It applies
one central theme to SPPM, swimlane, spaghetti, and value-stream SVG output. Built-ins are
`default`, `flatly`, `mpi-lms`, `print`, and `monochrome`. Direct session overrides are
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

  `flo render --export items` emits human-readable item and resource summaries.
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
uv run flo render examples/reference/new_semantics.flo --export items
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

Export as JSON by default, or choose SVG, Typst publication source, item/resource text, or movement text.

```bash
uv run flo export path/to/model.flo
uv run flo export path/to/model.flo --export items
uv run flo export path/to/model.flo --export movement
uv run flo export path/to/model.flo --export svg
```

SVG is typically requested from `render` when diagram options or `--render-to` are needed.

## 6) Options

Common options:

- `-o, --output <file>`: write text or JSON output to file
- `-v, --verbose`: verbose logging
- `--export {svg,typst,json,items,movement}`: choose output format

Inspect options:

- `--analysis {timing}`: choose the static analysis; timing is the default
- `--format {text,json}`: choose human-readable text or deterministic JSON

Diagram render options:

- `--diagram {swimlane,spaghetti,sppm,value_stream}`
- `--render-backend {svg}`
- `--spaghetti-channel {both,material,people}`
- `--spaghetti-people-mode {worker,aggregate}`
- `--spaghetti-strict-spatial`
- `--sppm-theme {default,flatly,mpi-lms,print,monochrome}` or a config-defined theme name
- `--theme <name>`
- `--background-color <color>`
- `--font-family <family[,fallback...]>`
- `--typography-scale <0.75..1.5>`
- `--layout-wrap {auto,off}`
- `--layout-fit {fit-preferred,fit-strict}`
- `--layout-width <dimension>`
- `--layout-height <dimension>`
- `--layout-overflow {safe-fit,error,expand,scale,paginate}`
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
- Typst pagination currently splits only one unambiguous linear path. Page bands
  identify both the adjacent page and boundary step. A branching, cyclic, or
  otherwise non-linear map stays on one page with a warning under
  `fit-preferred`; `--layout-fit fit-strict` rejects the ambiguous request.
- Raster and PDF output are not emitted directly by FLO; convert SVG with an external tool if needed.

Examples:

```bash
uv run flo render examples/reference/swimlane.flo --export svg --render-to swimlane.svg --diagram swimlane
uv run flo render examples/reference/new_semantics.flo --export json
uv run flo render examples/reference/chocolate_chip_cookies.flo --export items
uv run flo render examples/reference/chocolate_chip_cookies.flo --export movement
uv run flo render examples/reference/washnfold.flo --export svg --render-to washnfold_sppm.svg --diagram sppm --sppm-output-profile book --layout-target-columns 4
uv run flo render examples/reference/washnfold.flo --export typst --render-to washnfold.typ --diagram sppm --layout-overflow paginate --layout-target-columns 4
```

### Direct SVG geometry

`--layout-width` and `--layout-height` apply to one render. They accept positive
values in `px`, `in`, `cm`, or `mm`; bare numbers remain pixel-compatible. Both
dimensions declare an exact SVG canvas. One dimension preserves the natural
aspect ratio by deriving the other, and omitting both retains natural renderer
bounds.

For example, this creates a 6-by-4-inch SVG canvas (576 by 384 pixels at FLO's
96-pixel-per-inch conversion):

```bash
flo render process.flo \
  --layout-width 6in \
  --layout-height 4in \
  --render-to process-6x4.svg
```

Requested SPPM width becomes a reflow constraint before any scaling. The
default `safe-fit` policy preserves aspect ratio and scales only when the result
stays at or above the `0.75` legibility floor. If readable content cannot fit,
FLO returns a render error with the natural bounds, requested bounds, required
scale, and floor. Choose `error` for no scaling, `expand` to let the canvas grow,
or `scale` to allow deliberate shrinking below the floor. `paginate` applies to
composed publication output rather than direct SVG.

Fixed PDF workflows can request a physical page box such as `8.5in` by `11in`.
Responsive HTML should retain the SVG `viewBox` and use CSS to control displayed
width; a fixed canvas is not required for every render.

Important:

- Render-only flags are invalid with JSON, item/resource, or movement export modes.
- If you pass render-only flags together with JSON, item/resource, or movement export, FLO returns usage error code `1`.
- Profile-driven direct-SVG row wrapping applies automatically to unambiguous
  linear LR SPPM sequences. Supplying an explicit `--layout-width` also opts a
  branching or rework map into width-constrained wrapping; rework stays on a
  secondary row below the wrapped mainline.
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
- Rework classification uses the explicit structured relation before any inferred back-edge finding.
- Cross-lane rework uses composite behavior.
- Layout fit modes are policy-defined as fit-preferred and fit-strict.

SPPM preset and config defaults:

- Built-in `--sppm-output-profile` presets set baseline SPPM defaults for orientation, wrapping, density, and named page formats.
- If a `diagrams.toml` file exists beside the source `.flo` file or in the current working directory, FLO loads `[sppm]` defaults automatically.
- Precedence is CLI flags, then the selected `diagrams.toml` preset, then global
  `diagrams.toml` defaults, then built-in defaults.
- FLO checks table structure when reading defaults, then validates effective
  fields after selecting a preset and applying CLI overrides. Unselected presets
  and overridden field values do not block rendering. Malformed configuration
  reports the file and field path as a usage error (exit 1).
  Positive integer settings accept integers, integer strings, and whole-number
  floats such as `6.0`; booleans and fractional numbers are rejected.
  Dimensions accept positive finite values
  with the existing px, in, cm, and mm syntax. Existing option aliases remain
  supported, and unknown configuration keys retain their existing handling.
  Theme contents and typography ranges continue to use the render theme validator.

The same render-input validation and alias normalization apply to CLI/configuration
and Python `RenderOptions.from_mapping` inputs. `RenderOptions` remains an immutable
dataclass inside renderers. Source compilation also validates process context,
recursive step structure, and transition/branch fields through typed models;
nested failures retain their authored field paths and source excerpts. This does
not convert authored numeric strings into process numbers or replace graph and
domain validation.

SPPM label policy matrix:

- `--sppm-wrap-strategy` selects wrapping behavior.
- `--sppm-truncation-policy` selects overflow behavior.
- Task node names, decision labels, subprocess titles, queue badges, decision and branch labels, and publication header and footer text all use `--sppm-max-label-step-name`.
- Performer-line text uses `--sppm-max-label-workers`.
- P/T and W/T metric lines and footer metric values use `--sppm-max-label-ctwt`.

SPPM time semantics:

- `wait_time` models queue delay.
- `changeover_time` models setup or changeover time.
- These metrics are intentionally distinct because they imply different operational problems and different improvement methods.
- Work-step shapes display declared setup or changeover as `S/T`; queue shapes
  display queue delay as `W/T`.
- When timing is declared for the complete visible process, the footer shows
  processing, waiting, setup, and modeled lead time from the same static-analysis
  result used by `flo inspect`. Alternative paths show a range; unresolved
  timing shows `Unavailable` and points to inspect diagnostics.
- Static timing consumes only
  the named `analysis_input` result; it will not calculate descriptive
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
- `handoff` and `rework` use structured relation objects
- `wait_time` carries waiting evidence on work and queue/wait nodes
- Promoted queue waits must reference the work measurements they project
- Queue nodes must not carry active work or setup-time fields such as `cycle_time` or `changeover_time`

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

- Cause: diagram render flags were used with JSON, item/resource, or movement export.
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
