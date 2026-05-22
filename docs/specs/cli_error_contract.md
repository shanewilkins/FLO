# FLO CLI Error Contract

Purpose: define the normative CLI-facing error classes, exit-code meanings, and
stream/output behavior for FLO commands.

## Error class hierarchy

Implemented in `src/flo/services/errors.py`:

- `DomainError`
  - Base class for expected domain-level errors.
- `CLIError`
  - CLI-facing error wrapper with exit code mapping.
- `ParseError`
  - Parse/loading failures.
- `CompileError`
  - Adapter-to-model compilation failures.
- `ValidationError`
  - Semantic/schema validation failures.
- `RenderError`
  - Output rendering failures.

## Exit codes

Current mappings:

- `0` (`EXIT_SUCCESS`): success
- `1` (`EXIT_USAGE`): CLI usage or argument issues
- `2` (`EXIT_PARSE_ERROR`): parse error
- `3` (`EXIT_COMPILE_ERROR`): compile error
- `4` (`EXIT_VALIDATION_ERROR`): validation error
- `5` (`EXIT_RENDER_ERROR`): render or export I/O/rendering error
- `70` (`EXIT_INTERNAL_ERROR`): unexpected internal failure

## Stream conventions

- Primary command output and artifacts are written to `stdout` unless an
  explicit output destination is used.
- Diagnostics and errors are written through the CLI error path, which is
  `stderr`-oriented.
- Telemetry or logging output must not be emitted on `stdout` when commands
  return payloads such as DOT or JSON.
- Input `-` means read from `stdin`.
- Output `-` means write to `stdout`.

## Render vs export contract

- Renderers and exporters are separate concerns and use separate registries.
  - Renderers (human-readable visualization) live under `src/flo/render`.
  - Exporters (machine-readable or report-style projections) live under
    `src/flo/export`.
- `--diagram` supports `flowchart`, `swimlane`, `spaghetti`, and `sppm` for
  render output.
- `--profile`, `--detail`, `--orientation`, `--show-notes`,
  `--subprocess-view`, shared autoformat controls (`--layout-wrap`,
  `--layout-max-width-px`, `--layout-target-columns`), and all SPPM render
  controls are render-only options.
- If `--export json`, `--export ingredients`, or `--export movement` is
  selected, render-only options are rejected with usage exit code `1`.

## Renderer policy contract (pre-1.0)

- Rework edges render as dashed lines.
- Rework classification precedence is explicit metadata first, inferred back-edge
  fallback second.
- Explicit rework semantics override inferred classification when they differ.

## Validation diagnostics

Semantic validation uses stable diagnostic-style prefixes in messages (for
example `E1003`, `E1101`) so failures are easier to script against and triage.

## Projection capability diagnostics

Unsupported diagram/backend projection requests are usage errors and must:

- return exit code `1` (`EXIT_USAGE`)
- include requested diagram and backend
- include supported backends for the requested diagram
- fail early before renderer dispatch

## Relationship to other documents

- Core language semantics live in `docs/specs/core_language.md`.
- Diagram meaning lives in the other files under `docs/specs/`.
- This contract is the normative CLI/interface companion to the implementation
  in `src/flo/services/errors.py`.