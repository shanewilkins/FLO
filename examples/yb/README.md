# Yellow Belt visual acceptance corpus

These four models define the first presentation-readiness slice for simple
process-improvement work:

- `linear.flo` — a basic SPPM mainline
- `simple_decision.flo` — a two-outcome SPPM branch
- `three_lane_handoff.flo` — a responsibility-oriented swimlane handoff
- `rework_loop.flo` — an SPPM decision with an explicit correction loop

`tests/integration/test_yb_visual_acceptance.py` checks source-to-SVG rendering,
complete layout geometry, start/end progression, node separation, lane order,
and explicit rework geometry. The fixtures are deliberately small enough for
first-time authors to understand and modify.
