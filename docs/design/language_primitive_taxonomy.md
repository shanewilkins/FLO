# FLO Language Primitive Taxonomy

Status: accepted

This is an accepted explanatory taxonomy note.
The migration contract is locked in
`docs/policy/language_primitive_migration_contract.md`.
The decision record lives in `docs/design/adr/language_primitive_taxonomy.md`.
Current implemented normative semantics remain in
`docs/specs/core_language.md` until the migration lands in code and tests.

## Purpose

Define the primitive hierarchy FLO should use when evolving from a graph-shaped implementation model into a process-first language.
This note distinguishes first-class domain primitives from organizing structures, quantitative descriptors, and compiled implementation forms.
This note is explanatory only.
Normative language rules belong in `docs/specs/` and authoritative structural contracts belong in `schema/`.

## Why This Note Exists

FLO's implementation already compiles authored process descriptions into a graph-shaped IR.
That IR is useful for validation, rendering, and analysis.
It should not decide the author-facing conceptual model by itself.

The language needs a stable answer to four questions.

1. Which concepts are truly first-class process primitives.
2. Which concepts are relations between primitives rather than primitive objects in their own right.
3. Which concepts are organizing or projection structures rather than core process meaning.
4. Which concepts belong only in compiled IR, analysis, or rendering layers.

## Promotion Tests

A concept should be promoted to a first-class domain primitive only when all or most of the following are true.

1. It changes process meaning rather than only changing presentation.
2. It directly supports process-improvement analysis or diagnosis.
3. A practitioner would naturally say the fact out loud when describing the process.

These tests should be applied before adding new top-level source constructs or new canonical IR concepts.

## Taxonomy Overview

FLO should use six conceptual layers.

1. Domain entities.
2. Control-flow step kinds.
3. First-class relations.
4. Organizing structures.
5. Quantitative descriptors.
6. Derived and compiled forms.

The design goal is to keep author-facing source close to the first five layers and keep generic graph machinery in the sixth.

## 1. Domain Entities

These are the primary nouns of the language.
If one of these changes, the process model itself changes.

### 1.1 Process

- `process`

Meaning:
The overall modeled system of work.

Why first-class:
It anchors identity, scope, versioning, and process-level metadata.

### 1.2 Step

- `step`

Meaning:
An authored unit of work or control point in business sequence.

Why first-class:
Process authors talk in steps before they talk in graphs.
Steps are the main source-level unit of process description.

### 1.3 Item

- `item`

Meaning:
The thing that flows, is transformed, is checked, is transferred, waits, or is reworked.

Why first-class:
Process mapping is fundamentally about flows of material and information.
`item` is the best umbrella term because it works across physical, informational, and mixed processes without carrying execution-instance baggage.

Required first-class item kinds:

- `material`
- `information`

Notes:

- `case` is a useful domain-specific subtype, but not the umbrella term.
- `workpiece` is a useful material-oriented subtype, but not the umbrella term.
- `artifact` remains a plausible synonym in some contexts, but `item` is the preferred authored noun.

### 1.4 Resource

- `resource`

Meaning:
The person or equipment that performs or supports work.

Why first-class:
Real process models almost always need to say who performs the work and what enabling equipment is used.

Required first-class resource kinds:

- `person`
- `equipment`

Notes:

- `team`, `role`, and `system` are important classifications, but they are not themselves the core resource umbrella.

### 1.5 Location

- `location`

Meaning:
The physical or logical place where work occurs or through which items move.

Why first-class:
Location is central to movement analysis, handoff analysis, and many practical process maps.
It matters strongly in manufacturing, healthcare, service operations, and logistics.

## 2. Control-Flow Step Kinds

These are specialized kinds of `step` that change how flow behaves.
They are not just descriptive labels.

- `decision`
- `queue`
- `wait`
- `subprocess`
- `parallel_split`
- `parallel_join`

### 2.1 Decision

Meaning:
A branching control step with labeled outcomes.

### 2.2 Queue

Meaning:
A step that represents waiting before work begins.

Why it stays distinct:
Queueing delay is a different process fact from active work and a different fact from an in-process hold.

### 2.3 Wait

Meaning:
An explicit hold state that does not imply active work.

Why it stays distinct:
Not all waiting is queueing.
Some waits are policy holds, aging periods, cure times, or external dependencies after work has already progressed.

### 2.4 Subprocess

Meaning:
A step that contains or references child process behavior.

Why first-class:
Subprocesses let authors preserve meaningful decomposition without abandoning the top-level process narrative.

### 2.5 Parallel Split And Join

Meaning:
`parallel_split` starts concurrent paths.
`parallel_join` synchronizes concurrent paths.

Why first-class:
Real processes often contain true concurrency.
Concurrency cannot be modeled faithfully as ordinary branching without losing semantic distinction between one-of and all-of flow.

## 3. First-Class Relations

These are the verbs and semantic links of the language.
They are more meaningful than generic graph edges.

### 3.1 Flow Relations

- `sequence`
- `branch`
- `rework`
- `handoff`

Meaning:

- `sequence` is the default next-step relation.
- `branch` is a labeled relation from a control point to one of several next steps.
- `rework` is a loop relation that sends flow back to earlier work.
- `handoff` is a transfer relation across a transition.

Important modeling rule:

- `rework` is a relation, not a step kind.
- `handoff` is a relation, not a lane change and not a step kind.

### 3.2 Work And Flow-Object Relations

- `performed_by`
- `uses`
- `consumes`
- `produces`
- `occurs_at`

Meaning:

- `performed_by` links a step to one or more people.
- `uses` links a step to supporting equipment.
- `consumes` links a step to one or more incoming items.
- `produces` links a step to one or more outgoing items.
- `occurs_at` links a step to a location.

Why first-class:
These relations express how work transforms or transfers items through resources and locations.
Without them, the language knows that steps exist but says too little about what is actually happening.

### 3.3 Handoff Semantics

Handoff uses the accepted hybrid model.

Core rule:
Handoff is a first-class transition-level semantic relation with both inferred defaults and explicit author override.

Meaning:
A meaningful transfer of responsibility, custody, or working context across a transition.

Evidence signals may include:

- lane change
- worker or role change
- system boundary change
- location change
- item custody or producer/consumer change

Evidence is not the same as meaning.
Crossing a lane may imply a handoff, but does not define one.
Staying in the same lane does not rule a handoff out.

Recommended typed handoff kinds:

- `responsibility`
- `information`
- `material`
- `system`
- `location`
- `mixed`

Relationship to rework:
An edge may be both `rework` and `handoff`.
These are distinct semantic dimensions.

## 4. Organizing Structures

These structures are important for grouping, projection, and readability.
They should not be confused with the deepest process primitives.

- `lane`
- `role`
- `team`
- `system`
- process boundary or grouping surfaces

Why secondary:
These concepts help explain ownership and projection.
They do not by themselves define what work is done, what items flow, or how control behaves.

Important modeling rule:
Lane change is a useful inference signal for handoff.
It is not itself the semantic meaning of handoff.

## 5. Quantitative Descriptors

These descriptors are important and often analysis-critical.
They are not the core nouns or core relations of the process language.

- `cycle_time`
- `wait_time`
- `changeover_time`
- `lead_time`
- `value_class`
- `queue_policy`
- `buffer_capacity`
- `handoff_latency`
- `rework_rate`
- `rework_reason`

Why secondary:
These values describe behavior, burden, or quality of the process.
They do not define the basic structural meaning of the process by themselves.

## 6. Derived And Compiled Forms

These constructs remain necessary for implementation.
They should not be treated as the primary conceptual model for authors.

- generic `node`
- generic `edge`
- inferred movement summaries
- inferred handoff summaries
- inferred rework classifications
- renderer-specific routing artifacts

Important modeling rule:
Nodes and edges remain valid compiled IR structure.
They are not the preferred author-facing primitives.

## Locked Primitive Set

The following set is the current recommended primitive hierarchy for FLO.

### Core domain nouns

- `process`
- `step`
- `item`
- `resource`
- `location`

### Required subkinds

- `material`
- `information`
- `person`
- `equipment`

### Control-flow step kinds

- `decision`
- `queue`
- `wait`
- `subprocess`
- `parallel_split`
- `parallel_join`

### First-class relations

- `sequence`
- `branch`
- `rework`
- `handoff`
- `performed_by`
- `uses`
- `consumes`
- `produces`
- `occurs_at`

### Organizing but secondary concepts

- `lane`
- `role`
- `team`
- `system`

### Non-primitive compiled forms

- generic `node`
- generic `edge`
- inferred analytics and renderer artifacts

## Source-Language Consequences

This taxonomy implies a process-first source language.

Authors should primarily describe:

- ordered steps
- control behavior through decisions, parallel splits, parallel joins, waits, and queues
- items and item transformations
- resources and locations
- explicit rework and handoff semantics where they matter

Authors should not be forced to assemble arbitrary graph structure for ordinary process descriptions.

Top-level `transitions` or `edges` can remain an advanced or compatibility-oriented authoring surface.
They should not be presented as the defining conceptual model of the language.

## Stress Test

The following stress tests check whether the taxonomy stays coherent across very different process domains.

### Insurance Claims

Primary item kind:
`information`

Why the taxonomy holds:

- the claim, attachments, policy details, and adjudication record are all naturally modeled as `item`s
- handoffs between intake, examiner, medical review, fraud review, and payment are central
- rework loops for missing information and re-submissions are central
- parallel verification or screening paths are plausible and meaningful

Conclusion:
The taxonomy fits strongly.
`item` works better than `case` as the umbrella term because `case` remains available as a subtype without taking over the whole ontology.

### Bakery

Primary item kind:
`material`

Why the taxonomy holds:

- dough, trays, and finished product are clearly `item`s
- order tickets and labeling instructions still fit as `information` items
- queues, waits, and changeover are all important and distinct
- people, equipment, and location are all central

Conclusion:
The taxonomy fits strongly.
The bakery case validates distinct waiting semantics and first-class equipment and location.

### Hospital Lab

Primary item kinds:
`material` and `information`

Why the taxonomy holds:

- the specimen is a material item
- the accession record, test order, and result are information items
- handoffs across collection, couriering, accessioning, analyzer use, review, and reporting are central
- rework includes recollection, reruns, and reflex testing
- parallel branches are often required for multi-test workflows

Conclusion:
The taxonomy fits very strongly.
This is the clearest argument for making `information` first-class alongside `material`.

### IT Support

Primary item kind:
`information`

Why the taxonomy holds:

- the ticket and attached diagnostic information are naturally modeled as `item`s
- handoffs across service desk, specialist teams, vendors, and requesters are central
- rework loops and reopen loops are central
- parallel troubleshooting or approval paths are plausible

Conclusion:
The taxonomy fits strongly.
This case shows why `workpiece` and `case` are both too narrow as the umbrella term.

### Water Pump Manufacturing

Primary item kinds:
`material` and `information`

Why the taxonomy holds:

- parts, subassemblies, and finished pumps are material items
- routings, torque specs, quality records, and test results are information items
- machining, inspection, assembly, test, and pack-out involve real handoffs even when lane changes are absent
- rework and parallel branches are essential rather than exceptional

Conclusion:
The taxonomy fits very strongly.
This case validates parallel split and join, item duality, and typed handoff semantics.

## What This Taxonomy Rejects

The taxonomy intentionally rejects the following as primary author-facing primitives.

- raw graph nodes and edges as the normal authoring model
- lane change as the definition of handoff
- rework as a task kind rather than a relation
- purely document-oriented or manufacturing-oriented umbrella nouns for the flow object
- simulation semantics as part of the core language primitive set

## Near-Term Implementation Implications

When this taxonomy is ratified, follow-on work should align the following layers.

- canonical source examples and conformance fixtures
- source parser and compiler normalization
- canonical IR and typed metadata where the new primitives require structural support
- renderers and exports that read IR semantics
- test fixtures and regression baselines
- user-facing and normative documentation

This note does not define the implementation plan.
That plan should live separately under `notes/` so it can track concrete phases, file moves, and test strategy.

## References

- `docs/specs/core_language.md`
- `docs/User_Manual.md`
- `schema/flo_ir.json`
- `schema/flo_types.json`
- `docs/design/history/ontology.md`
- `docs/design/typed_metadata.md`
