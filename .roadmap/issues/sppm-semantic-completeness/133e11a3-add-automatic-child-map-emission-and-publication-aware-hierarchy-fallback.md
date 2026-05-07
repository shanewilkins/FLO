---
id: 133e11a3
title: Add automatic child-map emission and publication-aware hierarchy fallback
headline: Build on the new SPPM projection seam to automatically emit child maps when
  publication profile or r
priority: high
status: todo
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-07T18:28:37.524279+00:00'
updated: '2026-05-07T18:29:05.913926+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 048bbcb1
- e98c98fb
- 6d3f7a91
- 5f2e3b71
- 13abd93e
blocks: []
actual_start_date: null
actual_end_date: null
progress_percentage: null
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

Build on the new SPPM projection seam to automatically emit child maps when publication profile or readability policy requires them, and make inline-to-child fallback a publication-aware diagnostic behavior rather than a caller-selected single-map mode.\n\nScope:\n- automatically plan child-map emission from the same authored FLO source\n- use multi-page publication series and page metadata when parent and child outputs are materialized\n- promote fallback decisions into explicit readability diagnostics/policy behavior\n- keep the implementation downstream of shared pagination/publication work\n\nNon-goals:\n- redoing the projection seam added under 5f2e3b71\n- unrelated CLI cleanup or renderer-platform polish\n\nAcceptance criteria:\n- child maps are emitted automatically when profile or readability policy requires them\n- fallback from inline expansion to collapsed parent plus child map is policy-driven and explicit\n- publication metadata carries enough context to connect parent and child outputs deterministically
