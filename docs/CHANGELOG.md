# Changelog

## Unreleased

- Add `--render-to <file>` convenience flag: renders DOT output directly to an
  image file (PNG, SVG, PDF, EPS, PS) via the system Graphviz `dot` binary,
  avoiding the need for a manual pipe. Reports a clear error if Graphviz is not
  installed. When `--render-to` is used, nothing is written to stdout.

- Add SPPM (Standard Process Performance Map) diagram renderer (`--diagram sppm`):
  color-coded nodes by `value_class` (VA/RNVA/NVA), cycle time and worker labels,
  wait time as edge labels, rounded-rectangle start/end nodes, left-to-right layout.

- Add `ProcessValueClass` enum (`VA`, `RNVA`, `NVA`, `unknown`) to
  `flo.compiler.ir.enums`; validation now rejects invalid `value_class` values
  with error `E1320`.

- Add SPPM color themes (`--sppm-theme default|print|monochrome`) backed by
  `SppmTheme` / `SppmNodeStyle` dataclasses in `_sppm_themes.py`; themes are
  resolved via `resolve_sppm_theme()` and decoupled from the renderer.

- Add `examples/reference/washnfold.flo` — Wash n' Fold process reference example
  with full `value_class`, `cycle_time`, `wait_time`, and `workers` annotations.

- Remove the temporary IR->schema translator: the compiler now emits the
  schema-shaped canonical IR directly. CI and the runtime enforce the
  JSON Schema contract (`schema/flo_ir.json`) and will fail on
  non-conforming output.

- Enforce schema-shaped IR across the pipeline: added `ensure_schema_aligned`
  and updated `scripts/validate_ir_schema.py` to fail when examples are not
  schema-aligned.

- Tests and CI updates: refactored tests to rely on the canonical IR output,
  tightened telemetry tests, cleaned the `vulture` whitelist, and updated
  CI to validate example IRs against the schema.

- Remove the `Hello world!` placeholder output from the core/main paths;
  the program now returns the rendered DOT text (or an empty string for
  empty input) which simplifies the CLI and test expectations.

