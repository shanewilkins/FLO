# SPPM Root Cause Debugging Workflow

Status: Active working procedure
Scope: Finding rendering root causes when SPPM DOT output and final SVG output disagree

## 1. Purpose

This document defines the procedure for debugging SPPM rendering defects,
especially cases where:

- routing logic appears correct
- emitted DOT looks correct
- final Graphviz SVG still renders edges incorrectly

The immediate driver is the current attachment regression in the SPPM showcase,
where rework-related arrows still enter or exit task cards from the wrong side in
the final image.

## 2. Core rule

The rendered image is the source of truth.

We do not treat any of the following as sufficient proof that a bug is fixed:

- route-plan snapshots
- DOT string assertions
- presence of `headport`, `tailport`, or endpoint syntax in DOT

A rendering bug is fixed only when the final SVG satisfies the visual contract.

## 3. Visual contract

For SPPM default rendering, the minimum attachment contract is:

- mainline left-to-right edges enter tasks from the west side and leave from the
  east side
- branch-to-rework edges enter rework tasks from the west side
- rework-return edges leave rework tasks from the east side
- returns into mainline tasks enter from the west side
- no rework edge should appear to enter or exit from the top unless the chosen
  orientation explicitly requires that behavior

If the SVG violates this contract, the bug remains open even if all text-based
tests pass.

## 4. Debugging model

Every rendering issue must be analyzed as a pipeline with separate failure
boundaries:

1. Semantic intent
2. Routing-plan selection
3. DOT serialization
4. Graphviz interpretation
5. Final SVG geometry

We debug by falsifying one layer at a time instead of jumping between symptoms.

## 5. Required workflow

## 5.1 Step 1: state the failing image-level claim

Start with one exact, falsifiable statement about the rendered image.

Examples:

- The return edge into Intake enters from the bottom instead of the west side.
- The rework branch into Rework Quality enters from the top instead of the west
  side.

Avoid vague problem statements such as "arrows are messed up" or "routing looks
bad".

## 5.2 Step 2: isolate one edge

Choose one specific failing edge and ignore the rest of the diagram until that
edge is explained.

Good candidates:

- the return edge from `rework_intake` to `intake`
- the branch edge from `qa` to `rework_quality`

Do not attempt to explain the full showcase at once.

## 5.3 Step 3: reduce to the smallest reproducer

Build the smallest graph that still exhibits the same visual defect.

The preferred reproducer contains only:

- one start node
- one mainline task
- one decision
- one rework task
- one return edge to a mainline task or one branch edge to a rework task

The reproducer should remove unrelated layout pressure, extra branches, and wrap
noise.

## 5.4 Step 4: inspect the routing plan

For the chosen edge, capture the route semantics before DOT emission.

Record at least:

- source node
- target node
- route kind
- selected tail side
- selected head side
- selected slot names
- whether the edge is treated as branch-out or return

If the route semantics are wrong here, the bug is in routing selection rather
than Graphviz behavior.

Primary code surface:

- `src/flo/render/_sppm_routing.py`

## 5.5 Step 5: inspect the emitted DOT for the same edge

Verify that the exact serialized edge matches the route intent.

Questions to answer:

- Did the expected port name survive serialization?
- Did the expected compass direction survive serialization?
- Did an intermediate corridor or anchor alter the effective endpoint?
- Did endpoint rewriting change the node or port unexpectedly?

If route intent is correct but DOT is not, the bug is in DOT serialization.

Primary code surface:

- `src/flo/render/_graphviz_dot_sppm.py`

## 5.6 Step 6: test whether Graphviz honors the chosen port

If DOT appears correct but SVG is wrong, treat Graphviz interpretation as the
active hypothesis.

Use discriminating checks:

- simplify the target task-card HTML table so ports live on obvious outer cells
- remove corridor nodes for one edge and compare the result
- compare the same edge against a simpler control node shape with known port
  behavior

This step exists to distinguish between these cases:

- Graphviz is ignoring the intended port
- Graphviz is honoring the port, but the port is located in the wrong visual
  place within the HTML table
- an intermediate segment changes the last visible approach angle

## 5.7 Step 7: inspect final SVG geometry directly

When necessary, inspect the rendered SVG itself rather than relying only on the
browser screenshot.

Look for:

- the final path segment before the arrowhead
- the arrowhead polygon position relative to the task-card border
- whether the edge lands on the outer boundary or an interior table region

This confirms whether the visual error is truly an attachment problem or a path
shape problem.

## 5.8 Step 8: change one variable at a time

After identifying the most likely layer, make the smallest possible edit that
can disconfirm the active hypothesis.

Examples:

- move a west-side port from an interior content cell to a dedicated outer cell
- bypass corridor emission for one reproducer edge
- force a simpler HTML label layout temporarily

Do not combine routing changes, label-structure changes, and corridor changes in
one step.

## 5.9 Step 9: validate at two levels

After each substantive edit, run:

1. the narrowest text-level check that covers the edited layer
2. the smallest rendered SVG check that covers the failing edge

Examples:

- routing or DOT unit tests
- minimal repro DOT generation
- minimal repro SVG generation
- showcase SVG verification only after the minimal repro is correct

## 6. Working hypotheses for the current regression

Current leading hypotheses, in order:

1. Graphviz is honoring endpoint syntax, but the HTML task-card port is placed in
   a cell whose visual geometry does not correspond to the outer west or east
   border.
2. Corridor segmentation is causing the final visible segment to approach the
   correct port from the wrong direction, making the attachment appear top- or
   bottom-based.
3. Routing intent differs between branch-out and return edges in a way that is
   not reflected cleanly in the task-card label structure.

The current evidence does not support treating DOT string correctness alone as a
fix.

## 7. Immediate execution plan

We will follow this order:

1. Select one failing edge from the showcase.
2. Build a minimal reproducer for that edge.
3. Trace that edge across routing plan, DOT output, and SVG geometry.
4. Simplify the HTML task-card port structure if DOT is correct but SVG is not.
5. Rebuild the minimal repro until the image-level contract passes.
6. Rebuild the full showcase and confirm the same class of edge is visually
   correct there.

## 8. Exit criteria

We consider the root cause identified only when all of the following are true:

- one specific failing edge is explained end-to-end across the rendering pipeline
- the minimal reproducer renders correctly in SVG
- the fix is expressible as a concrete cause, not just a tuning adjustment
- the full showcase confirms the same attachment behavior is corrected

At that point we can promote the fix from local diagnosis to general SPPM
renderer behavior.

## 9. Phase 1 execution log (2026-04-29)

Phase 1 status: completed.

Step 1: failing image-level claim

- The rework return edge from `rework_intake` to `intake` enters Intake Request
  from below instead of from the west side in the rendered SVG.

Step 2: isolated edge

- Isolated edge: `rework_intake -> intake` (rework return).

Step 3: minimal reproducer

- Reproducer source: `examples/reference/sppm_attachment_minimal_repro.flo`
- Reproducer DOT: `renders/reference/sppm_attachment_minimal_repro.dot`
- Reproducer SVG: `renders/reference/sppm_attachment_minimal_repro.svg`

Observed result:

- The minimal reproducer preserves the same attachment defect, confirming that
  the issue is not dependent on full showcase complexity.

Next phase:

- Proceed to Phase 2 (Diagnose): trace the same edge through routing intent,
  DOT emission, Graphviz interpretation, and final SVG geometry.

## 10. Phase 2 execution log (2026-04-29)

Phase 2 status: completed for isolated edge `rework_intake -> intake`.

Step 4: routing-plan intent

- Routing snapshot for the isolated edge resolves to:
  - segment 1: `rework_intake -> __sppm_rework_corridor_rework_intake_intake`
    with `tailport="out_0:e"`
  - segment 2: `__sppm_rework_corridor_rework_intake_intake -> intake`
    with `headport="in_1:w"`
- This confirms routing intent is west-side re-entry into Intake.

Step 5: DOT emission

- Emitted DOT serializes the same segment as:
  - `"__sppm_rework_corridor_rework_intake_intake" -> "intake":"in_1":w [...]`
- This confirms DOT serialization preserves the routing intent.

Step 6 and 7: Graphviz interpretation and final SVG geometry

- In the rendered SVG, the same edge appears as:
  - title `__sppm_rework_corridor_rework_intake_intake->intake:w`
  - terminal geometry is vertical and not visually west-side ingress into the
    Intake task card.
- This indicates Graphviz geometry is not honoring the intended named-port
  ingress behavior under current rendering conditions.

Controlled A/B checks

- A/B 1 (quoted vs unquoted endpoint port names): no meaningful change in final
  geometry for the isolated failing edge.
- A/B 2 (`splines=ortho` vs `splines=polyline`): geometry changes, confirming
  spline mode materially affects attachment behavior; however the final segment
  still does not satisfy the intended side-ingress contract.

Phase 2 conclusion

- Fault boundary is narrowed to Graphviz interpretation + task-label port
  geometry interaction, not routing-plan intent and not basic DOT segment
  selection.
- The next work should focus on label port-cell structure and/or connector
  strategy changes that remain robust under default SPPM spline mode.

## 11. Phase 3 execution log (2026-04-29, attempt 1)

Phase 3 status: in progress (attempt 1 completed, not yet fully resolved).

Changes tested one variable at a time:

1. Port-cell structure refactor

- Updated task-card HTML label wrapper so side ports are emitted via dedicated
  left and right stack columns instead of rowspan-coupled row cells.
- Result: no regression in focused SPPM tests, but isolated SVG attachment defect
  remained.

2. Spline mode switch for SPPM default

- Changed SPPM graph spline mode from `ortho` to `polyline`.
- Updated SPPM-specific tests accordingly.
- Result: focused SPPM tests pass; SVG attachments for rework edges now target
  west-side coordinates rather than top-entry behavior, but visual ingress can
  still collapse near lower-left corners in some cases.

Current status after attempt 1:

- Text-level routing and DOT checks still pass.
- Image-level contract is improved but not fully satisfied for clean, consistent
  side-entry presentation.

Next candidate experiment (single variable):

- Add a dedicated pre-target approach anchor for rework return edges and force a
  short final segment into the west side, so the last segment approaches from the
  side rather than from below.