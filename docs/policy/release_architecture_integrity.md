# Release architecture integrity

Status: current

## Purpose and scope

Every FLO release, including patch releases, must establish a known-good baseline
whose implementation and effective documented architecture agree. This gate
applies before the next release is cut and to every release thereafter. The
cross-cutting commitment is TR-118 in the
[technical requirements register](../requirements/technical_requirements.csv).

## Architecture acceptance gate

A release candidate must satisfy all of the following:

1. Identify the accepted architecture decisions and boundaries effective for the
   shipped scope. Distinguish current obligations from explicitly future target
   designs, proposed structures, and deferred product capabilities.
2. Verify the implementation against those obligations: dependency direction,
   responsibility and policy ownership, stage contracts, data flow, public and
   internal entrypoints, and diagnostic delivery boundaries. Import checks alone
   are insufficient when responsibility can drift without changing imports.
3. Resolve every identified violation of an effective boundary before release.
   Refactor to restore the boundary, or explicitly review and accept a justified
   architecture change and update the affected decisions, contracts, and checks.
   Updating prose merely to conceal implementation drift is not acceptance.
4. Keep current architecture documentation accurate. Clearly label future targets
   and incomplete migrations; do not describe intended behavior as implemented.
5. Protect important boundaries with executable checks where feasible, and record
   review evidence for obligations not amenable to automation. Passing functional
   tests, coverage thresholds, or golden comparisons does not alone establish
   architecture integrity. Existing lint exclusions are not architecture waivers.
6. Verify the final candidate and installed distribution from a clean checkout on
   the declared platform matrix. Evidence must correspond to the reviewed source
   revision and packaged artifacts, rather than to an earlier passing tree.

An open architecture violation blocks release. A plan to repair it later does not
satisfy this gate. Any exception requires an explicit user-approved policy change;
contributors must not infer an exception from scheduling pressure or a green test
suite.

## Known-good baseline record

The release acceptance record must identify:

- the immutable source revision and release tag;
- the effective architecture decisions and boundaries reviewed, including accepted
  changes since the previous baseline;
- the architecture findings and their dispositions, with no unresolved violations;
- executable boundary and functional checks, platform/installed-consumer results,
  and remaining limitations that do not violate the accepted architecture;
- distribution and representative artifact identities or hashes.

The accepted release becomes the recorded starting baseline for the next release
cycle. Work may intentionally change architecture during a cycle, but the next
candidate must reconcile implementation, accepted decisions, documentation, and
verification before it can replace that baseline. The first baseline established
under this policy requires a repository-wide boundary review; later cycles also
verify that unaffected baseline boundaries remain intact.

## Current candidate

The current White Belt candidate has completed architecture remediation and clean
candidate acceptance. Its [acceptance record](../design/white_belt_candidate_acceptance.md)
identifies reviewed decisions, closed findings, immutable source/tested revisions,
platform checks, and distribution identities. This is candidate acceptance, not a
published release baseline. The eventual versioned release must satisfy this gate
and record its immutable tag and final artifacts before publication.
