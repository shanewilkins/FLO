# ADR: Domain-Based Governance And Normative Registers

Status: accepted

Date: 2026-08-09

## Context

FLO values explicit governance, durable requirements, specifications, schemas,
ADRs, tests, and user documentation. The earlier governance model placed these
artifacts in one total authority hierarchy and required broad synchronized
updates. It also required lifecycle status metadata on every design document.

That model improved visibility but made unrelated authority domains compete,
duplicated release and decision information, and created administrative work
for implementation-only changes. Fragile source-section references and broad
stale-text checks increased the cost without improving the product contract.

FLO now has a clearer product audience: process-improvement professionals using
plain-text process models for visualization and downstream analysis. The
governance system must protect that product contract without becoming a second
product to maintain.

## Decision

FLO adopts Governance v2 as defined in `docs/GOVERNANCE.md`.

1. Authority is assigned by domain rather than by one global document order.
2. The user and technical CSV registers remain normative and retain immutable
   IDs, but use controlled release and state fields with direct contract
   references.
3. Changes are classified as scope, contract, implementation, or documentation
   changes and update only the artifacts relevant to that class.
4. ADR lifecycle state is controlled; ordinary explanatory design notes do not
   require a governance status header.
5. The roadmap remains a milestone narrative. Item-level release views derive
   from the normative registers.
6. Permanent policies are limited to durable governance, safety, privacy, and
   product-scope boundaries.
7. Governance automation validates structural and behavioral signals rather
   than policing explanatory prose broadly.

## Consequences

Positive consequences:

- one authoritative home exists for each type of decision
- requirement traceability and immutable IDs are preserved
- implementation-only work carries less documentation overhead
- release views can be generated from the normative registers
- ADRs retain rationale without competing with current contracts
- governance checks become more deterministic and less fragile

Costs and risks:

- the registers, documentation map, and checks require a one-time migration
- contributors must identify the authority domain rather than applying a
  memorized total ordering
- pruning duplicated technical requirements requires care
- generated roadmap views require small supporting tooling

These risks are acceptable because the domain table and four change classes
provide a smaller, more accurate decision procedure than the previous model.

## Alternatives Considered

### Keep the total hierarchy and add more checks

Rejected because it would preserve the source of duplication and increase
administrative burden.

### Make only specs and schemas normative

Rejected because product scope, release ownership, acceptance, privacy, and
cross-cutting quality constraints would lose an explicit home.

### Merge user and technical requirements into one register

Rejected for now because product outcomes and cross-cutting engineering
constraints serve different review audiences. The technical register will be
pruned rather than merged.

### Make all documentation non-normative

Rejected because FLO's language, artifact, interoperability, and safety
contracts require explicit durable governance.
