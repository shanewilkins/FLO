"""Supported-field and semantic-metadata architecture drift gates."""

import ast
import re
from pathlib import Path

import pytest

from flo.process import contracts
from flo.source import models

INVENTORY = Path("docs/specs/book_aligned_fields.md")
BOUNDARIES = [
    models.SourceDocument,
    models.SourceFragment,
    models.SourceProcess,
    models.FragmentProcess,
    models.SourceStep,
    models.ControlAttributes,
    models.NamedIdentity,
    models.BusinessUnit,
    models.SourceLane,
    models.BranchConfig,
    models.SourceTransition,
    models.OutcomeBranch,
    contracts.MeasurementProfile,
    contracts.MeasurementResult,
    contracts.MeasurementReference,
    contracts.HandoffRelation,
    contracts.ReworkRelation,
    contracts.ReworkFrequency,
    contracts.ItemContract,
    contracts.ResourceContract,
    contracts.LocationContract,
    contracts.CountQuantity,
    contracts.MeasureQuantity,
    contracts.SpatialContract,
    contracts.LocationMetadata,
]


@pytest.mark.parametrize("boundary", BOUNDARIES, ids=lambda cls: cls.__name__)
def test_every_supported_field_has_documented_semantics_owner_and_consumer(boundary):
    rows = [
        line.split("|")[1:-1]
        for line in INVENTORY.read_text().splitlines()
        if line.startswith(f"| `{boundary.__name__}` |")
    ]
    assert len(rows) == 1
    row = rows[0]
    assert len(row) == 7
    assert set(re.findall(r"`([^`]+)`", row[1])) == set(boundary.model_fields)
    assert all(column.strip() for column in row[2:])


SEMANTIC = {
    "value_class",
    "cycle_time",
    "wait_time",
    "changeover_time",
    "lead_time",
    "consumes",
    "produces",
    "performed_by",
    "uses",
    "handoff",
    "rework",
    "items",
    "resources",
    "locations",
}


def _key_read(node):
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        return node.value, node.slice.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    ):
        return node.func.value, node.args[0].value
    return None


def test_semantic_consumers_do_not_read_core_fields_from_opaque_metadata():
    paths = [
        *Path("src/flo/source").glob("*.py"),
        *Path("src/flo/process/analysis").glob("*.py"),
        *Path("src/flo/render").rglob("*.py"),
    ]
    violations = []
    for path in paths:
        tree = ast.parse(path.read_text())
        for scope in [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]:
            opaque_names = set()
            for node in ast.walk(scope):
                if (
                    isinstance(node, ast.Assign)
                    and (read := _key_read(node.value))
                    and read[1] == "metadata"
                ):
                    opaque_names.update(
                        target.id
                        for target in node.targets
                        if isinstance(target, ast.Name)
                    )
            for node in ast.walk(scope):
                read = _key_read(node)
                if not read or read[1] not in SEMANTIC:
                    continue
                base = read[0]
                chained = _key_read(base)
                if (isinstance(base, ast.Name) and base.id in opaque_names) or (
                    chained and chained[1] == "metadata"
                ):
                    violations.append(f"{path}:{node.lineno}: {read[1]}")
    assert violations == []
