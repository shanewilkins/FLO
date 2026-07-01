# SPPM Publication and Feature Completeness Design

Status: draft

## 0) Locked Decisions (May 2026)

The following decisions are approved as the working product direction for SPPM:

- SPPM publication completeness is the current top product priority.
- SPPM remains a static-first publishing target for now; interactive views are explicitly deferred.
- Swimlanes are out of scope for this iteration.
- Readability has priority over geometric symmetry and over exposing low-level layout controls.
- The FLO source model remains unchanged; hierarchy, pagination, and publication projections are derived automatically by the compiler and renderer pipeline.
- Explicit subprocess nodes are the authoritative decomposition boundaries for hierarchical SPPM publication.
- Default top-level SPPM output collapses subprocesses.
- Subprocess-focused child maps are emitted automatically when the chosen publication profile or measured complexity justifies them.
- Inline subprocess expansion is optional, static, and bounded by readability rules; it is not the default publication mode.
- Headers, footers, continuation anchors, and page metadata are part of the publication surface, not manual post-processing.
- Stable visible step references must include node identity derived from `node_id`.
- Diagnostics must support both warnings and hard failures, with strict publication modes failing rather than silently degrading.

## 1) Purpose

This specification defines what it means for FLO's SPPM renderer to be feature complete for static publication and long-form process communication.

The goal is not a perfect graph-layout engine. The goal is a deterministic, readable, hierarchy-aware publishing system that can render long and complex processes from the same canonical FLO source without forcing authors to rewrite their models for presentation.

## 2) Definition of Feature Completeness

SPPM is feature complete when it can do all of the following from the same FLO source model:

1. Render a readable top-level process performance map for ordinary processes.
2. Render long or complex processes as readable multi-page static artifacts.
3. Preserve SPPM semantics for value class, cycle time, wait time, workers, rework, queues, and decisions.
4. Treat subprocesses as compositional drill-down boundaries.
5. Emit child SPPM maps for subprocess detail without requiring separate authored models.
6. Support bounded inline expansion when it remains readable.
7. Provide stable references and continuation anchors across pages and child maps.
8. Produce publication-ready artifacts with headers, footers, and standalone map context.
9. Enforce readability through explicit diagnostics, warnings, and strict publication modes.

## 3) Non-Goals

The following are out of scope for this phase:

- Swimlane semantics within SPPM.
- Manual page-break authoring in FLO source.
- Freeform user control over geometry, rank constraints, and low-level edge routing.
- Heavy interactive or browser-only rendering dependencies.
- Automatic inference of semantic subprocess boundaries when the author has not modeled them explicitly.
- Optimal graph layout.

## 4) Public Control Surface

SPPM should expose semantic and publication intent, not low-level geometry knobs.

### 4.1 Exposed controls

The public API and CLI surface should remain narrow and intent-based:

- output profile: for example `web`, `book`, `print`, `slide`
- detail level: summary, standard, expanded
- subprocess policy: collapse, auto child-map emission, bounded inline expansion
- pagination policy: auto, off, strict
- focus target: whole process or a selected subprocess
- readability target: page size, width budget, page count and density limits
- diagnostics policy: warn, fail, or force fallback

### 4.2 Internal-only controls

The following should remain implementation details unless a future need proves otherwise:

- raw node spacing
- rank and grouping constraints
- page-break coordinates
- connector dogleg geometry
- exact anchor placement
- cluster padding and border geometry

## 5) Publication Model

SPPM publication needs an internal model above the canonical IR and below the renderer-specific DOT/SVG output.

That publication model should be able to represent:

- a publication set containing one top-level map and zero or more child maps
- one or more page series per map
- page bounds, margins, and document bands
- continuation anchors and continuation targets
- stable step references and cross-map references
- selected projection mode for each map

This model is renderer-independent. DOT, SVG, PDF, and any later interactive view should consume the same publication plan rather than recomputing semantics independently.

## 6) Subprocess Semantics for SPPM

### 6.1 Authoritative boundary

Explicit subprocess nodes are the authoritative hierarchy boundaries for SPPM publication. FLO should not infer new subprocesses automatically as part of core rendering behavior.

Future analysis may suggest candidate groupings, but those suggestions are advisory only and do not replace authored subprocess boundaries.

### 6.2 Default top-level behavior

Top-level SPPM output collapses subprocesses by default.

Rationale:

- preserves SPPM as a performance summary rather than a pseudo-flowchart
- prevents ambiguous double-counting between subprocess parent boxes and child boxes
- keeps long parent maps readable

### 6.3 Child maps

Every explicit subprocess is eligible to have its own child SPPM map.

Automatic child-map emission is controlled by publication profile and complexity heuristics. The renderer should emit child maps automatically when:

- a subprocess exceeds preferred inline readability thresholds, or
- the chosen publication profile requests hierarchical publication output

Child maps must include inherited context:

- parent process reference
- subprocess parent reference
- upstream entry context
- downstream return context

### 6.4 Inline expansion

Inline subprocess expansion is allowed only as a bounded static mode.

Policy:

- it is optional and never the default
- it is limited to one level unless a future spec says otherwise
- it may only be used when readability thresholds remain within budget
- when inline expansion would violate strict or preferred budgets, the system must fall back to collapsed parent plus child map behavior according to diagnostics policy

Inline expansion is for small subprocesses, review drafts, and teaching views. It is not the primary publication strategy for large processes.

## 7) Pagination and Continuation

### 7.1 Shared page model

Pagination must be based on a shared page and canvas abstraction rather than renderer-specific hacks.

The shared model must support:

- document size and output profile defaults
- margins and usable content region
- top and bottom document bands
- page identifiers and page sequence metadata

### 7.2 Page-break behavior

Page breaks should be chosen semantically, not purely geometrically.

Preferred break opportunities include:

- after queues or waits
- after collapsed subprocesses
- before large decision fans
- at low-crossing points on the main spine

Break behavior must be deterministic for the same input and options.

### 7.3 Continuation anchors

SPPM must support explicit continuation anchors when the flow resumes elsewhere.

Rules:

- main-spine continuation is visually prominent
- secondary branch and rework continuation is lighter but still explicit
- labels must be stable across re-renders for the same model and options
- continuation anchors must reference visible step identifiers, page identifiers, or both

Parent-map continuation and child-map drill-down are related but distinct concepts and must not be conflated.

## 8) Headers, Footers, and Standalone Context

Publication-ready SPPM output must support reusable document bands.

### 8.1 Header content

At minimum, a header should be able to show:

- process title
- process identifier or publication identifier
- selected detail level or publication level
- page number within the current map series
- optional report metadata such as owner, revision, or publication date

### 8.2 Footer content

At minimum, a footer should be able to show:

- optional summary metrics or explanatory notes
- continuation metadata where useful
- parent or child map references where useful

Headers and footers are publication bands. Their semantic content belongs to SPPM, but their layout primitives should be shared.

## 9) Step Reference Policy

Stable visible step references are mandatory for publication completeness.

Rules:

- each published step must expose a stable reference token derived from `node_id`
- step references must remain consistent across parent maps, child maps, and continuation labels
- human-facing labels may remain descriptive, but stable references must be visible somewhere in the node or attached annotation

Step references are required for:

- cross-page continuation
- subprocess drill-down references
- diagnostics
- review and discussion in print and static artifacts

## 10) Readability and Diagnostics Policy

SPPM publication must enforce readability explicitly.

### 10.1 Warning conditions

Warn when output is still publishable but degraded, such as:

- too many nodes on a page
- dense branch crossings
- overfull labels
- inline expansion exceeding preferred density
- child maps that exceed preferred but not hard limits

### 10.2 Error conditions

Fail when the requested publication mode cannot satisfy hard constraints, such as:

- strict publication mode cannot fit within configured limits
- requested expansion depth exceeds allowed policy
- continuation references would be ambiguous
- a required child map cannot be rendered within hard limits even after pagination

### 10.3 Fallback behavior

In non-strict mode, FLO may fall back automatically to a more readable publication mode, for example:

- expanded inline to collapsed plus child maps
- denser profile to a more compact profile

Automatic fallback must emit an explicit warning describing the change.

## 11) Default Publication Behavior

The default publication behavior for `--diagram sppm` should be:

1. render a top-level summary SPPM
2. collapse subprocesses on the top-level map
3. apply automatic pagination only when needed
4. include visible step references
5. emit child maps automatically only when the profile or complexity rules require them

This default should optimize for static readability and predictable output.

## 12) Implementation Priorities

The implementation sequence should follow this order:

1. define the shared publication, page, and canvas model
2. implement parent-only subprocess handling for SPPM
3. implement pagination, document bands, and continuation anchors
4. implement automatic child-map emission for subprocesses
5. implement stable step references across all SPPM publication views
6. implement readability diagnostics and strict publication modes
7. implement bounded inline subprocess expansion

Inline expansion is intentionally last because it depends on the publication and readability infrastructure.

## 13) Acceptance Criteria for This Spec

This spec is satisfied when the roadmap and implementation can demonstrate all of the following:

- a long process can render into a readable multi-page top-level SPPM
- subprocesses can be collapsed on the parent map and rendered as child maps from the same FLO source
- each page and child map can stand alone with header/footer context
- continuation anchors are stable and readable across page and branch boundaries
- stable step references are visible and consistent
- warnings and strict-mode failures behave deterministically

## 14) Architectural Notes

- Keep semantics in the compiler/publication model; keep geometry in the renderer.
- Do not hardcode DOT-specific logic as the only representation of pagination or hierarchy.
- Static-first design should not block future interactive rendering as long as the publication model remains renderer-independent.
