"""Evidence for contract prerequisites, independent of downstream fixture migration."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from flo import api
from flo.process.contracts import CanonicalProcessContract, MeasurementResult
from flo.source.models import SourceDocument, SourceShapeError, validate_source_shape
from scripts import generate_contract_schemas


def _source():
    return {
        "spec_version": "0.1",
        "process": {"id": "example", "name": "Example"},
        "steps": [{"id": "start", "kind": "start"}, {"id": "end", "kind": "end"}],
    }


@pytest.mark.parametrize(
    "method", ["mean", "count", "percentile", "lss4py:trimmed_mean"]
)
def test_methods_are_core_or_namespaced(method):
    result = {"method": method, "value": 1, "unit": "min"}
    if method == "percentile":
        result["parameters"] = {"percentile": 95}
    assert MeasurementResult.model_validate(result).method == method


@pytest.mark.parametrize("method", ["trimmed_mean", "P95", "", "x:", ":mean", "x:y:z"])
def test_unrecognized_or_malformed_method_names_are_rejected(method):
    with pytest.raises(ValidationError):
        MeasurementResult.model_validate({"method": method, "value": 1, "unit": "min"})


@pytest.mark.parametrize(
    "collection,entry",
    [
        ("items", {"id": "a", "name": "A", "kind": "material"}),
        ("resources", {"id": "a", "name": "A", "kind": "person"}),
        (
            "locations",
            {
                "id": "a",
                "name": "A",
                "metadata": {"spatial": {"x": 0, "y": 1, "unit": "m"}},
            },
        ),
    ],
)
def test_canonical_collections_are_typed_at_every_group_depth(collection, entry):
    value = {
        "id": "p",
        "name": "P",
        collection: {"group": {"name": "Group", "entries": [entry]}},
    }
    before = deepcopy(value)
    CanonicalProcessContract.model_validate(value)
    assert value == before
    invalid = deepcopy(value)
    invalid[collection]["group"]["entries"][0]["unsupported"] = True
    with pytest.raises(ValidationError):
        CanonicalProcessContract.model_validate(invalid)
    invalid = deepcopy(value)
    invalid[collection]["group"]["entries"][0]["quantity"] = {
        "kind": "count",
        "value": True,
    }
    with pytest.raises(ValidationError):
        CanonicalProcessContract.model_validate(invalid)


@pytest.mark.parametrize(
    "patch,code,path",
    [
        ({"unsupported": True}, "E0220", "unsupported"),
        ({"process": {"id": "p"}}, "E0221", "process.name"),
        ({"process": {"id": 3, "name": "P"}}, "E0222", "process.id"),
        ({"steps": []}, "E0222", "steps"),
        ({"steps": [{"id": "n", "kind": "unsupported"}]}, "E0222", "steps[0].kind"),
        ({"transitions": None}, "E0222", "transitions"),
    ],
)
def test_model_error_categories_have_stable_flo_diagnostics(patch, code, path):
    source = _source() | patch
    result = api.validate(
        yaml.safe_dump(source, sort_keys=False), source_path="probe.flo"
    )
    diagnostic = result.diagnostics[0]
    assert not result.ok
    assert diagnostic.code == code
    assert diagnostic.field_path == path
    assert diagnostic.line is not None
    assert "pydantic" not in diagnostic.message.lower()
    assert "input_value" not in diagnostic.message


def test_nested_measurement_error_retains_authored_path_without_union_markers():
    source = _source()
    source["steps"].insert(
        1,
        {
            "id": "work",
            "kind": "task",
            "cycle_time": {
                "basis": "observed",
                "primary": "mean",
                "results": {"mean": {"method": "mean", "value": -1, "unit": "min"}},
            },
        },
    )
    with pytest.raises(SourceShapeError) as error:
        validate_source_shape(SourceDocument, source)
    assert error.value.location[:5] == ("steps", 1, "cycle_time", "results", "mean")
    assert "MeasurementProfile" not in str(error.value)
    assert "function-after" not in str(error.value)


def test_schema_check_detects_missing_and_stale_artifacts_without_writing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(generate_contract_schemas, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["generate_contract_schemas.py", "--check"])
    with pytest.raises(SystemExit) as error:
        generate_contract_schemas.main()
    assert error.value.code == 1
    assert list(tmp_path.iterdir()) == []
    monkeypatch.setattr("sys.argv", ["generate_contract_schemas.py"])
    generate_contract_schemas.main()
    paths = list(generate_contract_schemas.generated_schemas())
    paths[0].write_text("{}\n")
    before = {path: path.read_bytes() for path in paths}
    monkeypatch.setattr("sys.argv", ["generate_contract_schemas.py", "--check"])
    with pytest.raises(SystemExit) as error:
        generate_contract_schemas.main()
    assert error.value.code == 1
    assert {path: path.read_bytes() for path in paths} == before


def test_repository_schemas_match_models():
    for path, expected in generate_contract_schemas.generated_schemas().items():
        assert path.read_text() == expected
        json.loads(expected)


def test_ci_and_publication_enforce_schema_drift():
    root = Path(__file__).resolve().parents[3]
    hooks = yaml.safe_load((root / ".pre-commit-config.yaml").read_text())
    hook = next(
        hook
        for repo in hooks["repos"]
        for hook in repo["hooks"]
        if hook["id"] == "contract-schema-check"
    )
    assert (
        hook["entry"]
        == "uv run --locked python scripts/generate_contract_schemas.py --check"
    )
    for filename in ("ci.yml", "publish.yml"):
        workflow = yaml.safe_load((root / ".github/workflows" / filename).read_text())
        assert any(
            "pre-commit run --all-files" in step.get("run", "")
            for job in workflow["jobs"].values()
            for step in job["steps"]
        )


def test_book_fixture_retains_population_statistics_and_evidence_through_exchange():
    root = Path(__file__).resolve().parents[3]
    path = root / "examples/reference/book_washnfold.flo"
    content = path.read_text()
    source = yaml.safe_load(content)
    result = api.export(content, source_path=str(path))
    assert result.ok, result.diagnostics
    exported = {node["id"]: node for node in json.loads(result.value)["nodes"]}
    expected_counts = {
        "wash": (65, "load"),
        "dry": (65, "load"),
        "fold_correction": (5, "order"),
    }
    for step in source["steps"]:
        for field in ("cycle_time", "wait_time", "changeover_time"):
            measurement = step.get(field)
            if measurement is None:
                continue
            assert exported[step["id"]][field] == measurement
            if "ref" in measurement:
                continue
            count, unit = expected_counts.get(step["id"], (39, "order"))
            assert (
                measurement["observation_count"],
                measurement["observation_unit"],
            ) == (count, unit)
            assert measurement["basis"] == "simulated"
            assert measurement["cohort"] == "Friday 91"
            assert measurement["observation_window"] == "Representative Friday"
            assert measurement["evidence_ref"].startswith("book:")
    assert (
        exported["wash_release_queue"]["wait_time"]["results"]["mean"]["value"] == 501.7
    )
    assert exported["wash"]["wait_time"]["results"]["mean"]["value"] == 500.9
    assert exported["notification_queue"]["wait_time"] == {
        "ref": "stage_collection.wait_time"
    }
    assert exported["correction_queue"]["wait_time"] == {
        "ref": "fold_correction.wait_time"
    }
    assert exported["dropoff"]["changeover_time"]["results"]["mean"]["value"] == 0
    assert {"stage_collection", "send_notification"} <= exported.keys()
    assert "stage_notify" not in exported
