---
id: 6a2c8f9b
title: Build bundle orchestration layer for multi-view, multi-artifact rendering
headline: Create executor that chains view selections and emits ordered artifacts (SPPM, spaghetti, topdown in one invocation).
priority: critical
status: open
archived: false
issue_type: feature
milestone: render-intent-schema-and-multi-view-support
labels: [architecture, critical-path]
remote_ids: {}
created: '2026-05-13T17:30:00+00:00'
updated: '2026-05-13T17:30:00+00:00'
assignee: null
estimated_hours: 10
due_date: null
depends_on: [a1d9f4c6, 5e6b7d3a]
blocks: []
actual_start_date: null
actual_end_date: null
progress_percentage: 0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

## Build bundle orchestration layer for multi-view, multi-artifact rendering

Create new `BundleOrchestrator` executor that sequences multi-view rendering, invoking resolver + renderer for each view and emitting ordered artifacts in one execution.

## Why

Current renderer is single-diagram dispatcher ([src/flo/render/__init__.py](../../../src/flo/render/__init__.py)). Cannot express "render SPPM + spaghetti in one invocation" intent in source metadata or CLI. Bundle orchestration is the missing piece that enables:
- One .flo file → multiple diagram types for publication/documentation
- Deterministic artifact ordering for build pipelines
- Shared compilation (parse once, render multiple views)
- Clean separation of view selection from rendering

## Acceptance Criteria

- [ ] Create new module [src/flo/render/bundle.py](../../../src/flo/render/bundle.py) with `BundleOrchestrator` class
- [ ] Orchestrator takes: (compiled IR, list of view names, RenderOptions overrides) → list of (view_name, artifact_path) tuples
- [ ] For each view: resolve RenderIntent → select diagram renderer → invoke renderer → capture artifact
- [ ] Maintain deterministic view ordering (as specified in source intent or CLI)
- [ ] Write integration tests asserting multi-view bundles for reference models (chocolate_chip_cookies with SPPM + spaghetti + topdown, etc.)
- [ ] Update [src/flo/core/__init__.py](../../../src/flo/core/__init__.py) run() to optionally use orchestrator when multi-view rendering requested
- [ ] Verify all existing single-view tests still pass without orchestrator involvement

## Implementation Notes

- Orchestrator should be pure orchestrator, not decision-maker; RenderIntent resolver and dispatcher determine diagram type
- Consider lazy view evaluation if performance needed (render on-demand, not all-at-once)
- Artifact capture strategy: write to temp dir, then move to final destination; supports atomic multi-artifact updates
- Error handling: if one view fails, decide whether to: a) abort all, b) continue with error logging, c) partial artifact set. Recommend option (a) for now (transactions-like semantics).
- Document artifact ordering and naming convention for downstream tools

## References

- Audit finding #3 (No Multi-View Bundle Orchestration)
- [docs/design/render_intent_schema.md](../../../docs/design/render_intent_schema.md) - multi-view intent spec
- [src/flo/render/__init__.py](../../../src/flo/render/__init__.py) - current single-diagram dispatcher (_DOT_RENDERERS)
- [src/flo/core/__init__.py](../../../src/flo/core/__init__.py) - execution orchestrator (integration point)
- Example use case: [examples/reference/chocolate_chip_cookies.flo](../../../examples/reference/chocolate_chip_cookies.flo) (would render SPPM + spaghetti)
