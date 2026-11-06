# Riverside teaching journey

Riverside is a fictional request-review service. A coordinator checks incoming
requests, asks the requester to clarify incomplete requests, and repeats review.
Complete requests need both technical and finance checks in parallel before the
coordinator issues a response. The proposed state uses a shared intake checklist
and review alerts to reduce known waiting; this is a hypothesis to test.

From the repository root, after the development setup in the main README:

```sh
uv run --locked flo validate examples/reference/riverside/current.flo
uv run --locked flo validate examples/reference/riverside/proposed.flo
uv run --locked python examples/reference/riverside/run.py
```

Open `renders/riverside/comparison.html` in a browser. It contains both states,
compact maps, full timing tables and analysis findings. Print to paper or PDF
using A3 portrait at 100% scale, with browser headers/footers disabled. Each map
and evidence table starts a new page. The HTML embeds its SVGs and works offline.
The script also writes individual SVGs, canonical JSON, inspection JSON and
structured diagnostics. To choose a destination, pass `--output PATH`.

Open [riverside.ipynb](riverside.ipynb) for the describe → validate → render →
revise lesson and an intentional selector error with its repair. Use the same
Python environment as FLO; Jupyter/IPython are optional notebook tooling and are
not FLO runtime dependencies. The script requires no notebook packages.

## Evidence conventions

- `current.flo`: invented activity summaries, labeled `basis: simulated` and
  `extensions.riverside.origin: synthetic teaching summary`. Counts of 12
  mainline and 3 clarification activity executions are synthetic, not observed
  Riverside data or unique-request counts. Repeated visits may be included.
- `proposed.flo`: workshop assumptions, labeled `basis: estimated`, with no
  observation count. Known waits are halved; processing and topology stay fixed.
- `evidence.json`: local source summaries keyed by state, step and field. Each
  profile's `evidence_ref` identifies its JSON Pointer. This fixture contains
  supplied summaries, not raw event observations or computed statistics.
- All displayed statistics are means in minutes. `primary` chooses display;
  `analysis_input` independently chooses analysis. Full JSON preserves profiles.
- Missing clarification waiting and setup are unknown and remain omitted.
  The explicitly supplied issue wait of `0 min` remains visible. Never fill an
  unknown with zero. Estimated sample counts are unknown, not zero.
- For actual observations, use `basis: observed`, real counts and units, a
  compatible cohort/window and an identifiable source. FLO validates evidence
  structure, not whether a source is true, available or statistically sound.

## Validation and comparison exercises

1. Read the process description, then locate its roles, handoffs, completeness
   decision, clarification return, parallel split and matching join in the source.
2. Validate. Missing timing is a warning; inspect `missing_fields` in diagnostic
   JSON and collect those measurements or retain the uncertainty. Parallel flow
   is valid but path lead time is unsupported. Neither warning is fixed by zero.
3. Render and compare the same step IDs, statistic and units in both states.
4. Change a selector to `missing`: validation identifies the profile and says
   `primary must reference a named result`. Repair it to `mean`. A missing unit
   must be supplied as `unit: min`; a misspelled edge target must name a declared
   step. The notebook demonstrates the error/repair loop without editing files.
5. Revise proposed assumptions, keep their basis and source honest, then rerun.

End-to-end time remains unavailable. Both checks execute; they are not alternative
routes to add together. Clarification can repeat work. Branch frequencies, repeat
counts and request-level elapsed observations are absent. Declared graph totals
in inspection JSON are inventories, not process elapsed time. No mean, percentile
or savings percentage is inferred by adding step summaries. Measure comparable
request-level start/end observations before claiming an overall improvement.
