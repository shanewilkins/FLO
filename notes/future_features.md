# FLO Future Features

**Purpose:** Track planned enhancements and improvements to FLO that are not yet implemented.

---

## SPPM Rendering

### User-Definable Color Themes
**Status:** Planned  
**Effort:** 2.5–4 hours  
**Description:**

Currently, SPPM color themes are hardcoded in Python (`_sppm_themes.py`). Users can select from three predefined themes (`default`, `print`, `monochrome`) via `--sppm-theme`, but cannot define custom themes without modifying code.

**Proposed Solution:**

Implement config-file-based theme loading:
1. Allow users to define themes in YAML/JSON config file (e.g., `~/.flo/themes.yaml` or `$FLO_THEMES_DIR/themes.yaml`)
2. Load custom themes at runtime and merge with hardcoded themes
3. CLI: `flo render process.flo --diagram sppm --sppm-theme custom:brand-blue`
4. Theme file format:
   ```yaml
   brand-blue:
     va:
       fill: "#1976D2"
       border: "#0D47A1"
     rnva:
       fill: "#E3F2FD"
       border: "#1565C0"
     # ... etc
   ```

**Implementation Steps:**
- Define YAML/JSON schema for theme definitions
- Write theme loader (check hardcoded first, then config file)
- Update CLI to accept dynamic theme names
- Add validation and error handling
- Update spec Section 3.6.1b with documentation
- Add tests for theme loading and fallback behavior

**Rationale:** Enables book authors, organizations, and practitioners to maintain brand-consistent diagrams without forking FLO.

**Blocked By:** None  
**Blocks:** None (enhancement only)

---

### Queue/Bottleneck Circle Visualization
**Status:** ✅ **Implemented** (May 4, 2026)  
**Effort:** ~2 hours  
**Description:**

Queue circles are user-specified visual indicators that appear before steps with waiting or queueing conditions.

**Implementation Complete:**
- ✅ Queue nodes generated when `metadata.queue_circle: true` is set
- ✅ Orange circles (#FF9800 fill, #E65100 border, 0.6" diameter)
- ✅ Edges rerouted: incoming → queue circle → original node
- ✅ Works with all render options and themes
- ✅ User controls which nodes get queue circles (explicit opt-in)

**Usage:**
```yaml
metadata:
  queue_circle: true  # Add to any node to render a queue circle before it
```

**Proposed Solution:**

1. Add FLO metadata field: `is_bottleneck: true` or auto-detect from WT ≥ 10 min
2. Render queue circle node upstream of bottleneck step
3. Circle diameter scales to queue severity (0.5"–0.7")
4. Optional label: `WT: 35 min` or queue count
5. Color: #FF9800 (Alert Orange) per spec

**Implementation Steps:**
- Modify FLO data model (optional `is_bottleneck` flag or auto-detect rule)
- Add queue node generation in `_graphviz_dot_sppm.py`
- Add edge from queue to next step
- Configure sizing/scaling logic
- Update spec with implementation notes
- Test on Wash n' Fold example (should show circles before "Fold & Package" and possibly others)

**Rationale:** Core pedagogical feature—makes waste visually obvious to students at a glance.

**Blocked By:** None  
**Blocks:** None (enhancement only)

---

### Subprocess Notation and Detail Map References
**Status:** Planned  
**Effort:** 3–4 hours  
**Description:**

Per SPPM spec Section 2.3, subprocesses should be marked with double-line borders or ⊡ notation and reference detail maps. Currently not supported.

**Proposed Solution:**

1. Extend FLO data model: add `subprocess: true` or `detail_map_ref: "Detail Map 3.1"` to step metadata
2. Render subprocess steps with double-line border in SPPM
3. Add label suffix: `"Wash Cycle (See Detail Map 3.1)"`
4. Generate linked reference (SVG `<a>` tag or footnote)
5. Support nested detail maps (detail of a detail)

**Implementation Steps:**
- Extend FLO metadata schema for subprocess markers
- Modify `_graphviz_dot_sppm.py` to render double borders
- Add reference labeling logic
- Add SVG postprocessing to inject hyperlinks
- Document detail map file naming convention
- Add validation (circular references, missing detail maps)

**Rationale:** Enables Yellow Belt+ analysis (root-cause analysis, subprocess zoom).

**Blocked By:** None  
**Blocks:** None (enhancement only)

---

### Rework Rate and Frequency Annotations
**Status:** Planned  
**Effort:** 1.5–2 hours  
**Description:**

Per SPPM spec Section 2.7, rework loops should be labeled with rates/frequencies (e.g., "8% fail", "5% rework"). Currently, only outcome labels ("yes", "no") appear on rework edges.

**Proposed Solution:**

1. Extend FLO data model: add `rework_rate` field to rework edges
   ```yaml
   transitions:
     - source: qa
       target: rework_quality
       edge_type: rework
       rework:
         rate: 0.08
         reason: "Quality fail"
   ```
2. Render rate label on dashed arrows: `"fail (8%)"`
3. Support multiple failure modes from one step with separate arrows

**Implementation Steps:**
- Extend transition/edge metadata with `rework` object (rate, reason)
- Update `_sppm_edge_render.py` to include rate in label
- Add validation (rate between 0–1, or percentage string)
- Update spec with example
- Test on rework_loop.flo and sppm_feature_showcase.flo

**Rationale:** Quantifies waste impact; essential for root-cause prioritization.

**Blocked By:** None  
**Blocks:** None (enhancement only)

---

## Infrastructure & Tooling

### Multi-Unit Dimension System for Layout Constraints
**Status:** Planned  
**Effort:** 1.5–2 hours  
**Description:**

Currently, layout constraints are pixels-only (`--layout-max-width-px` accepts integers). To support user-friendly spec compliance and cross-format publishing, support multiple units (pixels, inches, centimeters).

**Proposed Solution:**

1. Create `Dimension` type that parses strings: `"7in"`, `"1200px"`, `"18cm"`
2. Normalize to pixels internally (assuming 96 DPI for web/screen)
3. CLI accepts unit suffixes: `--layout-max-width "7in"` or `--layout-max-height "10cm"`
4. Reusable for sizing verification and constraint validation

**Implementation Steps:**
- Create `Dimension` dataclass with parser (regex for "value+unit")
- Add `to_pixels(dpi=96)` converter method
- Update `RenderOptions` to replace `layout_max_width_px` and add `layout_max_height` (with units)
- Update CLI options to accept dimension strings
- Add validation (positive values, recognized units)
- Add unit tests

**Rationale:** 
- Spec values are naturally in inches (1.5"W, 0.6"H)
- Users think in their native units (inches for US, cm for EU/SI)
- Internal pixels still work for GraphViz

**Blocked By:** None  
**Blocks:** Sizing verification (should be revisited once this is implemented)

---

### SPPM Sizing Verification Script
**Status:** Implemented (basic)  
**Effort:** 1–1.5 hours (completed)  
**Description:**

Audit tool to verify that rendered SPPM SVG output matches spec dimensions.

**Current Implementation:**

Created `scripts/verify_sppm_sizing.py` that:
- Parses SVG output and extracts element dimensions
- Compares against spec values (1.5"W, 0.6"H for boxes; 0.5"–0.7" for circles @ 96 DPI)
- Reports mismatches with tolerance (~5px for boxes, ~2px for circles)
- Ignores canvas/structural elements
- Distinguishes queue circles (✓ passing) from table cell polygons (requires manual review)

**Findings (Wash n' Fold example):**
- ✓ Queue circles: 57.8px, 56.9px diameter (within spec 48–67px)
- ⚠️ Process/data boxes: Rendered as complex Graphviz HTML-like table structures (polygons)
  - Cannot reliably extract from SVG alone due to Graphviz's dynamic layout
  - DOT source specifies WIDTH hints (e.g., `WIDTH="92"` points), not fixed pixel constraints

**Limitation & Next Steps:**

SVG-level sizing verification is approximate because:
1. Graphviz DOT uses WIDTH/HEIGHT as layout hints, not hard constraints
2. Actual rendered size depends on content (text wrapping), font metrics, and Graphviz's layout engine
3. HTML-like table labels become complex polygon structures in SVG

**TODO (Post-Dimension System):**
1. Implement DOT-level parser to extract intended WIDTH/HEIGHT from source
2. Validate DOT specs against intended dimensions
3. Once multi-unit dimension system (above) is implemented:
   - Read spec constraints from `RenderOptions` 
   - Use `Dimension.to_pixels()` for conversions
   - Integrate into CI/validation pipeline

**Rationale:** Ensures rendered diagrams comply with spec; catches layout/sizing regressions.

**Blocked By:** None (can start now with hardcoded spec values)  
**Blocks:** None

---

### Render Specifications for Other Diagram Types
**Status:** Planned  
**Effort:** Varies by diagram type (20–40 hrs total for swimlane, spaghetti, flowchart)  
**Description:**

SPPM specification (docs/sppm_specification.md) is comprehensive and includes color palettes, sizing guidelines, and visual design standards. Similar detailed specs should exist for other render types (swimlane, spaghetti, flowchart).

**Proposed Solution:**

1. Create spec documents for each render:
   - `docs/swimlane_specification.md`
   - `docs/spaghetti_specification.md`
   - `docs/flowchart_specification.md`
2. Use SPPM spec as template (philosophy, symbols, map-level conventions, visual design, edge cases, tools, checklist)
3. Adapt symbols and guidelines to each diagram type's purpose

**Implementation Steps:**
- Conduct similar audit of swimlane/spaghetti/flowchart render code
- Document actual implementation colors, sizes, conventions
- Identify gaps vs. pedagog intent
- Write specs following SPPM pattern
- Update repo docs to link all render specs

**Rationale:** Consistency across all renders; easier for contributors and users to understand standards.

**Blocked By:** SPPM spec completion ✓ (done)  
**Blocks:** Potentially other render improvements

---

## Documentation

### Expand User Manual with Render Type Guide
**Status:** Planned  
**Effort:** 4–6 hours  
**Description:**

User Manual (docs/User_Manual.md) should include a "Choosing a Render Type" guide explaining when to use SPPM vs. swimlane vs. spaghetti vs. flowchart.

**Proposed Solution:**

Add section with:
- When to use each render type (pedagogy, use case)
- Examples of each
- Pros/cons tradeoffs
- CLI examples
- Links to render specifications

**Rationale:** Helps practitioners and authors pick the right diagram for their analysis goal.

**Blocked By:** All render specs (in progress)  
**Blocks:** None

---

## Notes

- All items above are enhancements; no blocking issues or critical bugs
- Custom themes (highest priority for user flexibility)
- Queue circles and rework rates are core spec compliance issues
- Subprocess notation is Yellow Belt+ and can wait
- Render specs for other types enable future scaling
