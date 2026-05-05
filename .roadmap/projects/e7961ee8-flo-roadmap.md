---
name: FLO Roadmap
description: Project roadmap for FLO renderer and language evolution
owner: shanewilkins
priority: high
status: active
created: 2026-05-05T17:09:49.038989+00:00
updated: 2026-05-05T17:09:49.038989+00:00
github_repo: shanewilkins/FLO
timeline:
  start_date: 2026-05-05T17:09:49.038989+00:00
  target_end_date: null
tags: []
---

# FLO Roadmap

## Overview

Project roadmap for FLO renderer and language evolution

## Project Goals

- [ ] Complete the remaining v0.1 reference implementation work.
- [ ] Reach SPPM semantic completeness for book-grade maps.
- [ ] Build shared renderer-platform primitives reusable beyond SPPM.
- [ ] Deliver static analytics on canonical IR artifacts.
- [ ] Align declarative models with telemetry and trace analysis.

## Milestones

### v0.1 Core Completion
- Finish schema-aligned IR JSON export.
- Complete advanced compiler edge wiring.
- Deliver the remaining CLI polish and reference-implementation cleanup.

### SPPM Semantic Completeness
- Add subprocess notation, header/footer bands, and continuation markers.
- Complete the SPPM publishing surface without relying on manual post-editing.

### Renderer Platform Completeness
- Add shared dimension, page, overflow, and continuation primitives.
- Keep document-layout concerns reusable across future renderers.

### Spaghetti and Swimlane Renderers
- Finish swimlane renderer output after the shared renderer platform is in place.
- Extend spaghetti rendering beyond material-only routes with richer movement and spatial semantics.

### v0.2 Static Analytics
- Add handoff, rework, and path-length analysis on canonical IR.
- Produce analysis-oriented summaries suitable for Lean modeling.

### v0.3 Telemetry Alignment
- Define the minimal event schema and alignment workflow.
- Bridge observed traces to model-level frequency and rework metrics.

## Resources

- .roadmap/milestones/
- .roadmap/issues/
- docs/design/
- docs/

## Notes

This roadmap combines the versioned delivery plan from v0.1 to v0.3 with two
cross-cutting renderer milestones, plus a staged spaghetti enhancement track.
The intent is to keep renderer infrastructure reusable while still tracking
diagram-specific semantic work explicitly inside `.roadmap`.
