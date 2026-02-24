# Changelog

## Unreleased

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

