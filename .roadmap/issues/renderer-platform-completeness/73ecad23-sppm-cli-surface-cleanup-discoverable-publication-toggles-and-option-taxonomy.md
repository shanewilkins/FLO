---
id: 73ecad23
title: 'SPPM CLI surface cleanup: discoverable publication toggles and option taxonomy'
headline: Refine SPPM CLI ergonomics so publication options are intuitive and discoverable,
  including explicit
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- cli,sppm,ux
remote_ids: {}
created: '2026-05-11T17:23:08.972080+00:00'
updated: '2026-05-11T17:27:08.461708+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 63da7b5d
- '10085780'
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

Refine SPPM CLI ergonomics so publication options are intuitive and discoverable, including explicit toggles like --no-header/--no-footer.\n\nScope\n- Group SPPM publication options coherently in CLI help and docs.\n- Introduce or normalize explicit negative toggles for optional display elements.\n- Ensure option naming is consistent with existing render option schema.\n\nAcceptance Criteria\n- CLI help cleanly communicates publication controls and defaults.\n- New/renamed options are integration-tested and documented.\n- Behavior remains backward compatible or includes migration aliases.\n- User-facing diagnostics are clear for invalid combinations.
