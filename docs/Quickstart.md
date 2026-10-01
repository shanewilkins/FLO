# FLO Quickstart

This guide gets you from installation to a validated model, a reviewable SVG,
and canonical JSON. For the complete language and CLI reference, use
`docs/User_Manual.md`.

## 1. Install FLO

Install the released FLO package without cloning the repository:

- Python 3.14+
- Node.js 26
- `uv`

```bash
python3.14 --version
node --version
uv --version
uv tool install flo-lang
flo --version
```

FLO ships its pinned ELK JavaScript bundle in the Python package and executes
that bundle with the local Node.js runtime. End users do not need `npm`, an
`npm install`, or a repository checkout.

The following commands use the installed `flo` tool and work from any directory.

To contribute to FLO or run unreleased source, use the repository development
environment instead:

```bash
npm ci --ignore-scripts --no-audit --no-fund
uv sync --dev
```

## 2. Create a process

Create a valid starter model with explicit stable IDs:

```bash
flo new onboarding.flo --name "Client Onboarding"
```

Choose a specialized starting point with `--template`:

```bash
flo new approval.flo --name "Expense Approval" --template decision
```

Maintained templates are `simple-process`, `linear-flow`, `decision`,
`handoff`, `rework`, and `value-stream`.

List templates without creating a file:

```bash
flo new --list-templates
```

Preview the target path before writing, and use `--force` only when you intend
to replace an existing file:

```bash
flo new onboarding.flo --dry-run
flo new onboarding.flo --force
```

The generated file is ordinary YAML-shaped plain text:

```yaml
spec_version: "0.1"

process:
  id: client_onboarding
  name: Client Onboarding

steps:
  - id: start
    kind: start
    name: Start

  - id: receive_request
    kind: task
    name: Receive Request

  - id: complete_work
    kind: task
    name: Complete Work

  - id: finish
    kind: end
    name: Complete
```

Change the process and task names to match your work. FLO connects adjacent
steps automatically. Keep IDs stable after other tools or people begin
referring to the model; transitions, diagnostics, and future telemetry
alignment use them.

## 3. Validate

```bash
flo validate onboarding.flo
```

Validation checks process structure, references, branching, reachability, and
typed semantic rules. A successful command exits with code `0`.

## 4. Render an SVG

Create the default readable SPPM SVG used by the White Belt journey:

```bash
flo render onboarding.flo --render-to onboarding.svg
```

Geometry is optional and belongs to each render command. For example, request
an image that is exactly 6 inches wide and 4 inches tall:

```bash
flo render onboarding.flo \
  --layout-width 6in \
  --layout-height 4in \
  --render-to onboarding-6x4.svg
```

FLO accepts `px`, `in`, `cm`, and `mm`. When both dimensions are present, they
define the exact SVG canvas. When only one is present, FLO derives the other
from the rendered aspect ratio. Omitting both keeps the renderer's natural
size. These choices apply only to that render unless saved separately as render
intent.

For the White Belt PDF, the same controls request an exact US Letter canvas:

```bash
flo render onboarding.flo \
  --layout-width 8.5in \
  --layout-height 11in \
  --render-to onboarding-letter.svg
```

For responsive HTML, retain the SVG `viewBox` and set its displayed width in
the page stylesheet. SPPM reflows before scaling, preserves aspect ratio, and
fails rather than shrinking below its `0.75` legibility floor. Use
`--layout-overflow scale` only when deliberate unrestricted shrinking is
acceptable, or `--layout-overflow expand` when the canvas may grow.

Use an explicit diagram when a particular review surface is needed:

```bash
flo render onboarding.flo \
  --diagram swimlane \
  --render-to onboarding-swimlane.svg
```

## 5. Export canonical JSON

```bash
flo export onboarding.flo -o onboarding.json
```

The JSON output is aligned to `schema/flo_ir.json` and is the canonical
machine-readable interchange artifact.

## 6. Use FLO from Python

Use the supported `flo` package facade when a Python tool needs to work with a
model without scraping CLI output or importing private modules:

```python
from flo import export, validate

source = open("onboarding.flo", encoding="utf-8").read()
result = validate(source, source_path="onboarding.flo")
if result.ok:
  payload = export(source, source_path="onboarding.flo")
else:
  for diagnostic in result.diagnostics:
    print(diagnostic.message)
```

The facade provides `parse`, `compile`, `validate`, `inspect`, and `export`.
Each returns an `OperationResult` with either a typed value or structured
diagnostics.

## 7. Model waiting correctly

Queue delay and active work are different process facts. Put `wait_time` on a
queue node and `cycle_time` on the work node:

```yaml
steps:
  - id: review_queue
    kind: queue
    name: Review Queue
    metadata:
      wait_time: {value: 30, unit: min}

  - id: review_documents
    kind: task
    name: Review Documents
    metadata:
      cycle_time: {value: 10, unit: min}
```

FLO rejects `wait_time` on task-like nodes.

## 8. Use files in pipelines

Input `-` means stdin and output `-` means stdout:

```bash
cat onboarding.flo | flo export - -o -
```

Diagnostics and logging stay off payload stdout.

## 9. Next references

- Complete language and CLI reference: `docs/User_Manual.md`
- Normative requirements: `docs/requirements/`
- Core language semantics: `docs/specs/core_language.md`
- CLI and error contract: `docs/specs/cli_error_contract.md`
- Diagram specifications: `docs/specs/`
- Roadmap to 1.0: `docs/ROADMAP.md`
