# Code and ecosystem review: FLO follow-up

Status: FLO-owned work complete, 2026-10-30. Package candidate: **0.5.0**.

This records the dispositions of CE-001 through CE-006 in the fourteen-lens
review archived at `notes/code_ecosystem_review_2026_10_30.md`. The original
review and reproductions remain unchanged. The user approved the 0.5 package
boundary and assigned peer-repository work to each peer's own team.

| Finding | FLO disposition | Peer-team work |
| --- | --- | --- |
| CE-001: nonportable nested evidence | Shared typed result/parameter contracts reject nonfinite or non-JSON data, including unselected statistics. Export encoding also rejects NaN/Infinity. Valid structured evidence round-trips unchanged. | None for this producer defect. |
| CE-002: lss4py projection/classification mismatch | Documented the 0.5.0 producer boundary and migration rules. Added regressions proving empty structured relations survive export and inspection, distinguishable from omission. First-class classification and evidence remain intact. | lss4py owns projection/policy migration and installed-producer acceptance. |
| CE-003: old book sources versus new contract | Versioned the breaking candidate as 0.5.0, distinct from published 0.4.3; added a source/consumer migration guide. The language marker stays `0.1`, with the distinction explicit. | The book team owns native-source migration and installed-wheel acceptance. |
| CE-004: processing/setup terminology | Inspection and value-stream output now use processing/P/T and setup/S/T, matching SPPM. Setup policy text agrees. Machine keys, numerical behavior, zero and selectors stay intact. Corrected RNVA prose to “required non-value-added.” | Teams may review their own downstream terminology. |
| CE-005: accepted IDs unusable by references | References support full nonblank IDs, including Unicode, spaces, newlines and dots. The final dot separates the field. Authored `ref` selects reference validation, so malformed refs report their own field rather than missing profile `basis`. | None for this producer defect. |
| CE-006: palette duplication and provenance | Centralized FLO's existing ten shared colors and font list; pinned mpi-theme 0.1.5/revision provenance. Legacy MPI SPPM roles derive from the central theme. Added producer conformance command, drift tests and an owner/update procedure. Added no assets or dependency. | Broader producer adapter/asset distribution decisions remain with the respective teams. |

The [migration guide](../howto/migrate_to_0_5.md),
[normative contract](../specs/book_aligned_contract.md) and
[palette procedure](../specs/render_themes.md#mpi-palette-ownership) describe the
maintained boundary. Retired runtime aliases remain rejected. No peer files
were modified, and this closure does not certify migrated book/lss4py consumers.

## Verification

- Full final suite: **2,542 passed**, no failures or skips; **94.54%** statement
  coverage against the 90% gate. Seven existing Click deprecation warnings.
- Focused regressions cover source and canonical invalid evidence, strict JSON
  export defense, preserved structured statistics, supported ID/reference
  round-trips, malformed-ref diagnostics, direct-reference domain failures,
  empty versus absent relations, glossary-derived P/T/S/T expectations, and
  shared-token/producer-version drift.
- Ruff, formatting, `ty`, eleven import contracts, renderer responsibility
  checks, generated schemas, strict docs governance and whitespace checks pass.
- All thirteen golden cases/twenty-six files match byte-for-byte; thirteen SVGs
  pass final geometry and accessible-name checks.
- Pinned mpi-theme 0.1.5 checkout matches all ten shared colors and heading
  font fallbacks via `scripts/check_mpi_palette.py`.
- Wheel and sdist build as 0.5.0; strict Twine and release identity/bundled-ELK
  checks pass. The release-tag validator was exercised with `v0.5.0`; no tag was
  created and nothing was published.
- A temporary clean installed wheel imports all **169** modules and completes
  `scripts/check_yb_journey.py`. Archived review probes produce identical
  corrected FLO-owned results from source and the installed wheel: nested NaN
  and sets fail E0222 at the supplied result field, and Unicode references pass.
  The clean cache-selected install uses Pydantic 2.14.1/core 2.50.1; the source
  environment uses 2.14.2/core 2.50.2. Both are within declared bounds.
- Verified all six pre-existing changed files against the review manifest:
  their original content is preserved, with only the intended package-version
  change in the lock and migration-guide link in the docs index overlapping.

Remote CI/platform/browser/assistive-technology acceptance and peer migrations
were not executed here. Those remain separately owned acceptance work.
