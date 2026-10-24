# White Belt candidate acceptance

Status: candidate accepted; tagging and publication pending.
Review date: 2026-10-24. Requirements: TR-114 and TR-118.

## Candidate identity and evidence

The [machine record](white_belt_candidate_acceptance.json) identifies the immutable
source revision, GitHub's tested synthetic merge revision, configuration and
architecture-document fingerprints, wheel hashes, and complete glyph measurements.
The [architecture trace](architecture_validation_evidence.json) retains actual
stage observations and public/CLI/golden/installed-path parity. These records
identify the tested candidate rather than assuming that any later HEAD was tested.

[Clean CI run 40102340173](https://github.com/shanewilkins/FLO/actions/runs/40102340173)
passed all four jobs. Source revision:
`e82859da49aff86068992ec7bcbc7bbb2a4e9565`; tested merge revision:
`91b6855f6dc91d457c57b9ad2cfec3ac4b75486f`.

Both platform builds produced the same `flo_lang-0.4.2-py3-none-any.whl`:
SHA-256 `04321a78079ede3020030f9c8bfa62420836bd3fbbc0b655c9ebc5c1e873627b`.
The package version identifies a rehearsal build, not a newly published release.
The eventual release must record its version/tag and verify the resulting candidate
under the same policy before publication.

## Architecture review and dispositions

The repository-wide [validation report](architecture_validation.md) reviews process,
source, rendering, application/API, optional integrations, diagnostics, and publication.
Effective decisions are the four-package architecture, render-stack ADR, renderer
boundaries, SPPM design, and accepted layout-finalization clarification linked there.
Proposed target structures remain future work.

| Finding | Final disposition | Evidence |
| --- | --- | --- |
| AF-001 | Closed by R3a/R3b | Typed routed geometry and complete final scene; supplied-scene consumption with policy disabled; zero observed placement calls during emission; transitive pure-emitter import contract |
| AF-002 | Closed by R2 | Diagram-owned policy; explicit neutral settings/transforms; independent-diagram and environment-invariance tests; all neutral modules checked |
| AF-003 | Closed by R1 | One production execution; golden call-through/import tests; detached optional stage observation |

No identified architecture violation remains open. Eleven import contracts,
responsibility probes, behavioral stage tests, and publication/CI policy checks
protect the reviewed boundaries. The trace's acceptance field deliberately
requires this recorded review; a passing automated probe alone cannot accept a release.

## Acceptance results

- Full clean Linux suite: **1,234 passed, 93.72% coverage**, seven existing Click
  test-helper deprecations. Full pre-commit quality gates pass.
- Determinism: all **13 cases / 26 golden files** match. Final-SVG geometry has
  zero violations; accessible names/descriptions pass for all 13 artifacts.
- Linux and macOS: isolated installed-wheel imports, CLI/API author/validate/
  inspect/render/size/export journeys, runtime identity, representative path parity,
  IR preservation, repeatability, and architecture checks pass.
- Chrome 156: **643 text elements across 13 SVGs on each platform**, with zero
  invalid bounds, node/annotation clipping, canvas overflow, or unsafe-fit findings.
  Minimum effective corpus text sizes range from 9 to about 13 CSS pixels; the
  explicit 0.75 fit floor remains enforced. Theme contrast/non-color tests are
  separate from glyph measurements. Linux also retains the rendered screenshot.
- macOS consumer startup was reproduced failing when the setup action flattened
  Chrome's bundle. Restoring its `.app` structure fixes the child-process service
  lookup without disabling the macOS browser sandbox or changing acceptance limits.

## Accepted scope and release boundary

The single-page White Belt SPPM surface is promoted to stable under the
[capability contract](../specs/render_capabilities.md). Multi-page publication,
child maps, dedicated generic-branch geometry, and later-belt renderer acceptance
remain outside this promotion. Practitioner/specialist sessions remain the agreed
1.0 follow-up. Consistent diagnostic delivery is separately queued under TR-117;
unknown optional timing is visible and nonfatal.

R4 and candidate review are complete. No release tag, version bump, merge, or
package publication is recorded by this acceptance. A release-cut record must add
the eventual immutable tag and distribution identities; this candidate record
must not be presented as an already published release baseline.
