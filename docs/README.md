# FLO Documentation Map

FLO uses domain-based governance: each type of question has one authoritative
home. The complete rules are in `GOVERNANCE.md`.

## Authority By Question

| Question | Start here |
| --- | --- |
| What must FLO deliver, and by when? | `requirements/` |
| What does FLO source or a public interface mean? | `specs/` |
| What serialized shape is valid? | `../schema/` |
| What safety, privacy, scope, or governance rule applies? | `GOVERNANCE.md` and `policy/` |
| Why was a durable decision made? | `design/adr/` |
| How is a component implemented? | `design/` and source code |
| How does a user accomplish a task? | `Quickstart.md` and `User_Manual.md` |

No total document hierarchy applies across these domains. A requirement owns
scope but does not silently change current semantics; an ADR records rationale
but does not override a specification; a schema owns serialized structure but
does not set release priority.

## Main Document Sets

- `requirements/`: normative user outcomes and cross-cutting technical
  constraints, including the committed path through 1.0
- `specs/`: normative current language, CLI, diagram, and interchange meaning
- `policy/`: durable scope and privacy boundaries
- `design/adr/`: accepted and superseded durable decisions
- `design/`: explanatory architecture, implementation strategy, renderer
  notes, migration plans, and history
- `../schema/`: machine-readable canonical structural contracts

Supporting documents:

- `Quickstart.md`: shortest end-to-end user path
- `User_Manual.md`: complete user reference
- `ROADMAP.md`: milestone themes, MVP meaning, and release gates
- `CHANGELOG.md`: released changes
- `FLO_Manifesto.md`: product and modeling principles

## Placement Rules

- Put a user outcome or release commitment in the appropriate requirement
  register.
- Put language, CLI, diagram, or public-interface meaning in a specification.
- Put serialized structure in a schema.
- Put durable safety, privacy, scope, or governance rules in policy.
- Put decision rationale in an ADR.
- Put implementation explanation and temporary migration plans in design.
- Put task-oriented teaching in the Quickstart or reference guide.

Working notes stay in `notes/` until their role is clear. Completed plans should
move to history or point directly to the current contract.
