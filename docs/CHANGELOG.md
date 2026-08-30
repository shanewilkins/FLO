# Changelog

## Unreleased

- Split SPPM, swimlane, spaghetti, and value stream into independent renderer
  packages; give ELK-backed renderers owned request builders and presentation
  policy, derive capabilities from the executable registry, remove global SCC
  preprocessing and legacy flat renderer modules, and enforce the dependency
  direction with Import Linter and policy tests.
- Add the maintained `value_stream` direct-SVG renderer with typed
  analysis projection, distinct information and material surfaces, declared
  timing annotations, external-boundary flows, and honest partial-data notices.
- Add deterministic model inspection covering composition, entities, paths,
  named views, diagnostics, and requested analysis or diagram readiness.
- Render spatially complete spaghetti routes by default when other routes lack
  coordinates, with stable warnings and visible partial notices; add strict
  all-routes-positioned mode.
- Preserve authored integer or string `process.version` values through canonical
  IR, internal serialization, schema projection, validation, and JSON export.
- Activate deterministic direct-SVG row wrapping for linear LR SPPM sequences,
  with explicit inter-row corridor routing and shape-aware connector attachment.
  Add the book-profile White Belt wash-and-fold golden case and a build/check
  command for copying its generated SVG into the book without hand editing.
- Improve direct-SVG SPPM legibility with inverted split-tone queue triangles,
  shallower colored title caps, and slightly larger task-card body text.
- Add a compact book-profile decision golden with a diamond, labeled true/false
  branches, deterministic convergence, and branch-geometry invariants.
- Add the initial typed static timing-analysis engine with unit-normalized node
  contributions, complete linear lead time, deterministic branch ranges, and
  explicit diagnostics for incomplete, cyclic, parallel, or ambiguous models;
  expose it through `flo inspect` as concise text or deterministic JSON, feed
  it into SPPM publication footers, and label declared task changeover as `C/O`
  on work-step shapes.
- Implement deterministic publication background and font family/scale controls
  through one typed cross-diagram theme registry, with inheritance, semantic
  roles, render-intent and CLI precedence, legacy SPPM adaptation, validation,
  accessibility checks, and configured-theme regression goldens.
- Add `flo new --template simple-process` with readable stable-ID generation
  and non-overwriting file creation.
- Route explicit CLI commands through command-specific Click help and emit
  concise source-aware validation diagnostics with file, line, column, field
  path, and source excerpt where the current validator identifies a node.
- Vendor the pinned `elkjs` runtime and license into distribution artifacts,
  and require a clean-wheel scaffold, validate, render, and export rehearsal
  before publication.
- Add the Yellow Belt visual acceptance corpus for linear, decision,
  three-lane handoff, and rework-loop maps. Keep SPPM independent of invisible
  business-lane hierarchy and place unassigned swimlane boundaries in process
  order.

## 0.2.0 - 2026-08-09

- Breaking (pre-1.0): remove the deprecated flowchart renderer from the CLI,
  capability matrix, implementation, tests, and current user guidance.
- Consolidate maintained direct-SVG renderer support around SPPM, swimlane, and
  spaghetti maps.
- Add deterministic standalone SPPM publication context, including named page
  formats and SVG header and footer bands without multi-page composition.
- Align stored render-intent validation with the maintained renderer vocabulary
  and retain `lr` and `tb` as the only supported layout orientation values.
- Document strict coordinate-required spaghetti rendering as the current 0.2
  behavior, with deterministic partial rendering committed for 0.3.
- Add release-view governance checks and strengthen deterministic SPPM
  invariant and golden-artifact regression coverage.

## 0.1.2 - 2026-04-28

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

- Add SPPM design note for layout-width, row wrapping, label density/text controls,
  and output profile presets in `docs/design/renderers/sppm_layout_enhancement.md`.
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
