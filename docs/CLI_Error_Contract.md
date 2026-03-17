# FLO CLI Error Contract (v0.1 draft)

This document defines the current error classes and exit code behavior for the FLO CLI.

## Error class hierarchy

Implemented in [src/flo/services/errors.py](../src/flo/services/errors.py):

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
- `1` (`EXIT_USAGE`): CLI usage/argument issues
- `2` (`EXIT_PARSE_ERROR`): parse error
- `3` (`EXIT_COMPILE_ERROR`): compile error
- `4` (`EXIT_VALIDATION_ERROR`): validation error
- `5` (`EXIT_RENDER_ERROR`): render/export IO or rendering error
- `70` (`EXIT_INTERNAL_ERROR`): unexpected internal failure

## Stream conventions (POSIX style)

- Primary command output/artifacts are written to `stdout`.
- Diagnostics/errors are written via CLI error handling (stderr-oriented logging path).
- Input `-` means read from `stdin`.
- Output `-` means write to `stdout`.

## Render vs export contract

- Renderers and exporters are separate concerns and use separate registries.
  - Renderers (human-readable visualization) live under [src/flo/render](../src/flo/render).
  - Exporters (machine-readable projection) live under [src/flo/export](../src/flo/export).
- `--diagram` supports `flowchart`, `swimlane`, and `spaghetti` for **DOT render** output.
- `--profile`, `--detail`, `--orientation`, `--show-notes`, and `--subprocess-view` are **DOT render** options.
- If `--export json`, `--export ingredients`, or `--export movement` is selected, render-only options are rejected with usage exit code `1`.

## Validation diagnostics

Semantic validation uses stable diagnostic-style prefixes in messages (e.g., `E1003`, `E1101`) to make failures easier to script against and triage.

## Notes

- JSON is an export format of the in-memory model, not the canonical IR itself.
- This is a lightweight v0.1 contract doc and may be expanded into full CLI reference docs later.
