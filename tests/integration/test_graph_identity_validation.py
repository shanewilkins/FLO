"""Duplicate graph identities stop every validated source/canonical consumer."""

import json
from copy import deepcopy

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.process.ir._internal_shape import ir_from_internal_dict, ir_to_internal_dict
from flo.source import compile_adapter


def model():
    return {
        "spec_version": "0.1",
        "process": {"id": "identity", "name": "Identity"},
        "steps": [
            {"id": "s", "kind": "start"},
            {"id": "work", "kind": "task", "lane": "lane"},
            {"id": "e", "kind": "end"},
        ],
        "transitions": [
            {"source": "s", "target": "work"},
            {"source": "work", "target": "e"},
        ],
        "lanes": [{"id": "lane", "name": "Lane"}],
    }


def invalidate(document, case, *, canonical=False):
    edges = document["edges" if canonical else "transitions"]
    if case == "record":
        edges.append(deepcopy(edges[0]))
    elif case == "edge_id":
        edges[0]["id"] = edges[1]["id"] = "same"
    else:
        document["lanes"].append({"id": "lane", "name": "Different name"})


CASES = [("record", "E1033"), ("edge_id", "E1034"), ("lane_id", "E1035")]


@pytest.mark.parametrize("case,code", CASES)
@pytest.mark.parametrize("canonical", [False, True], ids=["source", "canonical"])
def test_graph_identity_errors_stop_api_and_cli_consumers(
    case, code, canonical, monkeypatch, tmp_path
):
    document = model()
    if canonical:
        payload = ir_to_internal_dict(compile_adapter(document))
        invalidate(payload, case, canonical=True)
        monkeypatch.setattr(
            "flo.app.compile_adapter",
            lambda _source: ir_from_internal_dict(deepcopy(payload)),
        )
    else:
        invalidate(document, case)
    calls = []

    def forbidden_consumer(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Invalid graph reached consumer")

    for target in (
        "flo.api.inspect_process_model",
        "flo.api.export_ir",
        "flo.app._run_inspect_output",
        "flo.app._run_export_output",
        "flo.app._run_render_output",
        "flo.app.timing_diagnostic_report",
        "flo.api.timing_diagnostic_report",
    ):
        monkeypatch.setattr(target, forbidden_consumer)
    source = yaml.safe_dump(document, sort_keys=False)
    expected = api.validate(source, source_path="-").report
    assert expected.error_count == 1
    diagnostic = expected.diagnostics[0]
    assert diagnostic.code == code
    assert (
        diagnostic.field_path
        == {
            "record": "edges[2]" if canonical else "transitions[2]",
            "edge_id": "edges[1].id" if canonical else "transitions[1].id",
            "lane_id": "lanes[1].id",
        }[case]
    )
    if canonical:
        assert diagnostic.line is None and diagnostic.column is None
    else:
        assert diagnostic.line is not None and diagnostic.column is not None
    for operation in (api.validate, api.inspect, api.export):
        result = operation(source, source_path="-")
        assert not result.ok and result.value is None
        assert result.report == expected
    output = tmp_path / "invalid.svg"
    for command in ("validate", "inspect", "export", "render"):
        args = [command, "-", "--diagnostics-format", "json"]
        if command == "inspect":
            args += ["--format", "json"]
        if command == "render":
            args += ["--render-to", str(output)]
        result = CliRunner().invoke(cli, args, input=source)
        assert result.exit_code == (3 if case == "lane_id" and not canonical else 4)
        assert result.stdout == ""
        assert json.loads(result.stderr) == json.loads(json.dumps(expected.as_dict()))
    assert not output.exists() and calls == []


@pytest.mark.parametrize("case,code", CASES)
def test_duplicates_across_includes_point_to_second_authored_declaration(
    case, code, tmp_path
):
    root = model()
    fragment = {}
    if case == "lane_id":
        fragment["lanes"] = [{"id": "lane", "name": "Included lane"}]
        expected_path = "lanes[0].id"
    elif case == "record":
        fragment["transitions"] = [deepcopy(root["transitions"][0])]
        expected_path = "transitions[0]"
    else:
        root["transitions"][0]["id"] = "same"
        fragment["transitions"] = [{"source": "work", "target": "e", "id": "same"}]
        expected_path = "transitions[0].id"
    root["includes"] = ["fragment.flo"]
    (tmp_path / "fragment.flo").write_text(yaml.safe_dump(fragment, sort_keys=False))
    source = yaml.safe_dump(root, sort_keys=False)
    result = api.validate(source, source_path=str(tmp_path / "root.flo"))
    assert not result.ok
    diagnostic = result.report.diagnostics[0]
    assert diagnostic.code == code
    # Included entries precede local entries: report the local duplicate.
    assert diagnostic.source == str(tmp_path / "root.flo")
    assert diagnostic.field_path == expected_path
    assert diagnostic.line is not None


def test_duplicate_named_target_ids_point_to_nested_authored_field():
    document = model()
    document.pop("transitions")
    document["steps"] = [
        {"id": "s", "kind": "start"},
        {
            "id": "gate",
            "kind": "decision",
            "outcomes": {
                "yes": {"target": "e", "id": "same"},
                "no": {"target": "e", "id": "same"},
            },
        },
        {"id": "e", "kind": "end"},
    ]
    source = yaml.safe_dump(document, sort_keys=False)
    result = api.validate(source)
    assert not result.ok
    diagnostic = result.report.diagnostics[0]
    assert diagnostic.code == "E1034"
    assert diagnostic.field_path == "steps[1].outcomes.no.id"
    assert (
        diagnostic.line
        == [
            index + 1
            for index, line in enumerate(source.splitlines())
            if line == "      id: same"
        ][-1]
    )


@pytest.mark.parametrize("case,code", CASES)
def test_duplicate_in_later_include_keeps_original_file_and_location(
    case, code, tmp_path
):
    document = model()
    if case == "lane_id":
        first = {"lanes": document.pop("lanes")}
        second = {"lanes": [{"id": "lane", "name": "Other lane"}]}
        field = "lanes[0].id"
    else:
        edges = document.pop("transitions")
        if case == "edge_id":
            edges[0]["id"] = edges[1]["id"] = "same"
            first = {"transitions": [edges[0]]}
            second = {"transitions": [edges[1]]}
            field = "transitions[0].id"
        else:
            first = {"transitions": edges}
            second = {"transitions": [deepcopy(edges[0])]}
            field = "transitions[0]"
    for name, content in (("first.flo", first), ("second.flo", second)):
        (tmp_path / name).write_text(yaml.safe_dump(content, sort_keys=False))
    document["includes"] = ["first.flo", "second.flo"]
    source = yaml.safe_dump(document, sort_keys=False)
    result = api.validate(source, source_path=str(tmp_path / "root.flo"))
    assert not result.ok
    diagnostic = result.report.diagnostics[0]
    assert diagnostic.code == code and diagnostic.field_path == field
    assert diagnostic.source == str(tmp_path / "second.flo")
    assert diagnostic.line is not None
    assert any("second.flo" in entry for entry in diagnostic.include_chain)


def test_direct_source_compilation_rejects_duplicate_lanes_with_specific_path():
    from flo.source.models import SourceShapeError

    document = model()
    invalidate(document, "lane_id")
    with pytest.raises(SourceShapeError, match="E1035") as error:
        compile_adapter(document)
    assert error.value.location == ("lanes", 1, "id")
