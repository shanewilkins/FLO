---
id: b6f283a1
title: Migrate maintained notebooks to marimo
headline: Make marimo the official notebook format while retaining Jupyter support.
priority: low
status: todo
archived: false
issue_type: other
milestone: null
labels: [tooling, examples, documentation]
remote_ids: {}
created: '2026-11-15T00:00:00-06:00'
updated: '2026-11-15T00:00:00-06:00'
assignee: null
estimated_hours: null
due_date: null
depends_on: []
blocks: []
github_issue: null
---

# Migrate maintained notebooks to marimo

The project is moving its official notebook experience to marimo while
continuing to support Jupyter users through FLO's public Python API and
embeddable outputs. Riverside currently ships the repository's only tracked
`.ipynb`, and its documentation and integration test still assume Jupyter.

## Acceptance Criteria

- Replace the maintained Riverside `.ipynb` lesson with a marimo `.py` notebook,
  preserving the describe, validate, render, and revise journey, including the
  intentional selector error and repair exercise.
- Update the Riverside README, example index, Quickstart, and relevant design
  guidance to identify marimo as the official maintained notebook experience.
- Update `tests/integration/test_riverside_journey.py` to verify the marimo
  lesson's execution and behavior, and include maintained notebook Python files
  in appropriate lint and type-check coverage.
- Document how Jupyter users can continue to validate models and display FLO
  outputs without maintaining duplicate teaching notebooks.
- Keep notebook tooling optional and preserve the standalone Riverside build
  script's ability to run without notebook packages.

## Notes

Deferred follow-up; no release milestone assigned. This issue records the
migration decision without implementing the conversion yet.
