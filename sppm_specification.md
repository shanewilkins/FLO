# SPPM Specification: Simplified Process and Performance Mapping

**Version:** 1.0  
**Date:** May 4, 2026  
**Purpose:** Authoritative reference for building and rendering SPPM diagrams across the LSS book  
**Audience:** Instructional designers, content authors, diagram creators

---

## 1. Philosophy and Design Constraints

SPPM is a pedagogical notation system designed to balance **simplicity with analytic expressiveness**. It is not a brand-new invention; rather, it synthesizes widely recognized symbols from value-stream mapping, flowcharting, and Lean process documentation practices.

**Core Design Principles:**
1. **No proprietary tool required** — any drawing software (Google Drawings, Lucidchart, Draw.io, even PowerPoint) can render SPPM
2. **Low cognitive load for White Belt students** — minimal notation choices during observation; students focus on data, not decoration
3. **Analytic transparency** — the diagram should make flow problems, waste, and bottlenecks visually obvious
4. **Progressive enrichment** — White Belt uses base elements; Yellow Belt adds detail (queue shapes, rework rates, subprocess zoom); Green Belt and beyond add capacity, distribution, and simulation hooks

---

## 2. Symbol Specification

### 2.1 Process Step (Rectangle)

**Shape:** Standard rectangle  
**Color coding by value type:**
- **Green** = Value-Added (VA): directly transforms product/service in a way the customer pays for
- **Gray** = Required Non-Value-Added (RNVA): necessary for compliance, regulation, or contractual reasons
- **Red** = Non-Value-Added (NVA): pure waste; eligible for elimination

**Data Box:**
- Small rectangle or text box placed directly below the process step rectangle
- Content format: `Role | CT (min) | WT (min)` or as separate rows if space is tight
- Example: `Staff | 30 | 18` means staff perform the step in 30 min average cycle time, with 18 min average wait before it starts

**Labeling:**
- Process step name goes inside the rectangle (2–4 words, verb-noun form: "Sort Laundry", "Verify ID", "Run Wash Cycle")
- Do not put numbers in the rectangle itself; all metrics go in the data box below

**Size convention:**
- Uniform width (e.g., 1.5 inches) for visual rhythm
- Height proportional to cycle time (optional for advanced diagrams, but not required at White Belt)

---

### 2.2 Queue / Waiting State (Triangle)

**Shape:** Upright triangle (fixed size)  
**Color:** Light Orange (Alert Orange #FF9800, border #E65100; distinct from value-type colors to signal "delay" or "idle state")

**Placement:** Before the step at which wait time is most pronounced  
**Example:** In Wash n' Fold, a queue triangle appears before "Fold & Pack" because the 35-minute wait is the biggest bottleneck.

**Labeling and sizing:**
- Keep queue triangles at a fixed size for readability and stable routing
- Place a short queue label inside the triangle (for example, queue name and step reference)
- Put queue metadata in a data box below the triangle (for example, `WT: 35 min`)

**Use in the map:**
- **When to include:** Any step where you want to highlight a waiting or queueing condition; typically steps with WT ≥ 10 min
- **Why:** Makes bottlenecks jump out visually; students instantly see where congestion lives
- **Frequency in Wash n' Fold example:** 2–3 queue triangles (before fold+pack, possibly after wash exit if dry queue is high)

**Implementation (FLO):**  
✅ **Implemented** — Queue nodes are first-class elements in FLO. Define a queue as a node with `kind: queue`, positioned in the flow immediately before the task it serves. Example:
```yaml
steps:
  - id: fold_package_queue
    kind: queue
    name: Fold & Package Queue
    metadata:
      wait_time:
        value: 35
        unit: min
  
  - id: fold_package
    kind: task
    name: Fold and package
    metadata:
      value_class: VA

transitions:
  - source: dry_clothes
    target: fold_package_queue
  
  - source: fold_package_queue
    target: fold_package
```

FLO will render the queue node according to the diagram type:
- **SPPM:** Orange upright triangle (#FF9800 fill, #E65100 border) with a compact in-shape label; wait-time metadata is rendered in a data box below
- **Flowchart:** Queue node may be rendered inline or skipped depending on visualization
- **Swimlane:** Queue indicator in the same lane as the target task
- **Other VSM variants:** Rendered per diagram conventions

Manually authored diagrams (Google Drawings, Draw.io) can include queue symbols using the same color scheme and placement rules.

---

### 2.3 Subprocess (Dotted Oval Container)

**Shape:** Dotted oval container  
**Color:** Neutral/light fill with dotted border, distinct from value-class task cards

**Placement:** On the main map where detail will be "exploded"

**Annotation:**
- Label subprocess name and step reference inside the dotted oval
- Include a detail-map reference in metadata below the subprocess symbol (for example, `Detail map: 3.1`)
- Optional: show internal structure as a brief note, e.g., `"Load → Run → Unload → QC"`

### 2.4 Continuation Anchor (Circle)

**Shape:** Circle
**Color:** White/light fill with dark border for primary flow; lighter border for secondary/rework flow

**Placement:** At continuation breakpoints for cross-page flow and long-distance jumps

**Labeling:**
- Use stable anchor IDs in `P{page}-{letter}` format (for example, `P2-B`)
- Anchor labels must be deterministic across re-renders for the same model and options
- Use paired outgoing/incoming anchors to show where flow exits and re-enters

**Separate detail map:**
- Created as a complete SPPM within a bounded region (e.g., in the appendix or as an inset)
- Detail map uses the same symbol set and follows the same rules
- Clearly labeled with parent process name and cross-reference to main map (e.g., "Detail of 'Wash' from Chapter 4 Figure 4.1")
- Includes its own data boxes with observed cycle times and wait times inside the subprocess

**Use cases:**
- A step is a composite of multiple substeps (e.g., "Wash" = load + run + unload)
- A problem is suspected to live inside a step (e.g., during root-cause analysis, you zoom into "Fold & Pack" to find where defects occur)
- A step has high variability or multiple decision points (e.g., "Quality Check" differs by product type)

---

### 2.4 Decision / Approval Diamond

**Shape:** Diamond (four-point rhombus)  
**Color (optional):** Light yellow color

**Labeling:** Decision question or approval gate inside the diamond  
**Examples:** "Pass QC?", "Premium or Standard?", "Approval Granted?"

**Arrows out:** 
- Solid arrows to next step in normal flow
- Optionally label arrows with decision outcomes: `"Yes"`, `"No"`, `"Standard"`, `"Premium"`

**Use in the map:**
- Marks points where the process branches (variants)
- Each output arrow should be clear about which condition it represents
- If a variant loops back (e.g., failed QC → rework → back to test), show this with a dashed arrow

---

### 2.5 Start / Stop Event (Rounded Rectangle)

**Shape:** Rectangle with rounded corners  
**Color:** Neutral (uncolored or light gray)

**Labeling:** 
- Start event: customer action or external trigger (e.g., "Customer Drops Off Laundry", "Order Received")
- Stop event: final delivery or handoff to customer (e.g., "Delivery to Customer", "Payment Complete")

**Placement:** At the beginning and end of the process scope

**Scope rule:** The start and stop events define the process boundary from the customer's perspective. Everything inside the boundary is the process being analyzed.

---

### 2.6 Forward Progress (Solid Arrow)

**Shape:** Solid line with arrowhead  
**Direction:** Top-to-bottom or left-to-right (consistent within diagram)

**Labeling:** Usually unlabeled unless flow path is ambiguous or conditional  
**Examples of conditional labels:** `"If urgent"`, `"Standard path"` (but prefer decision diamonds for clarity)

---

### 2.7 Rework Loop (Dashed Arrow)

**Shape:** Dashed line with arrowhead, looping backward from a later step to an earlier one  
**Color (optional):** Red or orange to signal rework/waste

**Labeling (required):**
- At the origin of the rework, include rework rate or frequency
- Format: `[Rework Rate]` or `[Frequency]`
- Examples: `"8% fail"`, `"5% rework"`, `"avg 0.15 loops/cycle"`
- Or brief cause: `"Wrong sort [5%]"`, `"Damaged in transit [2%]"`

**Data Box (FLO support):**
- FLO supports an optional rework-loop data box on the dashed rework edge itself
- Record this data on the edge under `metadata`, not on the rework task node
- Supported keys are flexible, but recommended fields are `rate`, `reason`, `count`, `frequency`, and `note`
- Example:

```yaml
- source: qa
  target: rework_quality
  outcome: fail
  edge_type: rework
  rework: true
  metadata:
    rate: 0.08
    reason: Missing approvals
    note: Most failures are incomplete signatures.
```

- In FLO renders, that metadata is shown in a small boxed label attached to the rework loop while the branch outcome label (for example `fail`) remains on the loop

**Source of data:** Rework rate comes from observation notes; during White Belt observation, record "how many times did this step require a repeat?" across your 3–5 sample runs.

**Interpretation:**  
A 5% rework rate means 5% of items that pass through that step will circle back. This is a cost multiplier on cycle time and a quality indicator.

---

## 3. Map-Level Conventions

### 3.1 Flow Direction
- **Primary:** Top-to-bottom or left-to-right
- **Consistency:** All diagrams in the same document must use the same primary direction
- **Recommendation for the book:** Left-to-right (horizontal flow) for horizontal space efficiency; top-to-bottom acceptable for tall, narrow processes

### 3.2 Swimlanes (Optional, Yellow Belt+)
- Not required at White Belt
- At Yellow Belt, consider adding horizontal swimlanes by role (e.g., "Customer", "Staff", "Management") to show handoffs
- Swimlanes make organizational silos visible but add complexity; use only if handoff analysis is the focus

### 3.3 Data Boxes and Metrics
- **Every process step must have a data box** with role, cycle time, and wait time
- Format: `[Role] | [CT] | [WT]` or vertically arranged
- **Units:** Always state units (minutes, hours); be consistent across diagram
- **Rounding:** Cycle times and wait times should be rounded to whole numbers unless high precision is justified
- **Data source:** All metrics come from the completed observation sheet; no estimates

### 3.4 Color Consistency
- **Process step colors must follow the VA/RNVA/NVA rule** (Green / Gray / Red)
  - This is non-negotiable; it forces students to classify value and makes waste patterns obvious
- **Queue colors:** Orange or yellow (chosen consistently across all diagrams in the book)
- **Decision diamond colors (optional):** Light blue or light gray; if omitted, use black outline
- **Background:** White or light gray; avoid high contrast that fatigues the eye

### 3.5 Labeling Standards
- **Process step names:** 2–4 words, present tense, verb-noun (e.g., "Fold Laundry", "Verify Details")
- **Avoid:** Single words, gerunds, ambiguous names (e.g., "Processing" ❌, "Data Entry" ✓)
- **Font:** Sans-serif (Arial, Helvetica, Roboto) for web/PDF; size 10–12 pt minimum
- **Legends:** If any non-standard notation is used, include a small legend in the diagram's caption or appendix

---

## 3.6 Visual Design Guidelines

### 3.6.1 Color Palette (Default Theme)

**Default Color Theme**

FLO uses a default color palette designed for visual clarity, print compatibility, and pedagogical impact. Copy hex values directly into tool swatches.

| Element | Fill Color (Hex) | Border Color (Hex) | RGB (Fill) | Usage |
|---------|---|---|---|---|
| Value-Added (VA) | #81C784 | #2E7D32 | (129, 199, 132) | Process steps that add customer value |
| Required Non-Value-Added (RNVA) | #FFF176 | #F9A825 | (255, 241, 118) | Necessary but non-value-adding steps |
| Non-Value-Added (NVA) | #EF9A9A | #C62828 | (239, 154, 154) | Pure waste; eligible for elimination |
| Queue / Bottleneck | #FF9800 | #E65100 | (255, 152, 0) | Waiting states, congestion (visual indicators) |
| Decision Diamond | #FFFFFF | #333333 | (255, 255, 255) | Decision gates, approval points |
| Start / Stop Event | #FFFFFF | #333333 | (255, 255, 255) | Process boundaries (start/end) |
| Unknown/Unclassified | #FFFFFF | #9E9E9E | (255, 255, 255) | Fallback for missing value_class |
| Rework Arrow (dashed) | — | #C62828 | — | Dashed feedback loops (inherits NVA border) |
| Text (Labels) | — | #000000 | — | Process names, metrics (automatic) |
| Background | #FFFFFF | — | (255, 255, 255) | Diagram canvas |

**Rationale:**
- Green (VA) and red (NVA) are universally recognized waste signals
- Yellow (RNVA) provides visual separation without heavy contrast
- Light colors ensure readability on white backgrounds and print quality
- High border contrast aids visual hierarchy and accessibility

### 3.6.1b Theme Customization

While FLO ships with a default color theme, SPPM diagrams are fully themable for different contexts:

**Predefined Themes:**
- **`default`** — Standard theme (shown above); recommended for most use cases
- **`print`** — High-contrast variant for black-and-white printing; uses blues, pastels, and stark outlines
- **`monochrome`** — Grayscale only; useful when color cannot be relied upon
- **Custom themes** — Authors can define custom color palettes by specifying fill and border hex values for each element

**Applying a Theme:**
- If using FLO directly: Pass `--sppm-theme print` (or custom theme name) to render command
- If using Draw.io, Google Drawings, or Visio manually: Override fill/border colors in tool settings; the default palette above is recommended for consistency
- If defining a custom theme: Ensure at least VA, RNVA, NVA, and start/end colors are defined; other elements inherit sensible defaults

**Design Constraint for Custom Themes:**
When designing a custom theme:
1. Maintain sufficient contrast (WCAG AA minimum) for accessibility
2. Ensure VA is visually positive (bright/bold green preferred)
3. Ensure NVA is visually negative (red tones preferred)
4. RNVA should be neutral or slightly cautionary (yellow/gray/blue acceptable)
5. Test output in target format (web, PDF, print) before finalizing

### 3.6.2 Sizing Matrix

**Process Step Rectangle (Standard):**
- Width: 1.5 inches (38 mm)
- Height: 0.6 inches (15 mm)
- Corner radius: 0 (sharp corners; if tool default rounds, set to 0 for compatibility)
- Font size (label): 11 pt, bold, sans-serif
- Text alignment: Center, middle

**Data Box (below process step):**
- Width: 1.5 inches (same as process rectangle above)
- Height: 0.4 inches (10 mm)
- Border: Light gray (1 pt solid)
- Font size: 9 pt, sans-serif, monospace or table format preferred
- Spacing (gap between process box and data box): 0.1 inches (3 mm)
- Format: `Role | CT (min) | WT (min)` on single line, or three rows if horizontal space tight

**Queue / Circle:**
- Diameter: 0.5 inches (13 mm) standard; scale up to 0.7 inches (18 mm) only if queue is highest-severity bottleneck
- Scaling rule: If queue is in top 1 bottleneck, diameter = 0.7"; top 2–3, diameter = 0.6"; others = 0.5"
- Font size (label): 9 pt, optional; if included, place inside or immediately adjacent

**Decision Diamond:**
- Width: 0.9 inches (23 mm)
- Height: 0.9 inches (23 mm) (square aspect ratio)
- Font size: 10 pt, sans-serif
- Text alignment: Center, middle

**Start / Stop Rounded Rectangle:**
- Width: 1.4 inches (35 mm)
- Height: 0.5 inches (13 mm)
- Corner radius: 0.25 inches (6 mm)
- Font size: 10 pt, sans-serif

**Diagram-Level Constraints:**
- **User-specifiable max width:** Authors must define a maximum diagram width based on their publication/page format (e.g., 7 inches for a page with 0.5\" margins on 8.5×11\" paper)
- **User-specifiable max height:** Authors must define a maximum diagram height to prevent awkward page breaks (e.g., 10 inches for a single-page layout)
- **Resize strategy:** If a diagram exceeds max dimensions, authors should:
  - Create a detail map or split into multiple diagrams rather than reducing font size
  - Use swimlanes and rearrangement to optimize layout before resizing text
- **Minimum spacing between elements:** 0.2 inches (5 mm) horizontally; 0.3 inches (8 mm) vertically (to accommodate decision arrows without tangles)
- **Tool enforcement:** In tools with canvas or page size settings, configure page dimensions to equal (max width, max height) to provide visual feedback as you author

### 3.6.3 Line and Arrow Specifications

**Solid Arrow (Forward Progress):**
- Line weight: 1.5 pt
- Color: Dark Charcoal (#212121)
- Arrowhead style: Standard triangular, size medium (proportional to line weight)
- Arrowhead fill: Same color as line

**Dashed Arrow (Rework Loop):**
- Line weight: 1.5 pt (same as solid for visual cohesion)
- Color: Rework Red (#D32F2F) or Waste Red (#EF5350)
- Dash pattern: 3 pt dash, 2 pt gap (adjust if tool default is different, but maintain ~1.5:1 dash-to-gap ratio)
- Arrowhead style: Standard triangular, size medium
- Arrowhead fill: Same color as line
- Label placement: At line origin (source step), positioned above or to the left of the arrow

**Crossing Lines:**
- Where solid and dashed arrows must cross: use "bridge" notation (small semicircle arc over one line to show it passes in front) only if diagram becomes illegible; prefer re-routing flows to avoid complex crossings

---

## 4. Edge Cases and Ambiguities

### 4.1 Multiple Failure Modes from a Single Step

**Scenario:** A process step has more than one type of failure, each with a different rework path.

**Example:** "Sort & Tag" has two failure modes:
- 5% wrong-sort defects → rework to "Re-Sort"
- 3% damaged tags → rework to "Replace Tags"

**Solution:**
- Option A (Preferred): Draw one dashed arrow per failure mode, each labeled with its rate, each looping back to a different earlier step
  - Labeled: `[Wrong sort, 5%]` and `[Damaged, 3%]` on separate arrows
  - Visually distinct: slightly offset or curved paths to avoid visual tangles
- Option B: If paths merge, draw a single combined rework arrow labeled `[Rework total 8%: 5% sort + 3% damage]` with a note in the diagram caption explaining breakdown
- **Avoid:** Single arrow with ambiguous label like `[8% fail]` if causes are different or rework destinations differ

### 4.2 Shared Roles Across Multiple Steps

**Scenario:** Two adjacent steps are both performed by the same role (e.g., both by "Staff").

**Data Box Format:**
- Still include role name in each step's data box: `Staff | 10 | 2` and `Staff | 15 | 3`
- Swimlanes (if used) will show this visually; swimlane labels alone are not sufficient for role clarity in the data box
- If the process is role-focused (e.g., an analysis of handoffs), consider adding a swimlane and leaving role out of the data box for conciseness

### 4.3 Subprocess Depth and Decision Rule

**Scenario:** A candidate subprocess has more than 7 substeps when exploded.

**Rule:**
- If detail map exceeds 7 major steps, split into two detail maps:
  - Example: "Wash Cycle" is too large; split into "Wash Cycle – Load Phase" and "Wash Cycle – Run Phase"
  - Cross-reference both from the main map: "Wash Cycle (See Detail Maps 3.1–3.2)"
- Do **not** compress a detail map by consolidating steps into vague names; that defeats the purpose of zooming

### 4.4 Conditional Flows Without a Decision Diamond

**Scenario:** A flow branches but no formal approval or decision gate is modeled; the split is due to environmental or data-driven condition.

**Example:** "Order Received" → routes to either "Standard Path" or "Premium Path" based on order type, but there's no explicit decision point in the process (it's a data attribute).

**Solution:**
- Use a decision diamond if the process makes an explicit choice (e.g., an employee looks at a checkbox and routes accordingly)
- Use conditional arrow labels if the data attribute is simply noted: label the diverging arrows `"[Standard order]"` and `"[Premium order]"` without a diamond
- If unclear, default to a diamond; it's more explicit and pedagogically safer for students

### 4.5 Crossing and Overlapping Flows

**Scenario:** Multiple arrows cross or loop paths tangle the diagram.

**Best practices:**
- Re-order or re-layout steps horizontally or vertically to minimize crossings
- If rework loop must cross another flow, use a bridge notation (arc) to show layering
- If diagrams become too tangled despite re-layout, it's a sign the process is complex enough to warrant detail maps

---

## 5. Diagram Types and Examples

### 5.1 Current-State Map (White Belt Foundation)
**Purpose:** Baseline snapshot of the process as it exists today  
**Scope:** Usually 5–10 major steps  
**Key elements:**
- All steps in actual order observed
- Complete data boxes (role, CT, WT)
- All VA/RNVA/NVA colors applied
- Rework loops and decision diamonds marked
- Queue circles at major bottlenecks (top 2–3 wait times)

**Example:** Wash n' Fold current-state (Chapter 4)
- 7 major steps from drop-off to payment
- Rework loop on "Sort & Tag" (8% fail, recirculate to full wash)
- Queue circle before "Fold & Pack" (35-minute wait)
- Three VA steps (Wash, Dry, Fold & Pack); others RNVA

### 5.2 Future-State Map (Yellow Belt+)
**Purpose:** Proposed improved process  
**Differences from current-state:**
- Steps eliminated or consolidated
- Wait times reduced or redistributed
- New process paths (e.g., pull vs. push system)
- Same symbol set and color rules apply

### 5.3 Detail Maps (Yellow Belt+)
**Purpose:** Zoom into a subprocess to find root causes  
**Scope:** 3–7 substeps of one major step  
**Example:** "Wash Cycle" detail map
- Load Machines (VA)
- Run Cycle (VA, 45 min CT, 0 min WT)
- Unload (RNVA, 10 min CT)
- Quality Check (RNVA, 5 min CT, 2 min WT)
- Move to Dry Queue (RNVA)

---

## 6. Authoring Checklist

Use this before finalizing any SPPM diagram:

- [ ] **Scope clarity:** Start and stop events are clearly labeled and unambiguous
- [ ] **Data completeness:** Every process step has a data box with role, cycle time, and wait time
- [ ] **Value classification:** Every step is colored Green (VA), Gray (RNVA), or Red (NVA)
- [ ] **Rework loops labeled:** Every dashed arrow includes rework rate or frequency
- [ ] **Queue visibility:** Top 2–3 bottleneck wait times have queue circles
- [ ] **Decision diamonds clear:** Each diamond has a clear question or gate label and output arrows
- [ ] **Subprocess notation:** Any zoomed-in step is marked, and detail map is referenced
- [ ] **Swimlanes (if used):** Consistent across all diagrams; handoffs are explicit
- [ ] **Legend:** Any non-standard notation is explained in diagram caption or inset
- [ ] **Flow direction:** Consistent left-to-right or top-to-bottom across all diagrams in document
- [ ] **Font and readability:** Sans-serif, 10–12 pt minimum; contrast is sufficient for web and print
- [ ] **Size constraints:** Diagram respects specified max width and max height; if exceeded, split into multiple diagrams or create detail maps rather than shrinking text
- [ ] **Color palette:** All colors use hex values from Section 3.6.1
- [ ] **Spacing:** Minimum 0.2" horizontal, 0.3" vertical between elements
- [ ] **Multiple rework modes:** Each distinct failure mode has its own labeled dashed arrow if paths differ

### 6.1 Tool Setup Checklist
Before creating any diagram, configure your tool with these defaults and specify your max width/height constraints:

**Google Drawings:**
- [ ] Create a custom color palette with all hex values from Section 3.6.1
- [ ] Create shape stencils for each element type with correct sizing (rectangles 1.5" × 0.6", circles 0.5–0.7", diamonds 0.9" × 0.9")
- [ ] Set default text font to Arial 11pt, bold for process labels; 9pt for data boxes
- [ ] Specify max width and max height in document comments or as a layer (e.g., "Max: 7"W × 10"H")
- [ ] Optional: insert a reference rectangle with your max dimensions to guide layout
- [ ] Save as a team template for reuse

**Draw.io / Diagrams.net:**
- [ ] Import or create custom shape library with SPPM elements (rectangles, circles, diamonds, rounded rectangles)
- [ ] Define colors in Preferences → Colors using hex palette
- [ ] Create diagram template with grid enabled (0.1" grid for sizing precision)
- [ ] Set canvas/page size to your specified max width and max height (e.g., 7"W × 10"H) so the visual boundary is enforced
- [ ] Configure default arrow style: 1.5pt solid, dark charcoal; dashed variant with 3–2 dash pattern
- [ ] Export settings: SVG (scalable) and PDF (print-ready)

**Lucidchart / Visio:**
- [ ] Create a shared library with stencils for each SPPM element
- [ ] Define a named style guide for process boxes (Green, Gray, Red) with exact hex colors
- [ ] Create a document template where authors specify max width and max height before starting (e.g., via document properties)
- [ ] Add margin guides based on specified dimensions
- [ ] Define connector styles: solid (1.5pt, dark) and dashed (1.5pt, red)

---

## 7. Tool Recommendations

**Approved tools for SPPM:**
- Google Drawings (free, collaborative, web-based)
- Draw.io / Diagrams.net (free, open-source, SVG export)
- Lucidchart (commercial, but template-friendly)
- Microsoft Visio (commercial, standard in enterprise)
- Miro or Mural (whiteboarding tools, good for team workshops)

**Not recommended:**
- Proprietary Lean software that requires licenses (defeats "simple tool" principle)
- Hand-drawn scans without clear digital redraw (legibility in PDF/web)

**Export format:** SVG (scalable, web-friendly) or PDF (final print-ready); PNG only if resolution ≥ 300 dpi

---

## 8. Future Extensions (Green Belt and Beyond)

**Do not implement at White Belt; documented for forward planning:**

- **Capacity annotations:** Mark bottleneck steps with resource count and max throughput (e.g., "1 machine, 45 min/cycle")
- **Cycle-time distribution:** Annotate high-variability steps with range or coefficient of variation (e.g., "CT: 30 ± 15 min")
- **Cost or value annotations:** Label steps with labor cost, material cost, or customer-perceived value
- **Takt time reference:** Draw takt line or target line across the map to highlight gaps in flow
- **Simulation readiness:** Structure detail maps to feed discrete-event simulation (Yellow Belt+)
- **Multi-variant overlay:** Show all variants on one map with colored paths (alternative to separate detail maps)

---

**Document Control:** This specification is version 1.2, finalized May 4, 2026. Updates will be tracked in the repository history.
- **v1.0 → v1.1:** Added Visual Design Guidelines (color palette, sizing matrix, line specs), Edge Cases section, diagram-level size constraints (max 7"W × 10"H), tool setup checklist, subprocess depth rule.
- **v1.1 → v1.2:** Updated color palette to reflect FLO default theme colors (#81C784 VA, #FFF176 RNVA, #EF9A9A NVA). Added Section 3.6.1b documenting theme system (default, print, monochrome, custom themes) and how to apply or define themes for different contexts.
