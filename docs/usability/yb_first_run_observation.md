# White Belt First-Run Observation

This protocol evaluates the 0.4 White Belt MVP authoring journey without
coaching the participant through individual commands. The established `yb_`
file and script names are retained only for release-automation compatibility.

## Participant

A process-improvement professional who is comfortable creating a basic process
map but is not a FLO contributor and has not used FLO before.

## Starting condition

- A supported Python runtime and the documented FLO installation path are
  available.
- The participant receives only the maintained quickstart.
- No repository checkout or development environment is required.

## Task

Within ten minutes, the participant should:

1. Create a named starter model.
2. Change at least one task name to match a familiar business process.
3. Validate the model.
4. Correct one validation error using the diagnostic alone.
5. Render a readable single-page SPPM SVG.
6. Export canonical JSON.

Record elapsed time, requests for help, failed commands, diagnostic
comprehension, and whether the final diagram is understandable without an oral
explanation.

## Acceptance

The journey passes only when all artifacts are produced in ten minutes or less
without contributor intervention. `scripts/check_yb_journey.py` is the
automated packaging and command rehearsal; it does not substitute for this
representative-user observation.
