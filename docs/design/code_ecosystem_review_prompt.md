# FLO Code and Ecosystem Review

Status: current review prompt, 2026-10-30.

Review the exact current FLO candidate for correctness, maintainability,
duplication and ecosystem compatibility. Read and apply the
[shared fourteen lenses, authority boundaries and evidence rules](review_lenses.md)
before beginning. Use the [release quality gate](release_quality_gate_prompt.md)
for a release/tag/publication decision; this review has an engineering finding
and evidence disposition, with no numeric readiness score.

FLO's supported language, canonical IR, validation, analysis, interfaces and
artifacts are the subject. Preserve existing work and the declared product scope.
Do not treat the existence of future proposals as an obligation to implement
them. Unless the user also authorizes remediation, produce the review and
reproducers before changing product behavior or peer repositories.

## Establish the candidate and scope

Record before judging:

- FLO version, branch/base commit, candidate snapshot and relevant dirty files,
  including staged, unstaged and untracked inputs used by the review;
- the requested change/review scope, affected supported capabilities and users,
  relevant requirement/specification IDs, intentional exclusions and accepted
  decisions;
- public interfaces, producer/consumer boundaries, runtime/platform and input
  trust assumptions;
- peer repositories or published contracts actually available for the book,
  lss4py and mpi-theme, with exact revisions/versions and relevant dirty state;
- which compatibility directions and supported version combinations are being
  tested, and which remain unknown.

Do not require a clean commit merely to review the working tree. Snapshot it
without resetting or staging the user's changes. Include explicitly relevant
ignored notes as identified inputs; do not indiscriminately collect ignored
files, environments, caches or secrets. Preserve the scope of each observation
when an external checkout or package version differs from the candidate.

## Review basis

Read the shared catalog plus:

- FLO README, Quickstart, manual, documentation map and governance;
- applicable requirements, current specifications, policies and accepted ADRs;
- authored/canonical schemas, compiler, domain validation, IR projections,
  analysis, diagnostics, exports and affected renderer/interface code;
- relevant tests, conformance examples, golden artifacts and actual validation
  entry points;
- package/lock metadata, CI, pre-commit and packaging configuration;
- the book's reviewed terminology/glossary, manuscript examples and diagram
  source/outputs relevant to FLO;
- lss4py's actual supported API, producers/consumers, measurement/provenance
  models and integration examples;
- mpi-theme's actual role/token/theme contracts, consumers, generation/vendoring
  policy and relevant visual fixtures.

Use plans and previous reviews to locate decisions and risk areas, not as proof
that implementation is correct. Missing peer evidence is an explicit limit;
continue useful FLO review without claiming cross-repository compatibility.

## Review workflow

1. **Map contracts and ownership.** Trace source -> composition -> canonical IR
   -> validation -> inspect/export/render and the real ecosystem boundaries.
   Identify authoritative definitions and responsible adapters for each shared
   concept. Build the shared compatibility matrix.
2. **Challenge semantic invariants.** Examine every affected field, reference,
   identity, quantity and transformation. Check omission versus explicit values,
   selectors/populations/provenance, multiplicity, graph reachability/SCCs,
   projection loss, deterministic ordering and consistency among consumers.
   Schema validity alone is insufficient. Keep new execution semantics outside
   scope unless explicitly requested.
3. **Challenge tests independently.** Use L11 to look for false-green tests,
   assertions that mirror helpers, invalid fixtures rejected too early, mocks
   hiding consumer differences and golden changes that bless a regression.
   Prefer a small counterexample or independent oracle to another copy of the
   implementation. Preserve the distinction between new behavior, a migrated
   expectation and an assertion that has simply become weaker.
4. **Trace book terminology end to end.** Give L12 an explicit terminology table:
   book concept/definition and source, FLO authored term, canonical meaning,
   diagnostic/analysis/rendered label, consistency finding. Prioritize central
   concepts affected by recent work. A deliberate distinction must have a
   recorded rationale; vocabulary similarity alone does not prove equivalence.
5. **Check duplication and compatibility.** With L13/L14, compare actual peer
   contracts and representative payloads/artifacts. Look for copied analytical
   methods, conversion/validation rules, theme tokens and terminology catalogs.
   Distinguish owned adapters and governed generated copies from competing
   sources of truth. Recommend shared ownership with concrete migration and
   compatibility checks, not coupling for its own sake.
6. **Validate claims.** Inspect current CI and documented locked workflows. Run
   focused checks/probes first, then the full suite and affected schema,
   architecture/import, artifact, documentation and packaging gates at a
   meaningful checkpoint. Record unavailable checks and why. Exercise actual
   installed interfaces or the exact peer producer/consumer where compatibility
   is claimed. Identify source-isolated wheel checks that reuse dependencies
   separately from clean installs. Do not publish/tag as part of this audit.
7. **Consolidate findings.** Assign stable finding IDs, one primary owner/lens
   and supporting lenses. Separate contract defects, implementation defects,
   integration/version mismatches, maintenance risks and evidence gaps. Mark
   behavior intentionally outside the current contract as a proposal/question.

## Severity and finding requirements

Use `Critical`, `High`, `Medium` or `Low`, with the affected path and assumptions:

- Critical: demonstrated severe security/data-loss exposure or widespread
  corruption of supported semantics with no adequate boundary.
- High: material incorrect acceptance, rejection, evidence loss or incompatible
  supported interface on a meaningful user/consumer path.
- Medium: consequential bounded defect or maintainability/duplication risk with
  a credible failure mechanism.
- Low: limited consequence; explain why it merits action rather than presenting
  a style preference as a defect.

Keep severity separate from confidence (`High`, `Medium`, `Low`) and evidence
state. Unknown compatibility is an evidence gap until a concrete mismatch is
established. A contradiction between authoritative contracts is a finding even
when current code consistently implements one side.

Each finding must contain:

- stable ID/title, severity, confidence, primary lens and supporting lenses;
- affected repositories/revisions, precise files/symbols and governing contract;
- observed versus expected behavior, trigger and practical consequence;
- minimal reproducer/check result, or explicit source-based reasoning if no
  reproduction was obtained;
- existing test gap and smallest useful independent regression check;
- proposed owner and smallest justified correction or coordination decision.

Report genuinely shared issues once and link affected boundaries. Do not pad
findings to fill every lens. Retain strengths with concrete evidence too.

## Required report

Save as `notes/code_ecosystem_review_YYYY_MM_DD.md` using the review date. If it
exists, append a stable short suffix; preserve previous evidence. Reports remain
working notes under the repository's existing ignore policy.

Use this structure:

1. **Candidate, scope and evidence limits**: exact snapshot, peer availability,
   contracts examined, runtime/trust assumptions and exclusions.
2. **Executive findings**: consequential issues first; summarize what is
   established and what cannot be concluded. No release-readiness score.
3. **Lens coverage ledger**: all fourteen IDs with disposition, evidence and
   finding IDs; distinguish applied-with-no-finding from unknown/unavailable.
4. **Book terminology trace**: definitions and end-to-end vocabulary alignment,
   deliberate distinctions and unresolved conflicts.
5. **Ecosystem compatibility and ownership matrix**: the shared matrix, actual
   versions/directions/checks and duplication dispositions.
6. **Ranked consolidated findings**: the required finding fields above.
7. **Validation record and test-quality assessment**: commands/results on this
   candidate, independent probes, what tests establish and remaining blind spots.
8. **Strengths to preserve**: at most five evidence-backed strengths.
9. **Prioritized follow-up**: at most ten actions with owner, dependencies,
   acceptance criterion and smallest useful check. Separate fixes from owner
   decisions and missing evidence.
10. **Engineering disposition and open questions**: use `Material defects
    identified`, `No material defects found in examined scope`, or `Insufficient
    evidence`, with scope/limitations. State which decisions/evidence are needed
    next. An empty findings list never proves general correctness or release
    readiness.

## Final consistency check

Confirm all fourteen lenses are accounted for; every important ecosystem
boundary has versions, ownership and an evidence disposition; book terminology
has been traced through actual reviewed sources; findings are deduplicated;
severity/confidence/evidence are distinct; and each consequential issue has a
reproducer or labeled source-based reasoning and a concrete follow-up.

Do not claim actual team endorsement, compatibility with unexamined versions,
passed checks that did not run, safety beyond declared trust assumptions, or
readiness to publish. Keep release-specific decisions with the release gate.
