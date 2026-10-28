"""Source composition cannot discard invalid or canonical authored facts."""

import json

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli


def _flow():
    return {
        "spec_version": "0.1",
        "process": {"id": "integrity", "name": "Integrity"},
        "steps": [{"id": "start", "kind": "start"}, {"id": "end", "kind": "end"}],
    }


def _entry(entity_id, collection):
    result = {"id": entity_id, "name": entity_id.title()}
    if collection in {"items", "resources"}:
        result["kind"] = "material" if collection == "items" else "equipment"
    return result


def _put(document, collection, entries, placement):
    target = document
    for key in placement:
        target = target.setdefault(key, {})
    target[collection] = entries


@pytest.mark.parametrize(
    "collection",
    ["items", "resources", "locations"],
)
@pytest.mark.parametrize("placement", [(), ("process",)])
@pytest.mark.parametrize("included_placement", [(), ("process",)])
def test_includes_merge_collections_across_supported_placements(
    tmp_path, collection, placement, included_placement
):
    fragment = {}
    _put(fragment, collection, [_entry("included", collection)], included_placement)
    (tmp_path / "part.flo").write_text(yaml.safe_dump(fragment))
    model = _flow()
    model["includes"] = ["part.flo"]
    _put(model, collection, [_entry("local", collection)], placement)
    result = api.export(yaml.safe_dump(model), source_path=str(tmp_path / "root.flo"))
    if placement == () or included_placement == ():
        assert not result.ok
        assert result.diagnostics[0].code == "E0220"
        assert result.diagnostics[0].field_path == collection
        assert result.diagnostics[0].source.endswith(
            "root.flo" if placement == () else "part.flo"
        )
        return
    assert result.ok, result.diagnostics
    exported = json.loads(result.value)["process"][collection]
    assert [item["id"] for item in exported] == ["included", "local"]


@pytest.mark.parametrize("grouped", [False, True])
@pytest.mark.parametrize("collection", ["items", "resources"])
def test_duplicate_included_entity_ids_are_not_overrides(tmp_path, grouped, collection):
    entries = [_entry("same", collection)]
    fragment = {"process": {collection: {"group": entries} if grouped else entries}}
    (tmp_path / "part.flo").write_text(yaml.safe_dump(fragment))
    model = _flow()
    model["process"].update(fragment["process"])
    model["includes"] = ["part.flo"]
    result = api.validate(yaml.safe_dump(model), source_path=str(tmp_path / "root.flo"))
    assert not result.ok
    assert result.diagnostics[0].code == "E1221"


@pytest.mark.parametrize(
    "patch,field",
    [
        ({"spec_version": "9.9"}, "spec_version"),
        ({"steps": None}, "steps"),
        ({"transitions": None}, "transitions"),
        ({"process": {"metadata": None}}, "process.metadata"),
        ({"materials": {"broken": "not a collection"}}, "materials"),
    ],
)
@pytest.mark.parametrize("invalid_include", [False, True])
def test_invalid_fragment_fields_are_checked_before_merge(
    tmp_path, patch, field, invalid_include
):
    fragment = patch if invalid_include else _flow()
    (tmp_path / "part.flo").write_text(yaml.safe_dump(fragment, sort_keys=False))
    model = {**(_flow() if invalid_include else patch), "includes": ["part.flo"]}
    source = tmp_path / "root.flo"
    content = yaml.safe_dump(model, sort_keys=False)
    result = api.validate(content, source_path=str(source))
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.stage == "compile"
    assert diagnostic.field_path == field
    assert diagnostic.source == str(
        tmp_path / "part.flo" if invalid_include else source
    )
    assert diagnostic.line is not None and diagnostic.excerpt
    assert diagnostic.include_chain
    source.write_text(content)
    command = CliRunner().invoke(
        cli, ["validate", str(source), "--diagnostics-format", "json"]
    )
    assert command.exit_code == 3
    assert json.loads(command.stderr) == json.loads(json.dumps(result.report.as_dict()))


def test_included_quantity_failure_uses_original_file_and_entry_index(tmp_path):
    fragment = {"process": {"items": [_entry("included", "items")]}}
    fragment["process"]["items"][0]["quantity"] = {
        "kind": "measure",
        "value": 250,
        "unit": "g",
        "canonical_value": 99,
        "canonical_unit": "kg",
    }
    included = tmp_path / "part.flo"
    included.write_text(yaml.safe_dump(fragment))
    model = {**_flow(), "includes": ["part.flo"]}
    model["process"]["items"] = [_entry("local", "items")]
    result = api.validate(yaml.safe_dump(model), source_path=str(tmp_path / "root.flo"))
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "E1223"
    assert diagnostic.source == str(included)
    assert diagnostic.field_path == "process.items[0].quantity.canonical_value"
    assert diagnostic.excerpt.strip() == "canonical_value: 99"
    assert diagnostic.include_chain[-1] == str(included)


def test_transitions_merge_before_final_source_validation(tmp_path):
    fragment = {"transitions": [{"source": "start", "target": "work"}]}
    (tmp_path / "part.flo").write_text(yaml.safe_dump(fragment))
    model = _flow()
    model["steps"].insert(1, {"id": "work", "kind": "task"})
    model["includes"] = ["part.flo"]
    model["transitions"] = [{"source": "work", "target": "end"}]
    result = api.export(yaml.safe_dump(model), source_path=str(tmp_path / "root.flo"))
    assert result.ok, result.diagnostics
    edges = json.loads(result.value)["edges"]
    assert [(edge["source"], edge["target"]) for edge in edges] == [
        ("start", "work"),
        ("work", "end"),
    ]


def test_invalid_included_transition_retains_authored_location(tmp_path):
    included = tmp_path / "part.flo"
    included.write_text("transitions:\n- source: start\n  target: end\n  label: []\n")
    result = api.validate(
        yaml.safe_dump({**_flow(), "includes": ["part.flo"]}),
        source_path=str(tmp_path / "root.flo"),
    )
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "E0207"
    assert diagnostic.field_path == "transitions[0].label"
    assert diagnostic.source == str(included)
    assert diagnostic.excerpt.strip() == "label: []"


def test_merged_local_quantity_failure_retains_original_index(tmp_path):
    (tmp_path / "part.flo").write_text(
        yaml.safe_dump({"process": {"items": [_entry("included", "items")]}})
    )
    local = _entry("local", "items")
    local["quantity"] = {
        "kind": "measure",
        "value": 250,
        "unit": "g",
        "canonical_value": 99,
        "canonical_unit": "kg",
    }
    model = {**_flow(), "includes": ["part.flo"]}
    model["process"]["items"] = [local]
    source = tmp_path / "root.flo"
    result = api.validate(yaml.safe_dump(model), source_path=str(source))
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.source == str(source)
    assert diagnostic.field_path == "process.items[0].quantity.canonical_value"
    assert diagnostic.excerpt.strip() == "canonical_value: 99"


def test_duplicate_merged_entries_locate_the_original_local_entry(tmp_path):
    entries = [_entry("same", "items")]
    (tmp_path / "part.flo").write_text(yaml.safe_dump({"process": {"items": entries}}))
    model = {**_flow(), "includes": ["part.flo"]}
    model["process"]["items"] = entries
    source = tmp_path / "root.flo"
    result = api.validate(yaml.safe_dump(model), source_path=str(source))
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "E1221" and diagnostic.source == str(source)
    assert diagnostic.field_path == "process.items[0]"
    assert diagnostic.excerpt.strip() == "- id: same"


@pytest.mark.parametrize("collection", ["items", "resources"])
def test_nested_grouped_includes_retain_both_entries(tmp_path, collection):
    fragment = {
        "process": {
            collection: {
                "batch": {"name": "Batch", "entries": [_entry("included", collection)]}
            }
        }
    }
    (tmp_path / "part.flo").write_text(yaml.safe_dump(fragment))
    model = {**_flow(), "includes": ["part.flo"]}
    model["process"][collection] = {"batch": {"entries": [_entry("local", collection)]}}
    result = api.export(yaml.safe_dump(model), source_path=str(tmp_path / "root.flo"))
    assert result.ok, result.diagnostics
    group = json.loads(result.value)["process"][collection]["batch"]
    assert group["name"] == "Batch"
    assert [entry["id"] for entry in group["entries"]] == ["included", "local"]


@pytest.mark.parametrize("collection", ["items", "resources", "locations"])
@pytest.mark.parametrize("placement", [(), ("process",)])
def test_malformed_canonical_groups_are_not_silently_dropped(collection, placement):
    model = _flow()
    _put(model, collection, {"broken": "not a collection"}, placement)
    result = api.export(yaml.safe_dump(model))
    assert not result.ok and result.value is None
    assert result.diagnostics[0].code == ("E0220" if placement == () else "E1201")
