# Render Intent Schema

Status: accepted

This is the accepted explanatory design contract for source-owned render
intent.
The authoritative structural contract lives in `schema/flo_ir.json` under
`process.metadata.render`.
Implementation rollout remains phased and this note is non-blocking for the
language-primitive compiler migration.

## Purpose

Define a source-level schema for publication and render intent so a single `.flo`
model can produce multiple complementary render perspectives (for example SPPM
and spaghetti) with reproducible defaults.

This document is a design contract for refactoring. It does not change runtime
behavior by itself.

## Goals

- Keep process semantics in core IR and compiler validation.
- Move publication and renderer intent into process metadata for portability.
- Preserve CLI-driven experimentation and CI overrides.
- Support multiple render modes from one source without duplication.
- Keep `.flo` files easy to author, review, and maintain by humans.

## Non-goals

- Do not force one canonical rendered output per `.flo` file.
- Do not remove existing CLI options immediately.
- Do not entangle execution semantics with presentation semantics.
- Do not require verbose boilerplate metadata for common author workflows.

## Human readability constraints (must-have)

Render intent schema decisions should be filtered through these authoring rules:

1. Make the common case short.
2. Keep nesting shallow where possible.
3. Prefer stable, descriptive keys over compact cryptic abbreviations.
4. Support clear defaults so authors can omit most fields.
5. Keep stable view ids readable and task-oriented (for example `sppm_main`,
   `spaghetti_flow`); use an optional label for display text.
6. Minimize repeated values across views via inheritance from `render.defaults`.
7. Error messages must suggest short, copy-pasteable fixes.

## Authoring ergonomics (recommended)

- Treat `render.defaults` as the preferred place for shared intent.
- Require only per-view deltas under `render.views.<id>`.
- Keep numeric/unit fields human-oriented:
  - page format as named token (`letter`, `a4`, `legal`, `tabloid`),
  - dimensions as familiar values (`800`, `800px`, `8.5in`, `21cm`, `210mm`).
- Treat a bare numeric dimension as pixels for compatibility. New examples
  should include units when physical size matters.
- Avoid schema branches that force duplicated option names in many locations.
- Preserve alias migration paths long enough to avoid manual rewrites of all
  existing examples in one release.

## Recommended ownership model

1. Source metadata owns document intent.
2. CLI owns session-level overrides.
3. Built-in profile defaults fill any missing values.

## Precedence contract

For each resolved render option:

1. Explicit CLI option value
2. View-level source intent (`process.metadata.render.views.<view_id>`)
3. Process-level source defaults (`process.metadata.render.defaults`)
4. Existing output profile defaults (for example `book`, `print`, `web`)
5. Renderer hard defaults

This keeps source reproducible while preserving fast local iteration.

## Render intent structure

Render intent should live under process metadata:

```yaml
process:
  id: example
  name: Example
  metadata:
    render:
      defaults:
        diagram: sppm
        publication:
          page_format: letter
          margins:
            top: 48
            right: 48
            bottom: 48
            left: 48
          header:
            enabled: true
          footer:
            enabled: true
        layout:
          wrap: auto
          max_width: 1200
          target_columns: 3

      views:
        sppm_main:
          label: Main Process Map
          diagram: sppm
          publication:
            page_format: letter
            header:
              enabled: true
            footer:
              enabled: true
          layout:
            wrap: auto
            target_columns: 3

        spaghetti_material:
          label: Material Travel
          diagram: spaghetti
          spaghetti:
            channel: material
            people_mode: aggregate
          publication:
            page_format: tabloid
            header:
              enabled: false
            footer:
              enabled: false

Human-friendly shorthand guidance:

- If a view shares defaults, do not repeat those fields.
- If only one render perspective is needed, authors may omit `views` entirely
  and rely on `render.defaults`.
- Bundle pages should reference existing view ids rather than restating full
  view configuration per page.
```

Notes:

- `defaults` applies to all views unless overridden.
- `views` defines named projections for the same underlying process.
- Each view key is a stable machine identifier. `label` is optional display
  text and may change without changing the identifier used by CLI, bundles, or
  automation.
- `diagram` remains optional in `defaults`; if omitted there, each view must set it.
- Shared `publication` and `layout` sections carry cross-renderer intent.
  Renderer-specific options live in a subtree named for the renderer, such as
  `spaghetti`, `sppm`, `swimlane`, or `value_stream`.
- A renderer-specific subtree must agree with the resolved `diagram`; unrelated
  renderer subtrees are rejected or warned according to validation mode.
- Existing metadata aliases can remain supported during migration.

## Accepted vocabulary

After flowchart removal, maintained diagram identifiers are `sppm`,
`swimlane`, and `spaghetti`. The 0.3 value-stream-map release adds
`value_stream` when that renderer becomes available.

Spaghetti intent uses:

- channels: `material`, `people`, `both`
- people modes: `aggregate`, `worker`

The schema, validator, resolver, CLI, and tests must retire or explicitly
migrate the stale render-intent-only values `equipment` and `individual`.
Until those layers agree, the accepted contract is an implementation gap rather
than a claim about current runtime behavior.

Orientation belongs to render options rather than diagram identifiers.
Current CLI orientation values are `lr` and `tb`.

Dimensions accept `px`, `in`, `cm`, and `mm`. Bare numeric values remain
compatible and are interpreted as pixels.

## Should intended render modes be in source?

Yes, as optional named views.

Rationale:

- A process usually has multiple legitimate visual perspectives.
- Keeping those perspectives in source improves reproducibility in docs and CI.
- Named views avoid forcing a single renderer worldview.

Important constraint:

- One source must support many views.
- View selection should be explicit (`--view sppm_main`) and overrideable
  (`--diagram spaghetti`), not inferred from file path.

## CLI evolution

Keep current flags. Add only small routing helpers:

- `--view <name>`: select a named source view.
- `--list-views`: print available view ids and diagrams from source metadata.

All existing flags continue to work and override source values.

## Minimal schema keys (phase 1)

Start narrow to reduce risk:

- `render.defaults.diagram`
- `render.defaults.publication.page_format`
- `render.defaults.publication.header.enabled`
- `render.defaults.publication.footer.enabled`
- `render.defaults.layout.wrap`
- `render.defaults.layout.max_width`
- `render.defaults.layout.target_columns`
- `render.views.<id>.diagram`
- `render.views.<id>.label`
- Optional view overrides for the same publication/layout keys

Defer until phase 2 or later:

- Renderer-specific deep subtrees beyond currently supported options
- Pagination policies and multi-page sequencing directives

## Validation rules

- Unknown `render.views` entries are allowed but warned if malformed.
- `render.views.<id>.diagram` must be one of supported diagrams.
- `render.views.<id>.label`, when present, must be non-empty display text.
- `publication.page_format` must be one of known presets.
- Dimension fields accept positive numbers interpreted as pixels or positive
  values with `px`, `in`, `cm`, or `mm` units.
- Count fields such as `target_columns` must be positive integers.
- `header.enabled` and `footer.enabled` are booleans.

Validation usability rules:

- Diagnostics should show the exact failing metadata path.
- Diagnostics should include one valid example snippet.
- For unknown keys (strict mode), diagnostics should suggest closest valid key.

## Refactor plan (careful, staged)

Phase 0: no behavior change

- Add schema/documentation and fixtures that include render intent metadata.
- Add parser helpers that read intent blocks but do not apply them yet.

Phase 1: opt-in resolution path

- Add internal option resolver to merge:
  CLI > view intent > defaults intent > profile defaults > hard defaults.
- Gate with feature toggle in code path until tests stabilize.

Phase 2: CLI integration

- Add `--view` and `--list-views`.
- Keep all existing CLI flags untouched.
- Ensure existing scripts continue to pass without source render metadata.

Phase 3: schema hardening

- Extend typed metadata schema to include `process.render` shape.
- Add targeted validation diagnostics with actionable messages.

Phase 4: migration and deprecation

- Document recommended source-first workflow.
- Optionally deprecate select CLI knobs only after at least one stable cycle.

## Testing strategy

- Unit tests for resolver precedence and partial overrides.
- Integration tests for:
  - same `.flo` rendered through two named views (SPPM and spaghetti),
  - `--view` selection,
  - CLI override dominance,
  - fallback behavior when no render intent exists.
- Golden artifact tests for representative reference models.
- Authoring ergonomics tests:
  - minimal metadata example remains valid,
  - single-view defaults-only example remains concise,
  - multi-view example avoids duplicated defaults.

## Compatibility constraints

- Existing `.flo` files without render intent must produce identical outputs.
- Existing CLI contracts and error codes must remain stable.
- Existing build scripts should need no immediate changes.

## Accepted decisions

- `render.views` uses stable machine identifiers with optional display labels.
- Cross-renderer publication and layout intent uses shared sections;
  renderer-specific options use renderer-named subtrees.
- Dimension fields accept `px`, `in`, `cm`, and `mm`; bare numbers remain
  pixel-compatible.
- CLI values override named views, named views merge over process defaults,
  process defaults override profiles, and profiles override renderer defaults.

## Decision summary

Adopt source-level render intent with named multi-view support, keep CLI as
overrides, and complete the phased resolver, schema, validator, and vocabulary
alignment without changing legacy inputs silently.
