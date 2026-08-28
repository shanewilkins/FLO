# Render Themes

Status: implemented for FLO 0.3.

## Purpose

A render theme is a named, reusable presentation policy for maintained FLO
diagrams. Themes let a team establish book, screen, print, or organizational
presentation choices in one place without embedding arbitrary style overrides
in individual process steps.

The current runtime resolves maintained SVG presentation through this shared
contract. Existing `sppm_theme` and `sppm_themes` inputs remain supported as a
compatibility adapter into the central registry.

## User-facing home

Repository or project themes live in one top-level `themes` section of
`diagrams.toml`. Built-in themes use the same typed shape. A theme may extend
exactly one named parent and provide only the values it changes.

```toml
[themes.white_belt]
extends = "default"

[themes.white_belt.canvas]
background = "#fffdf8"

[themes.white_belt.typography]
font_family = ["Source Sans 3", "Arial", "sans-serif"]
scale = 1.05

[themes.white_belt.roles.queue]
fill = "#ffb74d"
border = "#e65100"
title_text = "#0f172a"
detail_text = "#475569"
```

Theme selection is available through profiles, process render defaults, named
views, and an explicit CLI override. The CLI remains the highest-precedence
session override.

Repository defaults use `[render]`, while reusable themes use `[themes]`:

```toml
[render]
theme = "white_belt"

[render.style.canvas]
background = "#fffdf8"

[render.style.typography]
font_family = ["Source Sans 3", "Arial", "sans-serif"]
scale = 1.05
```

The equivalent explicit CLI controls are `--theme`, `--background-color`,
`--font-family`, and `--typography-scale`. Font families on the CLI are a
comma-separated ordered list. The supported scale range is `0.75` through
`1.5`.

## Shared typed contract

The central theme contract contains:

- `canvas.background`
- `typography.font_family`: a non-empty ordered fallback list
- `typography.scale`: a bounded positive multiplier
- shared publication and diagram roles for primary and secondary text,
  connectors, rules, and neutral surfaces
- process-semantic roles for `va`, `rnva`, `nva`, `unknown`, `decision`,
  `queue`, and `start_end`, each with typed fill, border, title-text, and
  detail-text colors
- registered renderer extensions for genuinely renderer-specific roles

Registered renderer extensions include spaghetti route, boundary, and location
roles. Renderer extensions remain part of the central schema and registry. A
renderer may adapt resolved semantic roles to its shapes, but it may not create
an independent theme registry or require users to edit renderer source.

## Resolution and precedence

Theme resolution occurs in two stages.

1. Resolve the selected theme name using explicit CLI selection, named-view
   intent, process render defaults, `diagrams.toml` defaults, profile defaults,
   then the built-in default.
2. Resolve the selected theme and its single-parent inheritance, then apply
   explicit style-property overrides using CLI, named view, process defaults,
   `diagrams.toml`, profile, resolved theme, then renderer safety fallbacks.

Every merge is field-wise and deterministic. Theme inheritance cycles, unknown
parents, invalid colors, empty font lists, out-of-range scales, and unregistered
roles produce usage-stage diagnostics that identify the configuration path. New shared-theme configuration does not
silently discard malformed values.

## Cross-diagram behavior

Maintained SVG diagrams consume the same resolved canvas and typography values.
Semantic roles apply where the diagram presents the corresponding concept. A
theme does not force every renderer to use every role, and it does not change
process semantics, layout topology, or analysis results.

The same resolved input, theme registry, theme selection, and explicit
overrides must produce byte-identical supported SVG output on the supported
platform.

## Accessibility and safety

Built-in themes must preserve readable contrast and must include print and
monochrome treatments. Theme validation reports contrast risks where FLO can
evaluate them. Shape, label, line style, and other non-color semantics remain
available so color is never the only carrier of process meaning.

## Non-goals for 0.3

- per-node arbitrary colors or fonts
- a graphical theme editor
- multiple-inheritance or conditional themes
- downloadable theme packages or remote registries
- exact physical geometry or multi-page composition
