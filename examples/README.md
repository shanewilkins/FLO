# Examples Layout

This folder contains human-readable FLO model fixtures used for docs and tests.

- `reference/`: stable, representative examples used by smoke and integration tests.
- `conformance/valid/`: minimal rule-focused examples that should validate.
- `conformance/invalid/`: minimal rule-focused examples that should fail validation.

Governance intent:

- Use `reference/` when the question is "what does a realistic FLO model look like?"
- Use `conformance/` when the question is "does the implementation accept or reject this rule?"

Fixture posture:

- Reference artifacts are curated exemplars. They may be broad, readable, and representative.
- Conformance artifacts are executable assertions encoded as fixtures. Keep them as small and local as possible.
- Reference artifacts may anchor broad rendered-output or export regressions.
- Conformance artifacts should avoid carrying unrelated feature coverage when a narrower fixture will do.
- Do not use `reference/` to prove one narrow validation rule when a conformance fixture would do.
- Do not overload `conformance/` with documentation-style examples meant to teach usage patterns.

Testing pattern:

- Keep fixtures in `examples/` as source of truth.
- Load fixtures from tests instead of duplicating test-only YAML snippets.
- Use `reference/` for broad pipeline tests and rendered-output anchors.
- Use `conformance/` for parser, compiler, validator, and contract-focused rule tests.

Current canonical highlights:

- `reference/new_semantics.flo` demonstrates canonical item/resource relations,
	explicit handoff, and explicit parallel split/join.
- `reference/semantic_controls_showcase.flo` is the primary broad exemplar for
	mixed material and information flow, explicit handoff, explicit rework, and
	parallel coordination.
- `conformance/` fixtures are expected to stay narrow and rule-specific even as
	canonical semantics evolve.
