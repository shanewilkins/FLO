# FLO Requirements

This directory contains FLO's normative requirements registers.

- `user_requirements.csv` defines product behavior and user outcomes.
- `technical_requirements.csv` defines implementation, architecture,
  verification, governance, and release obligations.

The catalogs include the full path through 1.0. Rows marked
`State: Proposed` are normative records of unresolved decisions, not approved
implementation commitments. Committed post-1.0 boundaries may also be recorded
when the product direction is explicit.

Pre-1.0 product delivery follows the modern process-improvement book: 0.4
unlocks White Belt, 0.5 Yellow Belt, 0.6 Green Belt, 0.7 Black Belt, and 0.8
Master Black Belt. Later-belt features do not gate earlier releases, and Black
Belt or Master Black Belt candidates are not binding until the corresponding
book, language, and rendering specifications are accepted.

Governance, identifier stability, and change rules are defined in
`docs/GOVERNANCE.md`.

The user register uses:

`Requirement_ID, Journey, Outcome, Rationale, Priority, Target_Release, State, Acceptance, Contract_Refs, Decision_Record`

The technical register uses:

`Requirement_ID, Area, Constraint, Priority, Target_Release, State, Verification, Contract_Refs, Decision_Record`

The technical register is primarily for cross-cutting constraints. Existing
feature-level rows remain for immutable-ID history; new feature-specific
implementation detail belongs in the relevant specification and tests rather
than being duplicated here.

Generate a read-only release view from both registers with:

```bash
uv run python scripts/check_docs_governance.py --release-view
```

The generated view is navigation, not a second commitment source.

Current serialized structure remains authoritative in `schema/`, and current
language and diagram meaning remains authoritative in `docs/specs/`.
