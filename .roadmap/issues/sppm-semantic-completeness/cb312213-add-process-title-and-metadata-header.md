---
id: cb312213
title: Add process title and metadata header
headline: Render a process-level title and metadata band that lets an SPPM map stand
  alone.
priority: critical
status: in-progress
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:31.990288+00:00'
updated: '2026-05-06T18:17:19.933845+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- a3e631a8
blocks: []
actual_start_date: '2026-05-06T18:17:19.845643+00:00'
actual_end_date: null
progress_percentage: 0.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

# Add process title and metadata header

Render a process-level title band and metadata header at the top of SPPM outputs so the map can stand alone in book and report contexts.

## Why

The roadmap for SPPM semantic completeness calls out the need for a map that can be read in isolation. A title and metadata header are part of the notation and publishing surface, not just decorative layout.

## Acceptance Criteria

- SPPM output can render a title and core process metadata at the top of the map.
- The header content is driven from model or render inputs rather than manual SVG editing.
- The header works with existing queue, rework, and annotation rendering.
- Output remains readable in both reference and print-oriented themes.

## Notes

Use shared document-band primitives only where that reuse is clearly warranted; the semantic content still belongs to SPPM.
