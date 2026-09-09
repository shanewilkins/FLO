# Diagram Accessibility and Practitioner Review Protocol

## Status

Automated prerequisites are implemented and gate 0.4. On September 9, 2026,
the maintainer approved the external accessibility-specialist and practitioner
sessions as follow-up evidence for the 1.0 stable-promotion gate. Those sessions
remain pending and must not be represented as completed evidence until signed
records are added below.

## Automated prerequisite

`uv run python scripts/check_svg_accessibility.py` verifies that every committed SPPM golden SVG has a deterministic accessible name and description, `role="img"`, valid labelled-by references, and unique IDs. Theme tests independently enforce the current normal-text contrast floor. CI also opens and rasterizes the white-belt SVG in headless Chrome.

These checks establish machine-readable structure and browser consumption. They do not establish a useful screen-reader reading order or user comprehension.

## Accessibility-specialist session

Use the committed `washnfold_white_belt`, `simple_decision_book`, and `rework_loop_lr` SVGs. Record reviewer name, date, assistive technology and version, browser and version, display/zoom settings, and findings for:

1. accessible name and description;
2. screen-reader announcement and reading order;
3. 200% and 400% zoom behavior;
4. normal and high-contrast presentation;
5. color-independent identification of value class, queues, branches, and rework;
6. print/PDF legibility at the intended book size.

Each finding must be `pass`, `fail`, or `not applicable`, with artifact ID and a reproducible observation. Any failure that prevents identifying process sequence, node purpose, branch meaning, or timing blocks 1.0 stable promotion until resolved.

## Practitioner sessions

Recruit at least three process-improvement practitioners who are not FLO contributors. Give each participant the three artifacts without oral explanation and ask them to:

1. identify the process start and completion;
2. state the decision outcomes in the decision map;
3. identify the rework path and its reintegration point;
4. distinguish active cycle time, waiting time, and changeover time;
5. identify the longest declared queue in Wash n' Fold;
6. explain which role or lane owns each selected step.

Record accuracy, time, uncertainty, and any facilitator help. Acceptance requires all three participants to answer tasks 1–5 correctly without help; lane ownership is evaluated only on a lane-bearing artifact. Ambiguous labels, geometry, or visual conventions become tracked renderer defects rather than facilitator explanations.

## Evidence record

Add dated, anonymized records under `docs/usability/results/` and link them here. A record must identify the exact commit and golden artifact hashes. No external session evidence is checked in as of 2026-08-29.
