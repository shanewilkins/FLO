# FLO Specifications

This directory holds normative specifications for FLO concepts and diagram
types.

For the repository-wide documentation map and authority order, start with
`docs/README.md`.

Normative product scope, lifecycle, and acceptance criteria live in
`docs/requirements/`. Specifications in this directory define current semantic
meaning and must be updated with the catalogs when an approved requirement
changes behavior.

A spec should answer:

- What the artifact is for.
- What inputs or semantics it depends on.
- What behavior is required.
- What is intentionally out of scope.

Specs should avoid implementation detail when possible. Architecture and
refactor notes belong in `docs/design/`.

Current specs:

- `core_language.md`
- `cli_error_contract.md`
- `telemetry_events.md`
- `process_map.md`
- `value_stream_map.md`
- `swimlane.md`
- `sppm.md`
- `spaghetti_map.md`
- `render_capabilities.md`

Preferred split:

- Core language and canonical process semantics belong in `core_language.md`.
- Shared diagram-family semantics belong in a family spec such as
  `process_map.md` when multiple variants inherit the same richer meaning.
- Variant-specific diagram meaning belongs in one spec per concrete diagram
  surface such as `swimlane.md` or `sppm.md`.
- Implementation strategy belongs in `docs/design/`.

See also:

- `docs/GOVERNANCE.md` for domain-specific authority and change classes
- `docs/design/README.md` for explanatory architecture and migration material
