# Changelog

## Unreleased

- Wrapped SPPM SVG boundary routing hardening:
  - Keep DOT route metadata deterministic, then postprocess only wrapped LR
    boundary doglegs in SVG output to enforce the intended path shape
    (right, down, left, centered top-entry drop).
  - This interception is intentionally narrow to address Graphviz orthogonal
    routing behavior that can otherwise produce mid-box or side-biased
    boundary landings despite deterministic DOT hints.

- Breaking (pre-1.0): standardize renderer wrap-planning API to a single
  canonical entrypoint and contract:
  - `build_wrap_plan(nodes, options, planner=...)`
  - `WrapPlan`
  - Legacy public builders removed in favor of explicit planner strategy
    selection (`chunked` or `placement`).

- Document renderer policy decisions and contracts for pre-1.0:
  - shared autoformat controls across diagram styles,
  - rework classification precedence,
  - dashed styling for all rework edges,
  - readability-first alignment/packing policy,
  - composite behavior for cross-lane rework edges.
- Breaking (pre-1.0): migrate autoformat CLI controls from SPPM-specific names
  to shared layout names:
  - `--sppm-wrap-layout` -> `--layout-wrap`
  - `--sppm-max-width-px` -> `--layout-max-width-px`
  - `--sppm-target-columns` -> `--layout-target-columns`

- Add design spec for SPPM layout-width, row wrapping, label density/text controls,
  and output profile presets in `docs/design/SPPM_Layout_Enhancement_Spec.md`.
- Implement Phase 1 foundations:
  - New shared CLI/render option plumbing for autoformat width controls and
    orientation-aware wrap mode (`--layout-wrap`, `--layout-max-width-px`,
    `--layout-target-columns`) alongside SPPM-specific label density, text
    policies, and output profile controls.
  - DOT-only validation for shared layout flags and SPPM render flags.
  - SPPM label density modes (`full`, `compact`, `teaching`) and text handling controls
    (wrap strategy, truncation policy, per-field max lengths) in the DOT renderer.
  - Optional SPPM step numbering in node headers or edge xlabels.
  - Enforce positive-integer validation for SPPM numeric render controls with
    explicit usage errors before rendering.
- Implement shared orientation-aware wrapping:
  - Add deterministic wrap planner that chunks linear sequence renderers when
    `--layout-wrap auto` exceeds target thresholds.
  - Apply wrapped connector hints for LR (snake down rows) and TB (snake right columns)
    with boundary edge routing hints in DOT output.
  - Extend shared wrap coverage to SPPM, flowchart, and swimlane renderers.
  - Add hardening tests before Phase D: real-fixture LR/TB wrap checks, wrap-off
    regression, width-threshold-only activation, tiny-width chunk floor behavior,
    and deterministic node numbering under minor branching.
- Implement SPPM Phase D preset/config defaults:
  - Add built-in output profile defaults (`book`, `web`, `print`, `slide`) with
    explicit-flag override precedence.
  - Add optional `diagrams.toml` loading for `[sppm]` and `[sppm.presets.<profile>]`
    defaults (source-directory or cwd lookup) merged with CLI options.
  - Add tests for profile defaults and config precedence (CLI overrides config).

## 0.1.1 - 2026-04-21

- Fix distribution packaging to include runtime JSON schema assets in wheel and sdist:
  `flo/schema/flo_ir.json` and `flo/schema/flo_types.json`.

- Update runtime schema resolution to prefer packaged schema files under the
  installed `flo` package while retaining fallback lookup for legacy/source-tree
  layouts.

## 0.1.0 - 2026-04-21

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

