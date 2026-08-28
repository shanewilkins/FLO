from __future__ import annotations

import json
from pathlib import Path

import pytest

from flo.core import run_content
from flo.services.errors import CLIError, EXIT_USAGE


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


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"analysis": "capacity"}, "Unsupported inspect analysis: capacity"),
        ({"format": "yaml"}, "Unsupported inspect format: yaml"),
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
