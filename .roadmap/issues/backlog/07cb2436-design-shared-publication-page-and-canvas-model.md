---
id: 07cb2436
title: Design shared publication, page, and canvas model
headline: Introduce a reusable publication model that separates document series and
  page bounds from renderer-specific layout.
priority: critical
status: closed
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:35.659990+00:00'
updated: '2026-05-06T23:02:39.843939+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-06T22:49:14.708511+00:00'
actual_end_date: null
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

## Design shared publication, page, and canvas model

Introduce a reusable publication, page, and canvas abstraction for renderers so layout decisions can target print, slide, and web formats consistently.

## Why

Without a shared publication model, document layout concerns will keep leaking into individual renderers. A common publication and canvas abstraction is the foundation for headers, overflow handling, continuation markers, child-map artifacts, and output-profile-aware rendering.

## Acceptance Criteria

- A shared publication, page, or canvas model exists independently of any single renderer.
- The model can represent a publication set with one or more map series or child artifacts.
- The model can express usable bounds, margins, and content regions.
- Renderers can target the shared model without losing their own semantic styling.
- The design is documented well enough to support later pagination and document-band work.

## Notes

Favor a small, explicit model over a premature full document engine.
