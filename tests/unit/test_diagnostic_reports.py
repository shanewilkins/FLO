"""Common reports preserve producer evidence and deterministic delivery identity."""

import json
from dataclasses import replace

from flo import OperationResult
from flo.diagnostics import Diagnostic, adapt_diagnostic, diagnostic_report
from flo.process.analysis.structure import StructuralDiagnostic
from flo.render import RenderArtifact
from flo.render.diagnostics import (
    artifact_diagnostic_report,
    attach_operation_diagnostics,
)
from flo.source.diagnostics import SourceDiagnostic


def test_equivalent_findings_deduplicate_across_delivery_stages_in_any_order():
    first = Diagnostic(
        "timing-incomplete",
        "warning",
        "Missing timing",
        "analysis.timing",
        details={"node_id": "work"},
    )
    duplicate = replace(first, stage="render")
    other = replace(first, details={"node_id": "other"})
    forward = diagnostic_report((first, duplicate, other))
    reverse = diagnostic_report((other, duplicate, first))

    assert forward.as_dict() == reverse.as_dict()
    assert forward.warning_count == 2
    assert forward.error_count == 0
    assert all(item.stage == "analysis.timing" for item in forward.diagnostics)


def test_source_adapter_preserves_location_suggestion_chain_and_rendering():
    source = SourceDiagnostic(
        "E0209",
        "error",
        "bad rework",
        "test.flo",
        7,
        5,
        "    rework: 'yes'",
        "transitions[0].rework",
        "Use a boolean.",
        ("root.flo", "part.flo"),
    )
    record = adapt_diagnostic(source, stage="compile")
    assert record.render() == source.render()
    assert record.include_chain == source.include_chain
    assert record.suggestion == source.suggestion
    assert record.field_path == source.field_path
    assert record.stage == "compile"


def test_structural_adapter_retains_edge_context():
    original = StructuralDiagnostic(
        "structure-unmarked-lane-change",
        "warning",
        "Lane change",
        source_id="a",
        target_id="b",
    )
    record = adapt_diagnostic(original, stage="analysis.structure")
    assert record.details == {"node_id": None, "source_id": "a", "target_id": "b"}


def test_warning_and_info_only_results_remain_successful():
    warning = Diagnostic(
        "timing-incomplete", "warning", "Missing timing", "analysis.timing"
    )
    info = replace(warning, code="timing-multiple-paths", severity="info")
    assert OperationResult(value=0, diagnostics=(warning, info)).ok
    assert not OperationResult(
        value=0, diagnostics=(replace(warning, severity="error"),)
    ).ok
    assert not OperationResult(value=None, diagnostics=(warning,)).ok
    report = diagnostic_report((info, warning))
    assert report.as_dict()["info_count"] == 1
    assert "timing-multiple-paths" not in report.text()
    assert "timing-multiple-paths" in report.text(include_info=True)


def test_legacy_source_result_constructor_still_has_a_common_report():
    source = SourceDiagnostic(None, "warning", "Warning", None, None, None, None)
    result = OperationResult(value="ok", diagnostics=(source,))
    assert result.ok
    assert result.report.warning_count == 1


def test_render_adapter_preserves_native_metadata_and_avoids_summary_duplicates():
    native = {
        "code": "elk-edge-missing",
        "severity": "warning",
        "message": "Missing edge",
        "source_id": "a",
        "target_id": "b",
    }
    original = {"warning_count": 1, "partial_output": True}
    artifact = RenderArtifact(
        "svg",
        "<svg />",
        "svg",
        {
            "render_diagnostics": [native],
            "render_diagnostics_report": original,
            "warning": "elk-edge-missing: Missing edge",
        },
    )
    report = artifact_diagnostic_report(artifact, diagram="sppm")
    assert report.warning_count == 1
    record = report.diagnostics[0]
    assert record.details["source_id"] == "a"
    assert record.details["target_id"] == "b"
    assert record.details["diagram"] == "sppm"
    assert record.details["render_report"]["partial_output"] is True
    record.details["render_report"]["partial_output"] = False
    assert original["partial_output"] is True
    attached = attach_operation_diagnostics(artifact, object(), diagram="sppm")
    assert attached.content == artifact.content
    assert attached.metadata["warning"] == artifact.metadata["warning"]
    assert attached.diagnostic_report.warning_count == 1
    assert json.dumps(attached.diagnostic_report.as_dict(), sort_keys=True)
