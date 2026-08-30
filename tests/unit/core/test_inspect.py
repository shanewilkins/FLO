from __future__ import annotations

import json
from pathlib import Path

import pytest

from flo.app import run_content
from flo.errors import CLIError, EXIT_USAGE, ValidationError


WASHNFOLD = Path(__file__).parents[3] / "examples" / "reference" / "washnfold.flo"


def test_inspect_timing_text_reports_washnfold_totals() -> None:
    rc, out, err = run_content(
        WASHNFOLD.read_text(encoding="utf-8"),
        command="inspect",
        options={"analysis": "timing", "format": "text"},
    )

    assert rc == 0
    assert err == ""
    assert out == (
        "Process: Wash n' Fold (wash_n_fold)\n"
        "Version: 1\n"
        "Timing coverage: complete\n"
        "\n"
        "Declared totals:\n"
        "  Cycle time: 105 min\n"
        "  Wait time: 95 min\n"
        "  Changeover time: 0 min\n"
        "  Elapsed subtotal: 200 min\n"
        "\n"
        "Modeled lead time: 200 min\n"
        "Paths analyzed: 1\n"
        "Changeover policy: one declared changeover per visited step\n"
    )


def test_inspect_timing_json_is_stable_and_machine_readable() -> None:
    content = WASHNFOLD.read_text(encoding="utf-8")

    first = run_content(
        content,
        command="inspect",
        options={"analysis": "timing", "format": "json"},
    )
    second = run_content(
        content,
        command="inspect",
        options={"analysis": "timing", "format": "json"},
    )

    assert first == second
    rc, out, err = first
    assert rc == 0
    assert err == ""
    assert out.endswith("\n")
    payload = json.loads(out)
    assert payload["analysis_version"] == "0.1"
    assert payload["process"] == {
        "id": "wash_n_fold",
        "name": "Wash n' Fold",
        "version": 1,
    }
    assert payload["declared_totals"] == {
        "changeover_time_seconds": 0.0,
        "cycle_time_seconds": 6300.0,
        "elapsed_time_seconds": 12000.0,
        "wait_time_seconds": 5700.0,
    }
    assert payload["modeled_lead_time_seconds"] == 12000.0


def test_inspect_structure_json_is_stable_and_machine_readable() -> None:
    content = WASHNFOLD.read_text(encoding="utf-8")

    first = run_content(
        content,
        command="inspect",
        options={"analysis": "structure", "format": "json"},
    )
    second = run_content(
        content,
        command="inspect",
        options={"analysis": "structure", "format": "json"},
    )

    assert first == second
    rc, out, err = first
    assert rc == 0
    assert err == ""
    assert out.endswith("\n")
    payload = json.loads(out)
    assert payload["analysis_version"] == "0.1"
    assert payload["process"]["id"] == "wash_n_fold"
    assert payload["path_summary"] == {
        "maximum_edge_count": 13,
        "minimum_edge_count": 13,
        "path_count": 1,
    }
    assert payload["step_classification"]["node_type_counts"] == {
        "end": 1,
        "queue": 5,
        "start": 1,
        "task": 7,
    }


def test_inspect_structure_text_reports_summary() -> None:
    rc, out, err = run_content(
        WASHNFOLD.read_text(encoding="utf-8"),
        command="inspect",
        options={"analysis": "structure", "format": "text"},
    )

    assert rc == 0
    assert err == ""
    assert "Structural summary:\n" in out
    assert "  Non-rework paths: 1\n" in out
    assert "  Path length (edges): 13\n" in out
    assert "Step classification:\n" in out


def test_inspect_model_json_reports_summary_and_requested_readiness() -> None:
    options = {
        "analysis": "model",
        "format": "json",
        "for_analysis": "timing",
        "for_diagram": "spaghetti",
    }
    first = run_content(
        WASHNFOLD.read_text(encoding="utf-8"),
        command="inspect",
        options=options,
    )
    second = run_content(
        WASHNFOLD.read_text(encoding="utf-8"),
        command="inspect",
        options=options,
    )

    assert first == second
    rc, out, err = first
    assert rc == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["report_version"] == "0.1"
    assert payload["composition"]["entry_source"] == "<memory>"
    assert payload["model_summary"]["node_count"] == 14
    assert payload["paths"]["count"] == 1
    assert payload["views"][0]["view_id"] == "default"
    assert payload["readiness"][0] == {
        "target_type": "analysis",
        "target": "timing",
        "status": "ready",
        "findings": [],
    }
    assert payload["readiness"][1]["target"] == "spaghetti"
    assert payload["readiness"][1]["status"] == "unavailable"


def test_inspect_model_text_is_concise() -> None:
    rc, out, err = run_content(
        WASHNFOLD.read_text(encoding="utf-8"),
        command="inspect",
        options={"analysis": "model", "format": "text"},
    )

    assert rc == 0
    assert err == ""
    assert "Validation: valid\n" in out
    assert "Composition:\n  Entry source: <memory>\n" in out
    assert "Model summary:\n  Nodes: 14\n" in out
    assert "Views: default\n" in out


def test_inspect_model_does_not_turn_invalid_input_into_readiness() -> None:
    invalid = """
spec_version: "0.1"
process:
  id: invalid
  name: Invalid
steps:
  - id: start
    kind: start
"""

    with pytest.raises(ValidationError):
        run_content(
            invalid,
            command="inspect",
            options={"analysis": "model", "format": "json"},
        )


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"analysis": "capacity"}, "Unsupported inspect analysis: capacity"),
        ({"format": "yaml"}, "Unsupported inspect format: yaml"),
        (
            {"analysis": "timing", "for_diagram": "sppm"},
            "--for-analysis and --for-diagram require --analysis model",
        ),
        (
            {"analysis": "model", "for_analysis": "capacity"},
            "Unsupported readiness analysis: capacity",
        ),
    ],
)
def test_inspect_rejects_unsupported_programmatic_options(
    options: dict[str, str], message: str
) -> None:
    with pytest.raises(CLIError) as caught:
        run_content(
            WASHNFOLD.read_text(encoding="utf-8"),
            command="inspect",
            options=options,
        )

    assert caught.value.code == EXIT_USAGE
    assert caught.value.error_stage == "option_validation"
    assert str(caught.value) == message
