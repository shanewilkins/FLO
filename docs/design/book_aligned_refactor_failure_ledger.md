# Book-aligned refactor failure ledger

Status: remaining test failures closed on 2026-10-28 against the working tree
based on `64a705a`. All six phases are complete and accepted as of 2026-10-29; the final checkpoint is 2429 passed, no failures or skips.

This is the case-level record for the refactor. The
[implementation plan](book_aligned_contract_refactoring_plan.md) owns ordering;
[the specification](../specs/book_aligned_contract.md) owns intended semantics.

## Verified checkpoints

| Checkpoint | Failed | Passed | Notes |
| --- | ---: | ---: | --- |
| Initial full suite | 89 | 1686 | 7 warnings; 1775 cases. |
| Recovery full suite | 73 | 1726 | 7 warnings; 1799 cases. 16 original failures closed, 24 new contract checks passed, no new failing cases. |
| D-003 full suite | 56 | 1827 | 7 warnings; 1883 cases. 17 recovery failures closed; 84 added checks passed; no new failing cases or collection errors. |
| D-004 full suite | 56 | 1904 | 7 warnings; 1960 cases. 77 added regression cases pass; the failing case set is unchanged from D-003. |
| Publication timing closure | 52 | 1908 | 7 warnings; 1960 cases. The four named existing failures now pass; no new failing cases or added test cases. |
| Duration display closure | 47 | 1913 | 7 warnings; 1960 cases. Five named existing conversion cases closed; no new failures or added cases. |
| Movement export closure | 44 | 1916 | 7 warnings; 1960 cases. Three named movement-export failures closed; no new failures or added cases. |
| Batched migration checkpoint | 3 | 1957 | 7 warnings; 1960 cases. Fixtures migrated; reference projection and task measurement repaired. |
| Remaining-failure closure | 0 | 1966 | 7 existing Click deprecation warnings; all 44 remaining original cases closed, six added regressions pass. |
| Phase 3 semantic closeout | 0 | 2346 | Exhaustive applicability/inventory, collection placement, relation evidence and presentation verification; seven existing warnings, no skips. |
| Phases 4–5 closeout | 0 | 2366 | Compatibility deletion, focused domain validators, complete canonical round trips; runtime Python −1147 lines, tests +188; seven existing warnings, no skips. |
| Movement/export focused suite | 0 | 30 | Export registry and movement analysis; canonical fixtures pass IR validation. |
| Duration/display focused suite | 0 | 101 | Unit conversion and SPPM metadata tests; invalid selected durations exercise canonical profiles. |
| Publication focused suite | 0 | 23 | Existing timing assertions retained; fixtures validated; partial-projection control strengthened. |
| D-004 selected-duration delivery | 0 | 42 | Invalid selected-result API/CLI parity and included-evidence provenance, including fields before IDs. |
| D-003 focused suite | 0 | 118 | Canonical preservation/delivery, migrated validation and round-trip tests. |
| Foundation focused suite | 0 | 152 | Contracts, source models, semantic/timing diagnostics, CLI streams and diagnostic delivery. |

Full-suite command:
`.venv/bin/python -m pytest -q -n 4 --tb=short -p no:cacheprovider`.
Focused command covers `tests/unit/compiler/test_contract_schema_diagnostics.py`,
`test_source_models.py`, and integration `test_semantic_contract.py`,
`test_timing_correctness.py`, `test_diagnostic_delivery.py`, and
`test_cli_posix_streams.py`.

Ruff, formatting, type checking, documentation governance, responsibility
checks, all 11 import contracts, schema generation check, and `git diff --check`
passed at the recovery, D-003 and D-004 checkpoints. The 2026-10-28 closure repeats these gates and closes the
**44 remaining failures**; broader phase obligations remain below. File-length checks for the D-003 files also pass.

The original CI hygiene failure was a uv cache permission failure, not a
manifest/lock defect. Its offline probe passed outside the sandbox; it now uses
an isolated temporary cache and also passes in the full sandboxed suite.

## What a closure means

Every original failing case appears below. A checked case passed in the recovery
full suite. A contract-migration classification identifies retired setup or
assertions; it does not authorize deleting the behavioral assertion. Migrate
fixtures first, then diagnose any remaining consumer failure. Do not add runtime
aliases or loosen geometry/semantic assertions to make a case pass.

## Newly exposed implementation defects

- [x] **D-001 — referenced waiting labels.** Closed 2026-10-28. A presentation-only
  projection resolves direct canonical references before both ELK measurement and
  SVG emission. Authored IR remains unchanged. The actual book SVG displays
  `W/T: 37.9 min` and `W/T: 5.6 min`. Included evidence tests retain zero and
  select presentation `primary` independently of a different `analysis_input`.
- [x] **D-002 — task text overflow.** Closed 2026-10-28. ELK sizing and wrap
  planning now use the same first-class content as emission. Compact body lines
  wrap between complete measurement labels. Packing reserves margins and the
  actual row gap. The book regression checks emitted body baselines and
  conservative estimated text extents against card bounds; raster inspection
  confirms the book timing text fits. Existing White Belt row counts, width,
  overlap and corridor assertions pass unchanged.

- [x] **D-003 — invalid canonical values can disappear.** Closed in the
  D-003 checkpoint. Node relation lists and measurements, process `lead_time`,
  and edge handoff/rework retain malformed supplied values through construction
  and internal JSON round-trip. Exchange projection retains false/empty invalid
  relation values. Existing validators reject them with `E1310`/`E1311`, `E1301`,
  or `E1401`; process measurement shape validation was added using the existing
  profile contract. No runtime aliases or Pydantic dataclasses were introduced.
  Generic diagnostic enrichment now distinguishes field names from words in
  step IDs and locates canonical timing on first-class fields.

  Evidence: 56 new unit cases plus 28 new API/CLI delivery cases pass. Delivery
  tests exercise real canonical reconstruction and validation with substituted
  compiler output, assert identical diagnostic reports, forbid downstream
  consumer calls, and confirm no output artifact is written. Valid omitted
  measurements, integer/float zero, relations, references/context, and structured
  relations retain their behavior in the focused and full suites. Validation and
  serialization fixtures were migrated to the accepted fields while preserving
  their rejection/round-trip purpose. Legacy context normalization remains phase
  4 work; selected duration semantics remain D-004.

The earlier defective preview was not accepted. On 2026-10-28, the corrected
book output was rendered to PNG and visually inspected before golden updates.
All 13 regenerated corpus cases pass final SVG geometry and accessibility checks;
15 intentional artifact changes across eight cases are accepted. Golden drift
checks pass. A newly exposed callout collision was fixed with a bounded
two-axis placement search, and a real-book SVG regression preserves rework
reason/rate content while forbidding annotation overlap.

- [x] **D-004 — invalid selected presentation duration.** Closed in the D-004
  checkpoint. One domain helper applies the shared scalar-duration rules to
  `primary` and any supplied `analysis_input` on node and process profiles.
  Presentation-only profiles are validated even when no analysis result is
  selected. Numeric text, non-scalar selected values, non-duration units and
  conversions overflowing seconds fail with `E1303` before validated inspection,
  export or rendering. Measurement shape checks remain separate.

  Evidence: 77 added regression cases pass. These cover work cycle/wait/setup,
  independent queues, referenced work waits, process lead time, absent/null
  analytical selectors, distinct display/analysis statistics, retained unselected
  modes/counts, and included-evidence provenance. API/CLI error reports agree and
  invalid input writes no render artifact. Integer/float measured-zero and
  omission regressions remain passing. Process supplied lead time stays separate
  from modeled totals; its presentation across outputs is verified in the later phase 3 closeout.

  Diagnostic enrichment now uses the authored node declaration path to locate
  domain errors, preserving root/include field excerpts when timing appears
  before `id`. The final full suite has the same 56 failing cases as D-003;
  D-004 was a real defect without an existing failing regression case.

## Batched closure evidence (2026-10-28)

All 44 cases open at the movement-export checkpoint now pass. Original routing,
port, partition, footer, palette, conversion, geometry and error-delivery
assertions remain. Fixtures use structured rework, first-class relations and
measurement profiles. Schema export preserves descriptions, typed entities and
annotation groups under extensions. Arbitrary notes are display descriptions;
nonsemantic annotations remain extensions. No retired runtime aliases or skips
were added.

Unsupported source fields now assert `E0220`; malformed relation shapes assert
`E0222`; control-node classification asserts the current applicability rule
`E1508`. Process classification rejection occurs at the source boundary, where
that unsupported field exists. Blank subprocess detail references still fail
with `E1333` through the existing extension contract; valid extension references
reach SVG content and publication slots.

Six new cases cover book reference labels/nonmutation, book card text fit, two
included reference profiles (zero and nonzero, with distinct selectors), real
book annotation geometry, and subprocess-extension display. Focused checks ran
throughout; the final full suite passes **1966 cases**, with no skips and seven
pre-existing Click deprecation warnings. Ruff, formatting, type checking, all 11
import contracts, architecture responsibility checks, documentation governance,
schema generation, golden drift, SVG geometry/accessibility and diff whitespace
checks pass. The prior working golden tree was preserved in
`/tmp/flo-goldens-before-20261028` before reviewed artifact updates.

## Phase 3 semantic closeout (2026-10-28)

Full suite: **2346 passed**, no failures or skips, seven existing warnings.
The plan records detailed closeout evidence. New applicability and field-owner
inventory gates cover every authored node field and kind; complete relation
validation and API/CLI presentation retain full supplied evidence. Collections
have one placement under process, including fragments and exchange, without
legacy promotion or precedence. All diagrams distinguish supplied lead time
from modeled results; value-stream cards select primary while analytical totals
select analysis_input. Display names leave reference IDs unchanged. A real wait
shape/connector mismatch exposed during corpus review is fixed and protected.

All 13 corpus cases pass geometry/accessibility and golden drift checks; ten
reviewed artifacts across nine cases reflect intentional presentation changes.
Ruff, formatting, types, architecture/imports, schemas, documentation governance,
valid/invalid example validation and whitespace checks pass. Existing quantity,
provenance, geometry and rejection assertions were migrated and preserved.

## Phases 4–5 closeout (2026-10-29)

The plan records the complete compatibility-removal and simplification evidence.
Nested source uses steps, connections use transitions and source/target, and
retired attrs/endpoint/container coercions are gone. Canonical fields drive
serialization, rendering, SCC analysis and entity exports. Local contract
validation is shared; graph, relation, duration, entity, quantity and provenance
responsibilities have focused owners. Old diagnostic suggestions and runtime
metadata/alias fallback reads are removed.

Full suite: **2366 passed**, no failures/skips, seven existing Click warnings.
Runtime Python shrank from 28094 to 26947 lines (−1147, 4.1%); tests grew by
188 lines. Net runtime-plus-test reduction is 959 lines, excluding generated
schemas, artifacts, documentation and scripts. Existing behavioral assertions
were preserved through canonical fixture migrations and explicit alias rejection.

All standard checks pass, including all 11 import contracts, schema drift and
13 corpus geometry/accessibility/drift checks. Seven reviewed SVGs add explicit
first-class owner/version header rows without changing node layouts or routing.
The earlier artifacts are preserved in `/tmp/flo-phase45-goldens-before`.

## Phase 6 final acceptance — 2026-10-29

**2429 passed, no failures or skips**, seven existing Click deprecation warnings.
The twelve-criterion acceptance matrix is recorded in the refactoring plan.
Typed source/schema boundaries, named context, null handling, profile/reference
applicability, named-target declarations and safe diagnostics have regression
coverage. The documentation inventory, instructional examples and requirements
catalog reflect the implemented contract; broader future publication work is
not claimed complete.

Ruff/format, runtime type checking (`ty check src`), all 11 import contracts,
architecture checks, schema drift, strict documentation governance, file-length
policy and whitespace checks pass. All 27 valid roots rendered to 30 SVGs and
six item summaries; 24 invalid roots were rejected and three include fragments
composed. All 13 golden cases/26 files match, with zero final geometry violations
and passing accessibility checks. Phase 6 introduces no golden changes.

Runtime Python is 27049 lines (−1045 from the phase 4 baseline), tests 27433
(+496), combined −549. These counts exclude generated schemas and artifacts,
documentation and scripts. No original failure is reopened, skipped or hidden
by restored aliases. All changes remain uncommitted.

## Ordered remaining work

None within this refactor's six-phase scope.

## Original cases and dispositions

### `tests/integration/test_cli_posix_streams.py`

**Contract migration.** Use the current structured-relation diagnostic suggestion; preserve JSON and stream assertions.

- [x] `test_validate_json_reports_malformed_transition_without_silent_data_loss`

### `tests/integration/test_release_sizing.py`

**Acceptance drift, closed.** Correct reference labels, measured task text and relation callouts were inspected before accepting the updated public-CLI golden (D-001/D-002).

- [x] `test_book_golden_matches_public_cli_geometry_pipeline`

### `tests/policy/test_ci_hygiene.py`

**Environment isolation.** Offline uv probe passed with required permission; give the test its own writable temporary cache so it is hermetic.

- [x] `test_locked_ci_environment_rejects_manifest_drift_without_changing_lock`

### `tests/unit/render/test_publication.py`

**Contract migration, closed.** All four named failures now pass with first-class
measurement profiles. Their footer totals, zero/missing-category, alternative
path range, unavailable-total and diagnostic-note assertions are unchanged.
Fixtures pass IR validation; decision outcomes are explicit. The existing
partial-projection test also uses real timing evidence and now checks a complete
projection produces a footer before asserting the partial projection omits it.
The existing consumer works with the canonical data; no production changes or
new test cases were needed. Full module: 23 passed. Full suite: 52 failed,
1908 passed; exactly these four existing failures closed, with no new failures.

- [x] `test_build_sppm_publication_plan_uses_typed_timing_analysis_for_footer`
- [x] `test_build_sppm_publication_footer_marks_missing_categories_and_keeps_zero`
- [x] `test_build_sppm_publication_plan_reports_alternative_lead_time_range`
- [x] `test_build_sppm_publication_plan_marks_unavailable_lead_time_and_diagnostics`

### `tests/unit/test_cli_error_observability.py`

**Contract migration.** Replace retired source annotations so the fixture reaches the render-intent rule it is meant to exercise; retain stage assertions.

- [x] `test_execute_emits_render_intent_validation_stage_from_real_pipeline`

### `tests/unit/test_compiler_and_render.py`

**Contract migration.** Replace retired metadata/Boolean rework and obsolete diagnostic expectations; preserve book waiting independence and rework behavior.

- [x] `test_compile_rejects_transition_fields_that_would_be_discarded[metadata: discarded-E0210]`
- [x] `test_compile_and_render_examples` — include provenance defect fixed
- [x] `test_book_washnfold_preserves_independent_waits_and_renders_decision_rework`
- [x] `test_compile_and_render_preserves_rework_outcome_semantics`

### `tests/unit/test_conformance_examples.py`

**Fixture defect.** The invalid fixtures had lost their violation; restored unsupported metadata/capacity, invalid Boolean handoff, and invalid rework frequency.

- [x] `test_conformance_invalid_examples_fail_validation[example_file1]`
- [x] `test_conformance_invalid_examples_fail_validation[example_file5]`
- [x] `test_conformance_invalid_examples_fail_validation[example_file8]`
- [x] `test_conformance_invalid_examples_fail_validation[example_file21]`
- [x] `test_invalid_conformance_examples_fail_public_api[example_file1]`
- [x] `test_invalid_conformance_examples_fail_public_api[example_file5]`
- [x] `test_invalid_conformance_examples_fail_public_api[example_file8]`
- [x] `test_invalid_conformance_examples_fail_public_api[example_file21]`

### `tests/unit/test_duration_units.py`

**Contract migration, closed.** The five display fixtures now supply canonical
profiles with named primary results. Original expected conversions and
non-mutation assertions are unchanged. Adjacent invalid-duration accessor
checks also use profiles, so they test invalid selected values rather than
vacuously rejecting retired scalar shapes. Primitive conversion records use
current method/value/unit fields. No production changes or added cases were
needed. The focused unit/display suites pass 101 cases; full suite: 47 failed,
1913 passed, with exactly these five existing failures closed.

- [x] `test_wait_display_normalizes_without_changing_authored_units[30-s-0.5]`
- [x] `test_wait_display_normalizes_without_changing_authored_units[2-m-2]`
- [x] `test_wait_display_normalizes_without_changing_authored_units[2-min-2]`
- [x] `test_wait_display_normalizes_without_changing_authored_units[0.5-hr-30]`
- [x] `test_wait_display_normalizes_without_changing_authored_units[0.25-d-360]`

### `tests/unit/test_export_registry.py`

**Contract migration, closed for the three movement cases.** Fixtures now use
first-class `location`, `consumes`, `produces`, and `performed_by`, with explicit
item/resource/location collections. Complete boundary edges make all three
fixtures valid IR. Original material/people route and entity assertions are
unchanged, and the spatial case also verifies its 5-metre route distance.
The existing exporter and movement inference work with canonical inputs; no
production changes or added cases were needed. Focused suites: 30 passed.
Full suite: 44 failed, 1916 passed; exactly these three existing failures closed.

- [x] `test_export_ir_movement_mode_outputs_inferred_route_summary`
- [x] `test_export_ir_movement_mode_includes_people_movement_section`
- [x] `test_export_ir_movement_mode_prefers_canonical_relations`

### `tests/unit/test_ir_models_serialization.py`

**Contract migration, closed for this file.** Structured relations and extensions round-trip; retired edge_type/Boolean/metadata assertions were migrated without runtime aliases. Invalid relation preservation is explicit.

- [x] `test_ir_edge_optional_fields_roundtrip`
- [x] `test_ir_from_internal_dict_preserves_edge_type_and_rework` — migrated to `test_ir_from_internal_dict_preserves_structured_rework`
- [x] `test_ir_normalizes_non_object_attrs_and_metadata_at_construction` — migrated to `test_ir_preserves_invalid_relation_while_legacy_context_normalization_remains`

### `tests/unit/test_json_export_branches.py`

**Contract migration.** Migrate exchange assertions to first-class relations, typed collections, and extensions. Resolve the obsolete node-note expectation against the accepted description/extension boundary.

- [x] `test_edge_to_schema_omits_none_and_non_dict_metadata` — migrated to `test_edge_to_schema_omits_absent_optional_fields`
- [x] `test_node_note_is_exported_when_present`
- [x] `test_node_inputs_and_outputs_are_exported_when_present`
- [x] `test_node_location_workers_and_equipment_are_exported_when_present`
- [x] `test_node_canonical_relations_are_exported_when_present`
- [x] `test_edge_handoff_is_exported_when_present`
- [x] `test_process_metadata_is_exported_when_present` — migrated to `test_process_evidence_and_entities_are_exported_when_present`
- [x] `test_grouped_materials_are_exported_when_present` — migrated to `test_item_group_annotations_are_exported_as_extensions`

### `tests/unit/test_layout_core_elk_requests.py`

**Contract migration.** Supply structured rework and profile evidence; retain port, partition, callout, and routing assertions. Investigate any remaining consumer loss after migration.

- [x] `test_build_sppm_elk_layout_request_flattens_synthetic_rows_into_partitions`
- [x] `test_build_sppm_elk_layout_request_preserves_rework_callout_content`
- [x] `test_build_sppm_request_derives_branch_route_for_explicit_rework_return`
- [x] `test_serialize_sppm_rework_labels_do_not_participate_in_routing`
- [x] `test_serialize_sppm_elk_layout_request_emits_cardinal_ports_and_port_attached_edges`
- [x] `test_serialize_sppm_return_rework_edge_targets_south_port`
- [x] `test_build_sppm_synthetic_rows_reverse_ports_when_rework_returns_earlier`
- [x] `test_build_sppm_synthetic_rows_align_rework_partition_with_branch_decision`
- [x] `test_build_sppm_synthetic_rows_anchor_return_source_to_reintegration_target`

### `tests/unit/test_layout_core_elk_runtime.py`

**Contract migration.** Migrate fixture rework and canonical node fields while preserving normalized geometry and semantic assertions.

- [x] `test_normalize_elk_layout_result_preserves_rework_edge_semantics`
- [x] `test_normalize_elk_layout_result_balances_mainline_queue_to_task_gaps`
- [x] `test_normalize_elk_layout_result_equalizes_mainline_horizontal_gaps`
- [x] `test_build_sppm_elk_layout_request_distinguishes_rework_return_edges`

### `tests/unit/test_layout_core_graph_projection.py`

**Contract migration.** Use first-class attributes and structured relations on object/graph inputs and expected projections; preserve hierarchy collapse.

- [x] `test_extract_nodes_and_edges_from_ir_object_preserves_attrs_and_lists`
- [x] `test_extract_nodes_and_edges_from_adapter_dict_with_transitions_and_synthesized_edges`
- [x] `test_project_parent_only_subprocess_view_collapses_hidden_edges_and_semantics`

### `tests/unit/test_public_api.py`

**Contract migration.** Replace removed alias-conflict E0219 expectation with stable unsupported-field diagnostic and preserve public failure delivery.

- [x] `test_public_api_returns_typed_diagnostics_instead_of_raising`

### `tests/unit/test_render_artifact_backends_spaghetti.py`

**Implementation defect.** Compiler rejected parser-owned include provenance. Remove provenance only from a compiler-owned copy before authored-shape validation.

- [x] `test_reference_spaghetti_svg_artifact_is_deterministic`

### `tests/unit/test_render_artifact_backends_value_stream.py`

**Contract migration.** Migrate measurement fixture and preserve missing-metric disclosure; investigate any consumer failure after fixture repair.

- [x] `test_value_stream_svg_discloses_missing_optional_metrics`

### `tests/unit/test_render_themes.py`

**Contract migration.** Migrate canonical classification/relations feeding the theme specimen, then verify semantic theme signatures.

- [x] `test_configured_theme_cross_renderer_golden`

### `tests/unit/test_scaffold.py`

**Implementation defect.** Built-in scaffold still emitted retired Boolean relation fields; now emits structured handoff/rework.

- [x] `test_templates_compile_to_valid_models[handoff]`
- [x] `test_templates_compile_to_valid_models[rework]`

### `tests/unit/test_source_diagnostics.py`

**Contract migration.** Replace suggestion to use Boolean relations with the structured-relation instruction.

- [x] `test_compile_diagnostic_points_to_transition_field_and_suggests_fix`

### `tests/unit/test_sppm_layout_invariants.py`

**Implementation verification.** Includes were rejected by compiler; the remaining White Belt row/corridor expectation requires geometry investigation, not a relaxed assertion.

- [x] `test_sppm_corpus_layout_invariants_hold[cookies_process_lr]` — include provenance defect fixed
- [x] `test_white_belt_wrap_has_clear_rows_and_boundary_corridors`

### `tests/unit/test_svg_sppm_nodes.py`

**Contract migration.** Use first-class profiles/classification/performer fields. Resolve retired note expectations against description/extensions; preserve measured-zero and palette assertions.

- [x] `test_node_svg_task_includes_info_lines_and_note` — migrated to `test_node_svg_task_includes_info_lines_and_description`
- [x] `test_node_svg_task_displays_declared_changeover_as_setup_time`
- [x] `test_node_svg_queue_renders_wait_time_line`
- [x] `test_node_svg_queue_distinguishes_missing_and_zero_wait_time`
- [x] `test_node_svg_uses_mpi_lms_semantic_roles[task-metadata0-#0B5D5A-#CDD5D5-#FFFFFF]`
- [x] `test_node_svg_uses_mpi_lms_semantic_roles[task-metadata1-#8A5A00-#CDD5D5-#FFFFFF]`
- [x] `test_node_svg_uses_mpi_lms_semantic_roles[task-metadata2-#A43232-#CDD5D5-#FFFFFF]`

### `tests/unit/test_validate_errors.py`

**Contract migration.** D-003 closes the four canonical measurement/list rejection cases below. The classification fixtures now exercise first-class fields; unsupported process classification is rejected at the source boundary.

- [x] `test_validate_ir_rejects_invalid_node_time_unit`
- [x] `test_validate_ir_rejects_non_object_node_time_metadata_value`
- [x] `test_validate_ir_rejects_non_list_node_inputs`
- [x] `test_validate_ir_rejects_empty_string_node_output_item`
- [x] `test_validate_ir_rejects_invalid_value_class`
- [x] `test_validate_ir_rejects_value_class_on_control_nodes[start]`
- [x] `test_validate_ir_rejects_value_class_on_control_nodes[end]`
- [x] `test_validate_ir_rejects_process_value_class`

### `tests/unit/test_validate_errors_relations_parallel.py`

**Contract migration, closed for this file.** Fixtures now use canonical relation fields and explicit item/resource collections. Invalid handoff shapes survive construction and fail explicit validation (D-003).

- [x] `test_validate_ir_rejects_consumes_with_undeclared_item`
- [x] `test_validate_ir_rejects_non_boolean_handoff` — migrated to `test_validate_ir_rejects_non_object_handoff`
- [x] `test_validate_ir_rejects_resource_relations_with_unknown_resource`
- [x] `test_validate_ir_rejects_resource_relations_with_wrong_kind`

### `tests/unit/test_validate_errors_rework.py`

**Contract migration, closed for this file.** Structured frequency/reason constraints are tested. Retired duplicate edge_type/Boolean declarations fail at construction; invalid structured relations fail domain validation.

- [x] `test_validate_ir_accepts_valid_rework_edge_metadata`
- [x] `test_validate_ir_rejects_invalid_rework_rate`
- [x] `test_validate_ir_rejects_blank_rework_reason`
- [x] `test_validate_ir_rejects_conflicting_rework_declarations[rework-False]` — retired duplicate flags rejected at construction
- [x] `test_validate_ir_rejects_conflicting_rework_declarations[sequence-True]` — retired duplicate flags rejected at construction

### `tests/unit/test_validate_subprocess.py`

**Contract migration, closed.** Detail-map fixtures use the existing extensions boundary; blank references retain E1333 rejection and valid references reach rendering.

- [x] `test_validate_ir_rejects_blank_subprocess_detail_map_reference`

