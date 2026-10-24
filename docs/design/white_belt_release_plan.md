# White Belt release closure plan

Status: candidate acceptance complete; release cut pending.
Scope: single-page SPPM under TR-114 and architecture integrity under TR-118.

The [acceptance record](white_belt_candidate_acceptance.md) and its machine-readable
companion identify the clean tested revisions and distribution/consumer evidence.
The [release architecture integrity policy](../policy/release_architecture_integrity.md)
applies again if code, dependencies, effective architecture, or release packaging changes.

## Completed candidate gates

- [x] Repository-wide architecture assessment and effective-decision inventory.
- [x] R1 shared execution and detached stage observation; AF-003 closed.
- [x] R2 diagram-owned policy and explicit neutral engine inputs; AF-002 closed.
- [x] R3a routed geometry and R3b complete final scene before emission; AF-001 closed.
- [x] R4 clean-candidate architecture review, installed identity, platform results,
  finding dispositions, and retained artifact hashes.
- [x] Final-SVG geometry, deterministic rework, reviewed goldens, and zero corpus
  warning allowances: 13 cases / 26 files match, zero geometry violations.
- [x] CLI and installed px/in/cm/mm equivalence, reflow, bounds, expansion, safe
  fit, and unreadable-fit failure.
- [x] Accessible names, theme contrast/non-color meaning, and real browser glyph
  bounds/effective-size checks on Linux and macOS.
- [x] Stable single-page SPPM compatibility contract and scoped promotion.
- [x] Clean Linux/macOS installed-wheel author/validate/inspect/render/size/export
  journeys, API isolation, book-reference parity, and SVG consumer rehearsal.
- [x] Candidate review, requirement evidence, release-note reconciliation, and
  all required quality checks. Full clean suite: 1,234 passed, 93.72% coverage.

## Release-cut actions

- [ ] Select the next release version and review its concrete distribution candidate.
- [ ] Verify that final versioned candidate from clean checkouts under the same
  architecture/platform gates; record its immutable release tag and artifact hashes.
- [ ] Tag and publish the accepted distribution.

The repository still reports 0.4.2; the rehearsal wheel is not a newly published
version. No implementation or acceptance blocker remains for this reviewed
candidate. Tagging/publication have not been performed.

Unified diagnostic delivery (UR-086/TR-117) remains the separately queued next
stabilization sprint in [its plan](diagnostic_delivery_plan.md). Multi-page,
child-map, and later-belt renderer acceptance remain outside this release scope.
Practitioner/specialist sessions remain the agreed 1.0 follow-up.
