# FLO Policy

This directory is reserved for durable safety, privacy, product-scope, and release-governance
boundaries.

Current policies:

- [Release architecture integrity](release_architecture_integrity.md): known-good
  baselines and architecture acceptance before every release, including patches

- `artifact_scope.md`: what belongs in FLO versus downstream analysis tools
- `telemetry_privacy.md`: privacy and disclosure boundaries for process-event
  data

Repository governance is defined in `docs/GOVERNANCE.md`.

Historical redirect files remain for link compatibility but are not current
policy:

- `authoritative_artifacts.md`
- `requirements_governance.md`
- `language_primitive_migration_contract.md`
- `sppm_regression_gates.md`

Renderer-specific regression rules belong in renderer specifications and
tests. One-off implementation migrations belong in ADRs and plans.
