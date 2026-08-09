# FLO Quickstart

This guide gets you from installation to a validated model, a reviewable SVG,
and canonical JSON. For the complete language and CLI reference, use
`docs/User_Manual.md`.

## 1. Requirements

The current pre-0.4 quickstart uses the repository development environment.
FLO 0.4 will add the end-user tool-install path defined by the MVP requirements;
that future path will not require a repository checkout.

- Python 3.14+
- `uv`

From the repository root, install the development environment:

```bash
uv sync --dev
```

## 2. Create a process

Save this as `onboarding.flo`:

```yaml
spec_version: "0.1"

process:
  id: onboarding
  name: Client Onboarding

resources:
  - id: coordinator
    name: Onboarding Coordinator
    kind: person

steps:
  - id: start
    kind: start
    name: Start

  - id: collect_documents
    kind: task
    name: Collect Documents
    performed_by: [coordinator]

  - id: review
    kind: decision
    name: Complete?
    outcomes:
      yes: finish
      no: collect_documents

  - id: finish
    kind: end
    name: Complete
```

FLO normally connects adjacent steps automatically. Decision outcomes create
their labeled branches. Stable IDs matter because transitions, diagnostics,
and future telemetry alignment refer to them.

## 3. Validate

```bash
uv run flo validate onboarding.flo
```

Validation checks process structure, references, branching, reachability, and
typed semantic rules. A successful command exits with code `0`.

## 4. Render an SVG

Use SPPM for a rich process map:

```bash
uv run flo render onboarding.flo \
  --diagram sppm \
  --export svg \
  --render-to onboarding.svg
```

Use swimlane when responsibility lanes are the primary review surface:

```bash
uv run flo render onboarding.flo \
  --diagram swimlane \
  --export svg \
  --render-to onboarding-swimlane.svg
```

## 5. Export canonical JSON

```bash
uv run flo export onboarding.flo -o onboarding.json
```

The JSON output is aligned to `schema/flo_ir.json` and is the canonical
machine-readable interchange artifact.

## 6. Model waiting correctly

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

## 7. Use files in pipelines

Input `-` means stdin and output `-` means stdout:

```bash
cat onboarding.flo | uv run flo export - -o -
```

Diagnostics and logging stay off payload stdout.

## 8. Next references

- Complete language and CLI reference: `docs/User_Manual.md`
- Normative requirements: `docs/requirements/`
- Core language semantics: `docs/specs/core_language.md`
- CLI and error contract: `docs/specs/cli_error_contract.md`
- Diagram specifications: `docs/specs/`
- Roadmap to 1.0: `docs/ROADMAP.md`
