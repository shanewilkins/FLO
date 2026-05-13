---
id: 5e6b7d3a
title: Split RenderOptions by concern; separate render-specific from renderer-specific config
headline: Refactor monolithic RenderOptions into focused domain objects; decouple SPPM-specific fields from shared core.
priority: critical
status: open
archived: false
issue_type: refactor
milestone: render-intent-schema-and-multi-view-support
labels: [refactor, critical-path]
remote_ids: {}
created: '2026-05-13T17:30:00+00:00'
updated: '2026-05-13T17:30:00+00:00'
assignee: null
estimated_hours: 8
due_date: null
depends_on: [a1d9f4c6]
blocks: [6a2c8f9b]
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

## Split RenderOptions by concern; separate render-specific from renderer-specific config

Refactor [src/flo/render/options.py](../../../src/flo/render/options.py) RenderOptions dataclass to separate diagram-selection, publication/layout intent, and renderer-specific (SPPM, spaghetti, etc.) configuration into distinct types.

## Why

Current RenderOptions combines unrelated concerns: diagram type selection, publication page/canvas bounds, layout hints, SPPM-specific knobs (wrap-layout, label-density, truncation-policy), and legacy header/footer aliases. This makes it hard to:
- Express clean intent per renderer
- Deprecate legacy aliases without breaking unrelated config
- Validate renderer-specific options against diagram type
- Avoid SPPM-coupling in shared publication logic

## Acceptance Criteria

- [ ] Analyze current RenderOptions fields and group by concern (diagram, layout, publication, sppm-specific)
- [ ] Create new types: `RenderConfig` (diagram type, output format), `PublicationLayout` (margins, headers/footers, bands), `RendererProfile` (renderer-specific, e.g., SPPMProfile, SpagettiProfile)
- [ ] Update [src/flo/render/options.py](../../../src/flo/render/options.py) to compose these types instead of flat dataclass
- [ ] Remove legacy aliases (sppm_no_header, sppm_no_footer, etc.) from core; migrate to SPPM-specific validator
- [ ] Update all renderers to consume specific profile type instead of flat RenderOptions
- [ ] Write golden-file tests asserting option parsing and composition for each renderer
- [ ] Verify full test suite passes with no breaking changes to public API

## Implementation Notes

- Keep RenderOptions as top-level public type (for backward compatibility during transition)
- RenderOptions can delegate to composition: `publication_layout: PublicationLayout`, `profile: Union[SPPMProfile, SpagettiProfile, ...]`
- Move SPPM defaults from [src/flo/render/options.py#L44](../../../src/flo/render/options.py#L44) (_SPPM_PROFILE_DEFAULTS) into SPPMProfile.defaults()
- Separate alias handling: if SPPM is selected, apply sppm-specific aliases; else no-op
- Consider using discriminated union (@dataclass with profile_type field) for type-safe renderer profile dispatch

## References

- Audit finding #5 (RenderOptions is Monolithic Mixed Concern)
- [src/flo/render/options.py](../../../src/flo/render/options.py) - current monolithic implementation
- [src/flo/render/options.py#L193-L198](../../../src/flo/render/options.py#L193-L198) - legacy header/footer alias parsing
- [src/flo/render/_sppm_publication.py](../../../src/flo/render/_sppm_publication.py) - SPPM renderer (will consume SPPMProfile)
