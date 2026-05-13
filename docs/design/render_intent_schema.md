# Render Intent Schema (design)

Purpose
-------

Define a source-level schema for publication and render intent so a single `.flo`
model can produce multiple complementary render perspectives (for example SPPM
and spaghetti) with reproducible defaults.

This document is a design contract for refactoring. It does not change runtime
behavior by itself.

Goals
-----

- Keep process semantics in core IR and compiler validation.
- Move publication and renderer intent into process metadata for portability.
- Preserve CLI-driven experimentation and CI overrides.
- Support multiple render modes from one source without duplication.
- Keep `.flo` files easy to author, review, and maintain by humans.

Non-goals
---------

- Do not force one canonical rendered output per `.flo` file.
- Do not remove existing CLI options immediately.
- Do not entangle execution semantics with presentation semantics.
- Do not require verbose boilerplate metadata for common author workflows.

Human readability constraints (must-have)
-----------------------------------------

Render intent schema decisions should be filtered through these authoring rules:

1. Make the common case short.
2. Keep nesting shallow where possible.
3. Prefer stable, descriptive keys over compact cryptic abbreviations.
4. Support clear defaults so authors can omit most fields.
5. Keep view ids readable and task-oriented (for example `sppm_main`, `spaghetti_flow`).
6. Minimize repeated values across views via inheritance from `render.defaults`.
7. Error messages must suggest short, copy-pasteable fixes.

Authoring ergonomics (recommended)
----------------------------------

- Treat `render.defaults` as the preferred place for shared intent.
- Require only per-view deltas under `render.views.<id>`.
- Keep numeric/unit fields human-oriented:
  - page format as named token (`letter`, `a4`, `legal`, `tabloid`),
  - dimensions as familiar strings (`800`, `8.5in`, `21cm`).
- Avoid schema branches that force duplicated option names in many locations.
- Preserve alias migration paths long enough to avoid manual rewrites of all
  existing examples in one release.

Recommended ownership model
---------------------------

1. Source metadata owns document intent.
2. CLI owns session-level overrides.
3. Built-in profile defaults fill any missing values.

Precedence contract
-------------------

For each resolved render option:

1. Explicit CLI option value
2. View-level source intent (`process.metadata.render.views.<view_id>`)
3. Process-level source defaults (`process.metadata.render.defaults`)
4. Existing output profile defaults (for example `book`, `print`, `web`)
5. Renderer hard defaults

This keeps source reproducible while preserving fast local iteration.

Render intent structure (proposed)
----------------------------------

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
- `diagram` remains optional in `defaults`; if omitted there, each view must set it.
- Existing metadata aliases can remain supported during migration.

Should intended render modes be in source?
------------------------------------------

Yes, as optional named views.

Rationale:

- A process usually has multiple legitimate visual perspectives.
- Keeping those perspectives in source improves reproducibility in docs and CI.
- Named views avoid forcing a single renderer worldview.

Important constraint:

- One source must support many views.
- View selection should be explicit (`--view sppm_main`) and overrideable
  (`--diagram spaghetti`), not inferred from file path.

Proposed CLI evolution
----------------------

Keep current flags. Add only small routing helpers:

- `--view <name>`: select a named source view.
- `--list-views`: print available view ids and diagrams from source metadata.

All existing flags continue to work and override source values.

Minimal schema keys (phase 1)
-----------------------------

Start narrow to reduce risk:

- `render.defaults.diagram`
- `render.defaults.publication.page_format`
- `render.defaults.publication.header.enabled`
- `render.defaults.publication.footer.enabled`
- `render.defaults.layout.wrap`
- `render.defaults.layout.max_width`
- `render.defaults.layout.target_columns`
- `render.views.<id>.diagram`
- Optional view overrides for the same publication/layout keys

Defer until phase 2 or later:

- Full margin controls and unit syntax
- Renderer-specific deep subtrees beyond currently supported options
- Pagination policies and multi-page sequencing directives

Validation rules (proposed)
---------------------------

- Unknown `render.views` entries are allowed but warned if malformed.
- `render.views.<id>.diagram` must be one of supported diagrams.
- `publication.page_format` must be one of known presets.
- Numeric fields (`max_width`, `target_columns`) must be positive.
- `header.enabled` and `footer.enabled` are booleans.

Validation usability rules:

- Diagnostics should show the exact failing metadata path.
- Diagnostics should include one valid example snippet.
- For unknown keys (strict mode), diagnostics should suggest closest valid key.

Refactor plan (careful, staged)
-------------------------------

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

Testing strategy
----------------

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

Compatibility constraints
-------------------------

- Existing `.flo` files without render intent must produce identical outputs.
- Existing CLI contracts and error codes must remain stable.
- Existing build scripts should need no immediate changes.

Open decisions
--------------

- Should `render.views` require stable ids or allow freeform labels?
- Should diagram-specific keys live under `render.views.<id>.<diagram_name>`
  or under a shared flat option map?
- Should margins be strict pixel integers in phase 1, or permit dimensions
  (`px`, `in`, `cm`) immediately?

Recommendation
--------------

Adopt source-level render intent with named multi-view support, keep CLI as
overrides, and stage refactoring through a precedence resolver before exposing
new public behavior.
