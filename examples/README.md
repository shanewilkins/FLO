# Examples Layout

This folder contains human-readable FLO model fixtures used for docs and tests.

- `reference/`: stable, valid examples used by smoke/integration tests.
- `conformance/valid/`: rule-focused examples that should validate.
- `conformance/invalid/`: rule-focused examples that should fail validation.

Testing pattern:

- Keep fixtures in `examples/` as source of truth.
- Load fixtures from tests instead of duplicating test-only YAML snippets.
- Use `reference/` for broad pipeline tests and `conformance/` for rule tests.
