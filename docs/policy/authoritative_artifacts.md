# FLO Authoritative Artifacts Policy

Purpose: define where authoritative truth lives for FLO semantics, diagram
specifications, implementation behavior, and explanatory design notes.

## Document classes

FLO uses four document classes:

1. Policy documents
   - Location: `docs/policy/`
   - Purpose: define governance rules, authority boundaries, and update policy.
   - Status: normative.

2. Specification documents
   - Location: `docs/specs/`
   - Purpose: define what FLO artifacts and diagram types mean.
   - Status: normative.

3. Schema documents
   - Location: `schema/`
   - Purpose: define machine-readable structural contracts.
   - Status: normative for serialized structure.

4. Design documents
   - Location: `docs/design/`
   - Purpose: explain implementation strategy, architecture, and refactor intent.
   - Status: explanatory, not authoritative when a policy or spec exists.

## Source of truth hierarchy

When two artifacts disagree, resolve conflicts in this order:

1. Structural schema contract
   - `schema/flo_ir.json`
   - Governs serialized IR shape.

2. Project policy
   - `docs/policy/`
   - Governs authority boundaries and document roles.

3. Language and diagram specifications
   - `docs/specs/`
   - Governs FLO semantics and renderer-specific behavior expectations.

4. Executable implementation
   - `src/flo/`
   - Must conform to schema, policy, and specs.

5. User-facing summaries
   - `README.md`, `docs/User_Manual.md`
   - Should summarize current behavior without contradicting policy or specs.

6. Design notes
   - `docs/design/`
   - Explain why the implementation is shaped as it is, but do not override
     policy or specs.

## Change policy

For any change to FLO semantics, IR meaning, or diagram behavior:

1. Update the relevant spec in `docs/specs/`.
2. Update schema if the serialized contract changed.
3. Update implementation.
4. Update tests.
5. Update README or user manual if user-visible behavior changed.

For implementation-only refactors with no behavior change:

1. Update design notes only if they would otherwise become misleading.
2. Do not change specs unless observable behavior or normative meaning changed.

## Practical rule

If a future contributor asks, "What is an SPPM?" or "What is a spaghetti map in
FLO?", the answer should live in `docs/specs/`, not in renderer code and not in
an implementation design note.

If a future contributor asks, "What is the FLO process model?", the normative
answer should also live in `docs/specs/`.
