# FLO Documentation Map

This directory is the top-level navigation hub for FLO documentation.

Use it to answer two questions quickly:

- where a document should live
- which document is authoritative when topics overlap

## Documentation Roles

FLO uses four main documentation layers.

1. `docs/policy/`
   - governance rules
   - authority boundaries
   - update policy for specs, schema, implementation, and tests

2. `docs/specs/`
   - normative human-readable semantics
   - language meaning
   - diagram meaning
   - CLI-facing contracts

3. `schema/`
   - machine-readable structural contracts
   - canonical serialized IR and type shapes

4. `docs/design/`
   - explanatory architecture
   - implementation strategy
   - migration plans
   - ADRs and historical context

Supporting user-facing documents live at the top of `docs/`:

- `User_Manual.md` for how to use FLO
- `CHANGELOG.md` for released changes
- `FLO_Manifesto.md` for product and modeling principles

Working notes that are still being shaped should stay outside this tree until
they are ready to become design, policy, spec, or user-facing docs.

## Authority Order

When documents overlap or disagree, resolve conflicts in this order:

1. `schema/`
2. `docs/policy/`
3. `docs/specs/`
4. `src/flo/`
5. `README.md` and `docs/User_Manual.md`
6. `docs/design/`

## Quick Navigation

Start here based on the question you are trying to answer.

- What is authoritative: `docs/policy/authoritative_artifacts.md`
- What does FLO source mean: `docs/specs/core_language.md`
- What does a diagram type mean: `docs/specs/`
- What is the serialized contract: `schema/flo_ir.json` and `schema/flo_types.json`
- Why was it designed this way: `docs/design/`
- How do I use the tool: `docs/User_Manual.md`
- What changed recently: `docs/CHANGELOG.md`

## Placement Rules

Put a document in `docs/policy/` when it defines governance or source-of-truth rules.

Put a document in `docs/specs/` when it defines required semantics or diagram behavior.

Put a document in `docs/design/` when it explains rationale, architecture, migration sequencing, or implementation boundaries.

Keep active scratch plans in `notes/` until they are ready to be promoted into the documentation set.

## Current Gaps To Watch

- Draft and proposed design notes should either advance, be archived, or be marked explicitly as still open.
- Historical design notes should point readers back to the current spec or schema authority.
- File names in `docs/design/` should avoid implying normative status unless the file is explicitly non-normative.
