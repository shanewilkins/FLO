# FLO Specifications

This directory holds normative specifications for FLO concepts and diagram
types.

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
- `process_map.md`
- `flowchart.md`
- `value_stream_map.md`
- `swimlane.md`
- `sppm.md`
- `spaghetti_map.md`

Preferred split:

- Core language and canonical process semantics belong in `core_language.md`.
- Shared diagram-family semantics belong in a family spec such as
	`process_map.md` when multiple variants inherit the same richer meaning.
- Variant-specific diagram meaning belongs in one spec per concrete diagram
	surface such as `flowchart.md`, `swimlane.md`, or `sppm.md`.
- Implementation strategy belongs in `docs/design/`.

