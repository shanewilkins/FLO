# White Belt release closure plan

Status: in progress. Scope: the remaining single-page SPPM acceptance in TR-114.
The [roadmap](../ROADMAP.md) and requirements registers govern release scope.

Architecture acceptance under TR-118 and the
[release architecture integrity policy](../policy/release_architecture_integrity.md)
now takes precedence over the remaining release work. Existing completed checks
remain evidence for behavior; architecture integrity is not yet verified.

Work proceeds in this order; each item needs appropriate executable and review
evidence before closure.

- [x] Architecture validation assessment: the [report](architecture_validation.md)
  and [machine evidence](architecture_validation_evidence.json) identify three
  blocking responsibility findings; the ownership clarification is recorded in an
  accepted ADR. Passing output/import checks do not clear those findings.
- [x] R1 shared execution and optional detached engine-stage trace; AF-003 closed.
- [x] R2 diagram-owned policy and explicit neutral serialization/transform inputs; AF-002 closed.
- [x] R3a routed geometry before SVG emission; partial AF-001 remediation.
- [x] R3b complete final-scene geometry and geometry-consuming SVG emission; AF-001 closed.
- [ ] Architecture remediation and acceptance: complete report slice R4,
  close AF-001–003 with boundary evidence, and accept the immutable clean candidate
  as an architecture-consistent baseline.

- [x] Geometry and visual invariants (shape and annotation geometry): investigate the corpus's remaining warning
  budgets, fix faulty routing or classification, and gate final rendered node,
  label, endpoint, connector, visible-lane, and canvas geometry. Preserve bounded deterministic
  rework placement. Review changed goldens before accepting them.
- [x] Sizing acceptance: exercise width/height in px, in, cm, and mm, deterministic
  reflow, inspectable bounds, expansion, safe fit, and the legibility floor through
  the CLI and installed package.
- [ ] Accessibility (automated non-color/contrast checks completed): verify accessible names, contrasting text, monochrome and
  color-safe meaning, and effective text size under scaling.
- [ ] Stable contract (published; promotion pending): publish the single-page SPPM support boundary, capability
  matrix, compatibility guarantees, and remaining limitations. Promote only the
  acceptance surface whose gates pass.
- [ ] Installed-consumer rehearsal (local wheel passed; clean CI pending): build the current tree into a wheel and run
  author, validate, inspect, render, size, and JSON export in an isolated directory;
  regenerate the book reference and exercise an SVG consumer. CI repeats this
  from clean checkouts on the declared platforms.
- [ ] Release review: run all required checks, reconcile requirement evidence and
  release notes, and report the exact remaining blockers. Tagging and publishing
  follow review of the concrete release candidate.

Consistent diagnostic delivery (UR-086/TR-117) remains a separately queued next
stabilization sprint under [its implementation plan](diagnostic_delivery_plan.md).
Existing geometry warnings and errors must remain visible during this work.

## Evidence log

- Entry baseline: 1,148 tests passed, 93.49% coverage; 13 SPPM corpus cases matched
  26 committed files. Golden equality includes reviewed warning budgets and does
  not by itself prove visual acceptance.
- The working tree includes the previously completed timing, rework, and semantic
  changes; release rehearsal must package these changes, not just current HEAD.

- Final-SVG geometry gate: all 13 corpus cases pass with zero render diagnostics.
  Shared terminal classification, shifted forward/rework routing, branch-caption
  placement, polygon avoidance, and continuation-token collisions were repaired.
  `scripts/check_sppm_geometry.py` checks actual output shapes, routes, endpoints,
  annotation collisions, and canvas containment; regression tests include broken
  SVGs that must fail. CI and pre-commit run this gate.
- Browser text-metric acceptance remains pending: local headless Edge timed out;
  the in-app browser security policy rejected local-file navigation. No browser
  measurement result is claimed. Existing CI browser smoke remains in place.

- Public-path parity: the previous golden builder omitted public geometry
  preparation/resolution. It now validates canonical IR and runs those stages;
  the installed and checkout CLI book SVGs agree with the regenerated golden.
- Equivalent physical-size CLI tests pass; the isolated installed-wheel journey
  also validates, inspects, renders, exports, exercises the API from site-packages,
  and compares equivalent px/in/cm/mm outputs. Linux and macOS CI jobs now run
  the expanded journey from their installed wheels.
- All five built-in themes preserve visible VA/RNVA/NVA work-card class labels
  in full, compact, and teaching modes; monochrome SPPM colors are neutral gray.
  Existing text-contrast checks and 15 theme/density checks pass.

## Outstanding release blockers

0. Architecture remediation R1–R3b is complete; AF-001–003 are closed.
   Immutable clean-candidate acceptance under R4/TR-118 precedes release.

1. Browser/font legibility and text-clipping measurements at publication scales.
   Local shape/annotation checks do not substitute for these measurements.
2. Clean-checkout Linux/macOS CI and SVG-consumer results for this candidate.
   Local wheel installation is evidence for the current working tree, not a
   claim that clean remote CI passed.
3. Stable-tier promotion and final candidate review, followed by tagging and
   publishing. The repository version remains 0.4.2; no release was published.

## Local candidate verification

- Full suite after public-path alignment: 1,186 tests passed; 93.51% coverage.
  Subsequent final-geometry/lane checks: 21 tests passed, including the added
  negative lane-containment case. Platform-policy tests also pass after expanding
  the Linux/macOS installed-wheel CI journeys.
- Final corpus: 13 cases / 26 files regenerate identically; zero render warnings
  and zero final-SVG geometry violations. Accessible-name checks pass all 13 SVGs.
- Ruff, type checking, docstrings, complexity, file length, dead-code/import
  contracts, documentation governance, and whitespace checks pass locally.
- Isolated installed wheel: import smoke and the expanded journey pass. Equivalent
  physical sizes produce identical bytes. The installed book SVG equals the
  public-path golden (SHA-256
  `b4e6c43720e477c571d3ff21afb1913a660f9ae80eabf83a3c6cc0e1d159763c`).
  The built wheel SHA-256 is
  `bfb946f05c46ed3fa4fe88d0f77334763f99dc1b5ed6c2096b1c40c216ee995e`.
- The book-artifact generator regenerates and verifies the maintained reference.
  This evidence describes the current uncommitted candidate; remote CI, stable
  promotion, a release tag, and package publication are not claimed.
