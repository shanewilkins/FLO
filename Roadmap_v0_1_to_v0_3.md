# FLO Roadmap (v0.1 -- v0.3)

## v0.1 --- Minimal Modeling Core

Scope:

-   YAML-based FLO syntax\
-   Core constructs (process metadata, lanes, steps, decisions)\
-   Compilation to FLO IR\
-   IR validation\
-   DOT renderer (flowchart + swimlane)\
-   CLI: `flo compile`, `flo render`

Non-goals:

-   Parallelism\
-   Telemetry ingestion\
-   Simulation\
-   Expressions

Deliverable:

Stable FLO v0.1 spec + reference implementation.

------------------------------------------------------------------------

## v0.2 --- Static Lean Analytics Layer

Scope:

-   Static graph analytics:
    -   Handoff count\
    -   Rework loop detection\
    -   Longest path\
    -   Step classification summaries\
-   Optional annotations (`sla_target_seconds`, `value_class`)\
-   Improved diagnostics

Deliverable:

FLO usable for Lean modeling and structural analysis.

------------------------------------------------------------------------

## v0.3 --- Telemetry Alignment & Trace Model

Scope:

-   Event schema (`case_id`, `activity_key`, `timestamp`)\
-   Basic conformance alignment\
-   Node visit frequency\
-   Path frequency\
-   Rework rate from event data

Non-goals:

-   Full process mining suite\
-   High-performance streaming engine

Deliverable:

FLO bridges declarative modeling and measured execution reality.
