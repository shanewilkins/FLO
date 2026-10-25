"""Resource quantity semantics preserve syntax and source-aware delivery."""

import json
from copy import deepcopy

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli


def _source(quantity, *, collection="items", placement="top", grouped=False):
    entry = {"id": "supply", "name": "Supply", "quantity": quantity}
    if collection in {"items", "resources"}:
        entry["kind"] = "material" if collection == "items" else "equipment"
    entries = {"dry.mix": {"sub group": [entry]}} if grouped else [entry]
    model = {
        "spec_version": "0.1",
        "process": {"id": "quantities", "name": "Quantities"},
        "steps": [{"id": "start", "kind": "start"}, {"id": "end", "kind": "end"}],
    }
    if placement == "top":
        model[collection] = entries
    elif placement == "process":
        model["process"][collection] = entries
    else:
        model["process"]["metadata"] = {collection: entries}
    return yaml.safe_dump(model, sort_keys=False)


_INVALID_CANONICALS = [
    ({"canonical_value": 0.25, "canonical_unit": "l"}, "E1222", "canonical_unit"),
    ({"canonical_value": 99, "canonical_unit": "kg"}, "E1223", "canonical_value"),
    (
        {
            "value": 1e308,
            "unit": "kg",
            "canonical_value": 1e308,
            "canonical_unit": "mg",
        },
        "E1224",
        "canonical_value",
    ),
]


@pytest.mark.parametrize("patch,code,field", _INVALID_CANONICALS)
@pytest.mark.parametrize(
    "collection,placement",
    [
        ("items", "top"),
        ("resources", "process"),
        ("locations", "metadata"),
        ("materials", "top"),
        ("equipment", "process"),
        ("workers", "metadata"),
    ],
)
def test_quantity_errors_locate_authored_grouped_fields_in_cli_and_api(
    patch, code, field, collection, placement
):
    quantity = {"kind": "measure", "value": 250, "unit": "g", **patch}
    source = _source(quantity, collection=collection, placement=placement, grouped=True)
    result = api.validate(source, source_path="-")
    assert not result.ok
    record = result.report.diagnostics[0]
    prefix = {"top": "", "process": "process.", "metadata": "process.metadata."}[
        placement
    ]
    assert (
        record.field_path
        == f"{prefix}{collection}.dry.mix.sub group[0].quantity.{field}"
    )
    assert record.code == code and record.stage == "validate"
    assert record.excerpt == source.splitlines()[record.line - 1]
    assert record.excerpt.strip().startswith(f"{field}:")
    assert record.suggestion

    command = CliRunner().invoke(
        cli, ["validate", "-", "--diagnostics-format", "json"], input=source
    )
    assert command.exit_code == 4 and command.stdout == ""
    assert json.loads(command.stderr) == json.loads(json.dumps(result.report.as_dict()))


@pytest.mark.parametrize("patch,code,field", _INVALID_CANONICALS)
def test_invalid_canonical_quantities_stop_every_validated_consumer(
    patch, code, field, tmp_path
):
    content = _source({"kind": "measure", "value": 250, "unit": "g", **patch})
    source = tmp_path / "invalid.flo"
    source.write_text(content)
    expected = api.validate(content, source_path=str(source)).report
    for operation in (api.inspect, api.export):
        result = operation(content, source_path=str(source))
        assert not result.ok and result.value is None
        assert result.report == expected
    output = tmp_path / "invalid.svg"
    for args in (
        ["inspect", str(source), "--format", "json"],
        ["export", str(source)],
        ["render", str(source), "--render-to", str(output)],
    ):
        result = CliRunner().invoke(cli, [*args, "--diagnostics-format", "json"])
        assert result.exit_code == 4 and result.stdout == ""
        report = json.loads(result.stderr)
        assert report["error_count"] == 1 and report["warning_count"] == 0
        assert report["diagnostics"][0]["code"] == code
    assert not output.exists()


@pytest.mark.parametrize(
    "quantity",
    [
        {
            "kind": "measure",
            "value": 250,
            "unit": "g",
            "canonical_value": 0.25,
            "canonical_unit": "kg",
        },
        {
            "kind": "measure",
            "value": 500,
            "unit": "ml",
            "canonical_value": 0.5,
            "canonical_unit": "l",
        },
        {
            "kind": "measure",
            "value": 2.5,
            "unit": "cm",
            "canonical_value": 25,
            "canonical_unit": "mm",
        },
        {"kind": "measure", "value": 250, "unit": "g"},
        {"kind": "count", "value": 2, "unit": "each", "qualifier": "large"},
    ],
)
def test_valid_quantities_preserve_exchange_and_authored_export_text(quantity):
    before = deepcopy(quantity)
    content = _source(quantity)
    exported = api.export(content)
    assert exported.ok and not exported.diagnostics
    record = json.loads(exported.value)["process"]["metadata"]["items"][0]
    assert record["quantity"] == before
    assert type(record["quantity"]["value"]) is type(before["value"])
    text = api.export(content, export_format="ingredients")
    assert text.ok and f"Supply: {quantity['value']} {quantity['unit']}" in text.value
    rendered = CliRunner().invoke(
        cli, ["render", "-", "--diagnostics-format", "json"], input=content
    )
    assert rendered.exit_code == 0 and "<svg" in rendered.stdout
    assert json.loads(rendered.stderr)["diagnostics"] == []
    assert quantity == before


def test_legacy_diagnostic_uses_the_selected_collection_not_an_ignored_scalar():
    model = yaml.safe_load(
        _source(
            {
                "kind": "measure",
                "value": 250,
                "unit": "g",
                "canonical_value": 99,
                "canonical_unit": "kg",
            },
            collection="materials",
            placement="process",
        )
    )
    model["materials"] = "ignored legacy scalar"
    result = api.validate(yaml.safe_dump(model))

    assert not result.ok
    assert (
        result.diagnostics[0].field_path
        == "process.materials[0].quantity.canonical_value"
    )
    assert result.diagnostics[0].excerpt.strip() == "canonical_value: 99"
