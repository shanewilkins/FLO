# Historical architecture assessment and remediation evidence

This is a chronological record, not the current implementation contract. Gate
statuses and temporary paths describe their respective milestones. Current
dispositions and acceptance are in [the validation report](architecture_validation.md).

# Architecture validation: current release candidate

Status: R1–R3b complete; AF-001–003 closed. Clean-candidate platform acceptance (R4) is in progress.
Assessment date: 2026-10-23. Governing release requirement: TR-118.

The assessment covers the current working tree based on HEAD
`60c2c98be0c36bd3b71908ceb44b85c68e716804`. Runtime package fingerprint:
`b4a0876f32eabe419c0a1b6da924d5f04f61cd0cb0b3ce766d6588af4623c934`.
This is an assessment of an uncommitted candidate, not acceptance of that HEAD
or a new known-good release baseline. The
[machine evidence](architecture_validation_evidence.json) records source inputs,
configuration and architecture-document hashes, loaded distribution identity,
artifact hashes, observed geometry stages, and detected responsibility breaches.

## Result

The architecture's main separation remains appropriate. The implemented four
packages, dependency direction, optional-mining boundary, renderer independence,
and SVG/Typst output split pass their current boundary checks. The initial assessment identified three rendering
responsibility violations. R1 closes AF-003 and R2 closes AF-002; AF-001 still blocks release. They require refactoring within the
existing architecture, with the ownership clarification recorded in
[the accepted finalization ADR](adr/render_layout_finalization.md).
There is no evidence from this assessment that ELK must be replaced.

Functional parity is a passed behavioral check, not a waiver of the findings.
The architecture acceptance command intentionally returns nonzero while the
responsibility breaches are detected. No production rendering code was changed
by this assessment slice.

## Effective architecture inventory

| Decision or contract | Effective obligation | Assessment disposition |
| --- | --- | --- |
| [Simplified package ADR](adr/simplified_package_architecture.md) | `process`, `source`, `render`, and `app`; domain inward dependencies; app composition; no extra substantive top-level packages without demonstrated need | Four packages present; dependency and private-import checks pass. Root `flo.api` remains the supported public integration facade, not another substantive package. Its source workflow duplication is debt, not evidence that the package consolidation failed. |
| Same ADR, mining boundary | PM4Py optional, lazy, quarantined behind a future bridge; no mining types crossing into core | No bridge or runtime dependency is present. Its implementation is explicitly deferred to the first mining slice; absence is not a violation. AST/dependency checks pass. |
| [Renderer boundaries](renderers/boundaries.md) | Four independent renderer packages, one registry, renderer-owned diagram conventions, neutral mechanisms below | Registrations and import directions pass. R2 moves SPPM conventions into SPPM-owned policy; AF-002 is closed. |
| [Render stack ADR](adr/render_stack_elk_svg_typst.md) | ELK algorithmic layout, FLO SVG, Typst composition; no Graphviz or browser product runtime | Implemented stack matches. No legacy Graphviz modules or browser-library runtime imports/core dependencies detected. Browser testing is distinct from a product runtime dependency. |
| [SPPM design](renderers/sppm.md) | SVG consumes supplied geometry; historical presentation transforms must not create competing routing policy | Cosmetic serialization alone is not a violation. The stress case's node repositioning and route reconstruction exceed that allowance; the finalization ADR now makes the boundary explicit. |
| [Target architecture](render_platform_target_architecture.md) | Diagram policy -> layout -> SVG emission -> composition; emitter does not choose layout | Effective responsibility split applies now; implementation fails AF-001. Sections explicitly titled Proposed are design sketches, not demands to create every suggested package or diagram type. |
| [Geometry ADR](adr/render_geometry_overflow.md) | Unit-aware requested geometry becomes a layout constraint; viewport fit is explicit and inspectable | Public entrypoint prepares/resolves geometry; observed paths agree for explicit equivalent options. Golden generation now consumes the shared execution result; AF-003 is closed by R1. |
| [Publication model](publication_model.md) | Shared page model transports content; renderers own semantic metrics; composition does not route the graph | Shared planner and Typst emitter are separate. Standalone bands are supported; full multi-page and child-map acceptance stays in 0.5. Page-local projection dictionaries are internal diagram inputs, not mutations of authored IR. |
| [Diagnostic delivery plan](diagnostic_delivery_plan.md), TR-117 | Common envelope, severity-aware success, and deduplicated delivery are committed next-sprint work | Present source/analysis/render records and logging are distinct. Shared delivery is not falsely described as implemented. Coordinate its later change with the finalization seam; do not silently broaden this assessment into that implementation. |
| [Finalization ADR](adr/render_layout_finalization.md) | One execution path, diagram-owned policy, inspectable final geometry, geometry-consuming emission | Accepted ownership clarification for next-release acceptance. R1 implements shared execution and R2 restores policy ownership; geometry work remains pending under AF-001; it does not retroactively declare drift compliant. |

Existing file-length and complexity exclusions were inventoried. They are
nonblocking debt by themselves; they neither prove a responsibility violation nor
waive one. No exemptions were added to conceal the findings.

## Observed responsibility and data flow

| Stage | Current owner and values | Mutations or decisions | Intended boundary |
| --- | --- | --- | --- |
| Source parsing/composition | `source.parse_adapter` / composition helpers -> mapping and provenance | Resolves includes under source trust rules; no diagram geometry | Source owns authoring and composition |
| Compile | `source.compile_adapter` -> typed IR | Normalizes aliases, identities, edges, process context | Compiler owns source lowering; compile alone intentionally does not semantically validate |
| Validate/analyze/export | `process.ir`, `process.analysis`, `process.export` | Semantic/schema checks, timing and structural facts, canonical serialization | Domain remains independent of CLI and rendering; API/app choose operation delivery |
| Application / public facade | `app.run_content`, `api.validate/inspect/export` | Source diagnostics, options/config/view resolution, command choice, I/O | Public facade adapts supported operations; app coordinates CLI/config/I/O |
| Render entrypoint | `render.render_artifact_and_contract` -> prepared options -> registry | Applies geometry preparation; later resolves viewport/fit | One production execution sequence with observable intermediate results |
| Projection/measurement/request | `sppm.layout`, content helpers -> `ElkLayoutRequest` | Chooses subprocess projection, node measures, rows, ports, correction decorations | SPPM owns these conventions |
| Engine and normalization | `layout_core.elk_runtime` / `elk` -> `LayoutResult` | Executes Node/ELK and normalizes coordinates; also applies SPPM spacing, wrapping, placement, and rerouting | Neutral engine seam should execute/normalize; diagram policy belongs to SPPM (AF-002) |
| Display finalization | `sppm.renderer._display_geometry` -> copied node/path dictionaries | Row alignment, correction placement, route rebuilding, orthogonalization, canvas recomputation | Belongs to an explicit layout finalization stage, not SVG assembly (AF-001) |
| Shape/annotation emission | `sppm.edges`, node/primitives helpers -> SVG strings and annotation bounds | Computes shape attachments, label/callout/token positions, collision avoidance; infers correction styling | Geometry decisions must be captured before shape emission (AF-001) |
| Artifact / viewport | `RenderArtifact` and neutral geometry resolver | Theme paint/typography; requested dimensions, aspect ratio, fit metadata | Preserve the public artifact API; expose finalized scene/viewport through the one execution result |
| Publication | `sppm.publication*`, neutral page model, `typst_publication` | Plans pages/bands, projects page-local figures, emits Typst references | Publication owns composition, diagram pipeline owns figure geometry |

`LayoutResult` currently calls its fields “final”, but SVG assembly can still
change them and introduces annotations not represented in that value. Its frozen
dataclass also contains mutable dictionaries. The latter is a contract-design
risk, not an observed IR mutation: all three probes preserve the IR object and
canonical export. Do not claim that `frozen=True` proves deep immutability.

## Representative traces

All cases use identical explicit options across the compared paths. CLI config
and named-view resolution are application responsibilities; lower-level Python
rendering is compared after selecting equivalent options, not assumed to apply
CLI configuration implicitly.

| Input | CLI / Python / golden / installed CLI | Repeat / IR preservation | Work observed during SVG assembly |
| --- | --- | --- | --- |
| `valid_basic_linear.flo` | Identical bytes across all four | Repeatable; canonical export and IR object unchanged | No node/route correction and no edge labels required |
| Width-wrapped `book_washnfold.flo` | Identical bytes across all four | Repeatable; canonical export and IR object unchanged | Display orthogonalization changes 10 route point sequences; 3 edge labels placed during assembly |
| `sppm_long_label_stress.flo` | Identical bytes across all four | Repeatable; canonical export and IR object unchanged | `rework` node moves; 2 display routes change; shape clipping changes 4 routes; 2 edge labels placed during assembly |

The wrapped case's changed point sequences include orthogonalization; their
count alone is not proof of a semantic or visual defect. AF-001 is established
by responsibility ownership and the stress case's actual node repositioning,
route rebuilding, and paint-time geometry decisions.

All three have zero render diagnostics. The installed package's runtime source,
schema, and JavaScript fingerprint matches the checkout, and its modules load
from its isolated site-packages. Installed CLI output is generated from an
isolated working directory. This is local current-candidate evidence; clean
Linux/macOS CI and immutable release acceptance remain pending.

The golden builder's functional parity fix is effective but insufficient for
ownership: it still manually calls preparation, request building, ELK execution,
normalization, assembly, and viewport resolution. Its `layout_result.json` is
an intermediate layout snapshot, not an authoritative description of every
position painted in `render.svg`.

## Findings register

### AF-001 — Closed by R3b: complete final scene before SVG assembly

**Governing decision:** target architecture's layout/emission split, clarified
by the finalization ADR. **Status:** closed by R3b; platform acceptance remains R4 work.

**Initial evidence:** `sppm/renderer.py::_display_geometry` and
`render_sppm_svg_artifact_from_layout`; `sppm/rows.py` and `row_routes.py`;
`sppm/edges.py::_clip_edge_points_to_node_bounds`, label/callout/token placement,
and overlap avoidance. The stress trace demonstrates an actual node move and
route/attachment changes after `LayoutResult` exists. The renderer reconstructs
rework membership for styling as well as placing annotations.

**Consequence:** layout snapshots and downstream diagnostics can describe a
geometry state different from the emitted artifact. Fixes at one stage can
invalidate earlier attachment, label, or spacing assumptions. Output tests must
reverse-engineer SVG to inspect final positions.

**Closure:** a typed, inspectable finalized geometry value contains every bound,
route, attachment, annotation, and related diagnostic actually consumed by the
emitter. Shape emission performs no placement/routing/collision policy. Tests
prove the emitter consumes the supplied geometry without changing it, including
stress labels, continuation tokens, and visible lanes. Retain independent SVG
checks. A file move without this contract does not close the finding.

### AF-002 — Closed by R2: the neutral engine seam implemented SPPM policy

**Governing decision:** renderer ownership rules 1–3; finalization ADR.
**Status:** closed by R2; see the completion record below.

**Initial evidence:** `layout_core/elk.py` branched on `request.diagram == "sppm"` to
balance queue/task gaps, normalize horizontal spacing, construct wrapped rows,
choose correction placement, and reroute edges. `elk_sppm_helpers.py` and
`wrapped_rework.py` contain SPPM conventions in the neutral core. The existing
neutral-module policy test lists selected files and omits `elk.py`; imports can
therefore be acyclic and legal while responsibilities remain misplaced.

**Consequence:** an engine-normalization change can alter a diagram's conventions;
layout ownership is obscured by the module boundary. Import Linter cannot detect
policy implemented locally without a forbidden import.

**Closure:** SPPM owns its decisions and bounded layout passes. The neutral seam
retains execution, coordinate normalization, reusable contracts/mechanisms, and
narrow callback/adapter inputs as needed. Check every neutral core module's
ownership rather than grandfathering the offending files. Preserve bounded
above/below selection and unchanged semantic IR; do not create a general plugin
framework or move all reusable geometry into SPPM.

### AF-003 — Closed by R1: tools duplicated production orchestration

**Governing decision:** accepted finalization ADR's single production sequence.
**Status:** closed by R1; see the implementation and verification record below.

**Initial evidence:** `_build_case` in `build_sppm_baseline_artifacts.py` assembled the
sequence independently of `render_artifact_and_contract`. It needs intermediate
request/response/layout values, which the current artifact result does not expose.
Parity currently passes for all three probes; no current output mismatch is
claimed. Also inventory `sppm/publication_artifact.py::_render_sppm_page_svg_assets`
(which calls the diagram renderer directly) and the SPPM/swimlane layout-only
helpers during R1. Page-local figures and layout-only diagnostics are legitimate
stage consumers, but must have an explicit stage contract rather than silently
bypassing or reproducing full artifact preparation. The earlier missing geometry preparation demonstrates the failure mode.

**Consequence:** new production stages must be manually mirrored in tools; one
book parity fixture does not prove all consumers execute the same pipeline.

**Closure:** one execution function produces the artifact and optional stage
trace. Public rendering and golden generation call that function; diagnostic
output consumes its trace. Tests instrument the actual common entrypoint and
verify each consumer reaches it, with parity/repeatability for all three inputs.
Keep supported precomputed-layout APIs explicit about their stage.

### Nonblocking debt and resolved ambiguities

- **D-001, test coverage of responsibilities:** existing architecture tests mostly
  protect imports, registrations, legacy removal, and one global-preprocessing
  sentinel. New assessment probes detect concrete policy/assembly breaches; they
  do not pretend to prove arbitrary semantic responsibility automatically. Close
  the blind spots as part of AF-001–003; current green policy tests alone are
  insufficient for release.
- **D-002, pipeline typing/immutability and module size:** `Any`, mutable nested
  maps, private helper re-exports, and large-file exclusions increase coupling.
  Address contracts touched by the remediation. They do not justify an unrelated
  package-wide type cleanup in this slice.
- **D-003, validation orchestration duplication:** public API and app both compose
  source compilation and validation. Existing end-to-end semantic tests protect
  compatibility. A reusable domain/source operation could reduce drift, but this
  review found no current differing acceptance in the traced inputs. Do not
  conflate a public facade with a forbidden extra substantive package.
- **Resolved wording:** ELK supplies algorithmic layout; FLO owns bounded
  diagram-specific finalization. SVG emits supplied geometry. Future target type
  and package sketches remain future. The accepted ADR records this distinction;
  it does not accept AF-001–003 as compliant implementations.

## Bounded remediation sequence

| Slice | Scope and stop condition | Finding closed / evidence required |
| --- | --- | --- |
| R1: complete — one execution result and trace | Centralize production sequencing; expose intermediate request/response/layout for tools while preserving the public artifact return contract. Golden generation becomes a consumer. Stop at one shared sequence and three-input parity. | AF-003; call-through checks plus CLI/Python/golden/installed byte parity, repeated output, IR preservation |
| R2: complete — diagram-owned policy | Move SPPM placement/wrapping/spacing decisions to SPPM-owned layout passes; leave generic normalization/execution in core. Stop when neutral code implements no SPPM convention. | AF-002; complete neutral-module boundary checks, independent-renderer tests, bounded rework tests, corpus parity |
| R3a: complete — finalized nodes and routes | Materialize row adjustments, canvas/lane bounds, correction membership, and routed geometry before SVG assembly. Keep the existing output stable while moving ownership. | Partial AF-001 evidence only; cannot close AF-001 yet |
| R3b: complete — finalized attachments and annotations | Materialize attachments, labels, callouts, tokens, occupied bounds and diagnostics; make SVG emission a geometry consumer. Resolve viewport/fit within the same execution contract. | AF-001; geometry-consuming emitter checks, independently parsed final SVG invariants, three-case stress/repeatability evidence |
| R4: candidate architecture acceptance | Re-run all boundary and functional gates and clean installed/consumer CI on the immutable candidate; reconcile effective docs and findings. | TR-118 acceptance record; no open architecture violations, reviewed source/artifact identities |

Each slice should retain existing semantics and diagnostics. Only newly discovered
correctness defects justify reviewed output changes; a refactor should not
silently rebaseline appearance. Architecture acceptance remains blocked until all
remaining findings close and R4 evidence is complete. Browser legibility acceptance
and stable promotion follow this remediation sequence.

## Reproduction and check interpretation

Run the assessment against a matching installed wheel:

```sh
.venv/bin/python scripts/architecture_trace.py \
  --installed-python /tmp/flo-release-env/bin/python \
  --output /tmp/flo-architecture-validation.json --check
```

The installed interpreter location is a local example; prepare an isolated wheel
environment for the candidate being assessed. `--check` returns 1 on detected
responsibility violations or behavioral/package mismatch. Without `--check`,
the command can successfully record blocked findings; that is evidence capture,
not a green architecture gate. Missing installed evidence is reported explicitly.

`architecture_boundaries.py` detects the specific current implementation seams
through AST observations. Tests include synthetic offending and compliant
examples; detector tests passing means detection works, not that production
architecture passed. The probe must migrate with the accepted execution/geometry
contract during remediation rather than become a permanent symbol-name waiver.

Existing policy tests and all ten Import Linter contracts pass. The assessment
adds browser-runtime boundary checks and representative entrypoint/IR-preservation
checks. No known-failure tests are marked xfail or silently skipped to claim
acceptance. The structured evidence's acceptance state remains pending even if
future automated responsibility probes return clean; final candidate review is
still required by release policy.

## Validation results and release enforcement

The focused assessment and policy suite passes: 42 tests. All ten Import Linter
contracts pass. The three representative inputs agree across Python, CLI,
golden generation, and the matching installed wheel; repeat rendering is stable
and canonical IR remains unchanged. No production rendering code changed in this
assessment.

The installed-wheel assessment with `--check` returns 1 as expected because
AF-001 and AF-002 remain open (AF-003 is now closed by R1). This is a blocked architecture result,
despite the passing behavioral checks.

Both platform wheel jobs now run that check. The publication workflow also runs
it after installed-wheel smoke testing and before distribution artifact upload;
the publishing job depends on that build. These checks intentionally fail until
the responsibility violations are resolved. Policy tests verify this wiring;
remote CI has not been run for this working tree. The workflow does not prevent
manual tag or GitHub release creation: pre-tag review and immutable, clean-candidate
acceptance remain required under R4 and TR-118.


## Boundary enforcement follow-through

The neutral import contract now covers complete package trees and classified
root modules, including indirect dependencies on dispatch or diagram packages.
Policy tests force classification of newly added root modules/packages and reject
neutral imports through the public rendering facade. Fresh-package tests run the
actual configured Import Linter contract against deliberately bad absolute,
relative, aliased, and nested imports, plus a permitted neutral dependency.

The responsibility probe is also a fast, unfiltered pre-commit gate, so existing
AF-001–002 block ordinary quality checks before engine rendering or packaging.
The SPPM policy detector scans every neutral layout Python file, including nested
definitions/classes; call probes recognize imported aliases. This expands early
regression detection without waiving current debt. It still cannot establish
semantic neutrality from names alone. R1–R3 remain responsible for durable
execution/geometry-consumer contracts as their production interfaces are built.


## R1 completion: shared production execution

`flo.render.render_execution` now owns option preparation, registry dispatch,
viewport resolution, and the returned artifact. `render_artifact` and
`render_artifact_and_contract` delegate to it with their existing return contracts.
Golden generation calls the same function once with `capture_layout=True` and
serializes its returned stage snapshots. It no longer prepares dimensions,
constructs requests, executes/normalizes ELK, or invokes emission itself.

`RenderExecution` exposes prepared options, the final artifact, and optional
`ElkLayoutTrace` snapshots of request, serialized request, raw response, and
normalized engine geometry. Capture is off by default. Engine observations are
deep copies, so observer mutation cannot affect production geometry. These are
explicitly intermediate engine results; they do not claim the final-scene
contract required by R3. No ambient/global observer state is used.

Consumer inventory: page-local publication figures call the same diagram
entrypoint after publication planning supplies figure options. They deliberately
omit standalone viewport preparation/resolution and do not recreate engine
sequencing. `layout_sppm_with_elk` and `layout_swimlane_with_elk` remain explicit
layout-only diagnostic APIs; `render_sppm_svg_artifact_from_layout` is an explicit
precomputed-layout emission stage. Their docstrings distinguish these stages
from complete artifact execution. No new engine implementation was introduced.

Evidence and scope:

- Full suite: 1,215 passed, 93.40% coverage. Seven Click test-helper deprecation
  warnings remain; they are unrelated to rendering diagnostics.
- All 13 corpus cases / 26 committed golden files match byte for byte.
- Three representative inputs agree across Python, CLI, golden generation, and
  the rebuilt installed wheel, with repeatability and full IR preservation.
- Ten import contracts, type checking, Ruff, formatting, documentation governance,
  and docstring checks pass. Call-through and dependency tests prevent the golden
  builder from importing rendering implementation stages. Observer tests establish
  one engine call and isolation from mutations to captured snapshots.
- The broad complexity probe still reports the existing precomputed SPPM emitter
  at 18 (threshold 15). R1 changes its stage documentation, not its body; R3 owns
  its geometry/emission separation. No exclusion or threshold was added.
- Local wheel: `/tmp/flo-r1-dist/flo_lang-0.4.2-py3-none-any.whl`, SHA-256
  `ce71fb33e118dd31ce7199071659e078e570c251985f35c8f360c55bbba2a307`;
  isolated environment: `/tmp/flo-r1-env`. This is local working-tree evidence,
  not immutable clean-CI release acceptance.

The fast and installed architecture checks now report only AF-001 and AF-002
and still return 1. R1/AF-003 is complete; R2 is next. R3 and final R4 acceptance
remain required before release.


## R2 completion: diagram-owned ELK policy

SPPM now owns request serialization choices (`elk_serialization.py`), strategy
resolution (`strategy.py`), row/partition helpers (`elk_helpers.py`), namespace
rules (`namespace.py`), spacing (`layout_spacing.py`), wrapping/routes
(`layout_wrap.py`), and bounded correction placement (`wrapped_rework.py`). The
old SPPM modules in `layout_core` are removed, with no import-back shims. Their
tests and measurement-tool inventory now reference the owning package.

The neutral request carries explicit `ElkSerialization` settings (root/lane/node/
edge options, supplied ports and endpoints, label participation, auxiliary graph
objects, and terminal-layer constraint enablement) and an optional typed
`result_transform`. The engine normalizes coordinates, executes that supplied
transformation, checks diagnostics, and records the same stage snapshot as before.
It never selects a transformation by diagram name. Low-level callers needing
SPPM conventions use the SPPM request builder; setting `diagram="sppm"` on a
neutral request does not implicitly activate policy. Strategy environment values
are resolved when the diagram constructs the request, not during neutral
serialization. No plugin discovery, global policy registry, or new engine was
introduced.

Generic graph serialization lives in `layout_core/serialization.py` and returns
detached payload data. Coordinate translation, box/segment intersection,
rework semantic inference, lane-generation mechanisms, and generic namespace
collision checking remain shared. Builders supply their reserved namespace data;
SPPM-owned reserved prefixes no longer live in neutral validation. Auxiliary
response edges are excluded by declared IDs rather than a hard-coded SPPM prefix.
Unknown edges with a forged helper-looking ID now receive the ordinary unexpected
edge diagnostic; this does not change any legitimate corpus diagnostics or bytes.
Swimlane supplies its own serialization settings without depending on SPPM.

Verification:

- Full run: 1,220 tests passed, 93.62% coverage; seven existing Click test-helper
  deprecation warnings. Subsequent focused checks cover the additional auxiliary-ID
  regression test and final import/type cleanup.
- All 13 corpus cases / 26 golden files match byte for byte. Three representative
  inputs retain Python/CLI/golden/installed-wheel parity, repeatability, and full
  IR preservation.
- Ten import contracts, type checking, Ruff/formatting, docstring checks, and
  Vulture pass. Extracted policy and serialization functions pass complexity
  checks. The previously recorded emitter complexity remains part of R3.
- Behavioral boundary tests prove that changing a neutral request's diagram tag
  or SPPM environment variables cannot activate policy; only an explicitly supplied
  transformation runs. They also prove request/payload isolation and independent
  swimlane settings. Existing bounded above/below correction tests pass under
  SPPM ownership.
- The source probe now catches diagram-tag comparisons, SPPM symbols, reserved
  strings, and environment keys throughout the neutral tree, alongside existing
  import contracts. Arbitrary hidden semantic policy still requires architectural
  review; a symbol scan is not a semantic proof.

Current installed-wheel identity and runtime source fingerprint are recorded in
`architecture_validation_evidence.json`. This remains local working-tree evidence;
immutable clean-CI acceptance under R4 is not claimed. The source and installed
checks report only AF-001 and intentionally return 1. Next are R3a/R3b (finalized
geometry and geometry-consuming emission), followed by R4 acceptance.

Final R2 local wheel: `/tmp/flo-r2-dist/flo_lang-0.4.2-py3-none-any.whl`,
SHA-256 `ec12c5a2c56410fe6697c64f87a2b8dea5565ffd0dae2f75a3ae4b141c0ac818`;
matching isolated environment: `/tmp/flo-r2-env`.


## R3a completion: routed geometry before SVG

`finalize_sppm_geometry` now runs row alignment, route rebuilding/orthogonalization,
canvas calculation, visible-lane selection, correction membership inference, and
row diagnostics before emission. It returns a typed `RoutedGeometry` value with
read-only detached node/route/group mappings, frozen bounds/paths/lane values,
content canvas bounds, and diagnostics. Engine `LayoutResult` remains an explicit
intermediate contract and is not mutated by finalization.

The production orchestrator passes this value to
`sppm/svg.py::emit_sppm_svg_artifact`. That entrypoint consumes supplied node
positions, route points, lane/canvas bounds, and correction connector membership;
it does not rerun row layout or infer membership. Precomputed engine-layout
callers pass through the same finalizer. `render_execution(capture_layout=True)`
now exposes `geometry_stages` alongside engine snapshots. Capture stays optional,
with explicit observers and no ambient state. The stage is currently supplied by
SPPM; other diagram renderers do not claim a geometry stage they have not built.
Observer diagnostic data is detached from the render in progress.

Routed geometry is not the complete final scene: shape attachment clipping,
labels/callouts/tokens, avoidance, occupied annotation bounds, publication bands,
and artifact viewport resolution still require their existing subsequent stages.
AF-001 remains open until R3b materializes the remaining placements and makes SVG
emission a complete geometry consumer. This slice preserves emitted bytes rather
than changing those policies.

An eleventh Import Linter contract forbids direct or indirect dependencies from
the SVG emitter to node/route layout-policy modules or ELK execution. Policy tests
protect the contract from removal or exemptions. Behavioral tests deliberately
supply changed positions, a multi-bend route, a different canvas, and correction
membership; parsed SVG reflects the supplied values without re-entering layout.
They also verify immutable/detached maps, engine-result preservation, deterministic
finalization, visible-lane filtering, and finalization-before-emission order.
Independent final-SVG geometry checks remain in place.

All 13 cases / 26 golden files match. The architecture trace now records the
routed node/edge geometry, visible lanes, groups, and canvas before SVG emission,
while still counting attachment/annotation work during emission. Refactor
measurements include both new implementation files (`svg.py` and `geometry.py`)
so moving code out of `renderer.py` does not hide it from the measured scope.
The current implementation passes the complexity threshold, including the
extracted emitter; the earlier emitter complexity observation is superseded.

Full-suite and installed-wheel results for this slice are recorded below and in
`architecture_validation_evidence.json`. The architecture check intentionally
continues to return 1 for AF-001. R3b and clean immutable R4 acceptance remain
required before release.

Final R3a verification: 1,226 tests passed, 93.64% coverage, seven existing Click
test-helper deprecation warnings. Eleven import contracts, type checking, Ruff,
formatting, docstring checks, Vulture, and the scoped complexity check pass.
The rebuilt wheel matches source and all three inputs agree across Python, CLI,
golden generation, and installed CLI, with repeatability and IR preservation.
Local wheel: `/tmp/flo-r3a-dist/flo_lang-0.4.2-py3-none-any.whl`, SHA-256
`00fff3f0c6573b4912f70f36b120784c6c76b81f7c6c50f131e509c7347e6dcd`;
isolated environment: `/tmp/flo-r3a-env`. Clean immutable R4 acceptance remains pending.


## R3b completion: final scene and pure emission

`finalize_sppm_scene` materializes attached edge points, ordered labels/callouts/
continuation tokens, every annotation rectangle and text baseline, occupied
annotation bounds, diagnostic outcomes, publication-band positions, natural SVG
size, and content origin. `FinalScene` contains typed geometry rather than SVG
fragments. Capture exposes `RenderExecution.scene_stages`. The SVG serializer
consumes this scene; the public execution path still owns the final viewport/
fit transformation and exposes the resolved numeric geometry in artifact metadata.

Attachment geometry lives in `attachments.py`, annotation policy in
`edge_layout.py`/`edge_geometry.py`, and pure connector paint in `edge_svg.py`.
The import contract forbids both SVG emitters from depending directly or indirectly
on finalizers, attachment/annotation policy, avoidance, or engine layout. Explicit
private route/token test adapters in `edges.py` combine named stages but are absent
from the production emission dependency tree. Their policy tests reference the
actual owning modules; no private policy re-export is used to hide ownership.

The SPPM width-to-wrap budget moved from shared viewport resolution into its own
registered option preparation. The remaining shared viewport code applies generic
requested dimensions, expansion, scale, and safe-fit rules. This restores the
same diagram-owned policy rule beyond the engine module. No public CLI or artifact
return contract changes. Existing exclusions for the now-bounded core/edge files
were retired rather than transferred to the extracted files.

The full local quality gate passes. The initial R3b full run passed 1,230 tests at
93.72% coverage; added browser-parser/platform-gate tests are verified separately
and will be included in clean CI. All 26 golden files, final-SVG invariants,
accessibility names, themes, and physical sizing checks pass. Deliberately altered
scene points/annotation positions are serialized unchanged while placement and
attachment functions are disabled. Strict diagnostics fail during finalization.
The trace measures policy calls during actual emission; it does not infer zero
calls merely from the existence of a final-scene object.

R4 now requires the immutable candidate to pass clean Linux/macOS installed-wheel
checks and browser glyph measurements. Local Edge aborted under the sandbox and
timed out in an isolated unrestricted run; no local browser success is claimed.
The new Chrome consumer gate checks all corpus SVGs for real glyph bounds,
node/annotation/canvas clipping, and the accepted safe scaling floor, retaining
structured results on both CI platforms. External specialist/practitioner sessions
remain the separately approved 1.0 follow-up.
