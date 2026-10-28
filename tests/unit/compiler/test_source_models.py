"""Typed source structure preserves authored data, diagnostics, and IR boundaries."""

from copy import deepcopy

import pytest

from flo import api
from flo.source import compile_adapter
from flo.source.models import SourceDocument, SourceShapeError, validate_source_shape


@pytest.mark.parametrize("children", ["steps", "subnodes"])
def test_nested_attrs_error_points_to_the_authored_child_field(children):
    source = f"""spec_version: '0.1'
process: {{id: example, name: Example}}
steps:
  - id: start
    kind: start
  - id: group
    kind: subprocess
    {children}:
      - id: child
        kind: task
        attrs:
          metadata: invalid
  - id: end
    kind: end
"""
    result = api.compile(source, source_path="nested.flo")
    diagnostic = result.diagnostics[0]

    assert not result.ok
    assert diagnostic.source == "nested.flo"
    assert diagnostic.field_path == f"steps[1].{children}[0].attrs.metadata"
    assert diagnostic.line == 12
    assert diagnostic.column == 11
    assert diagnostic.excerpt.strip() == "metadata: invalid"


def test_required_process_field_has_a_structured_source_location():
    result = api.compile(
        "spec_version: '0.1'\nprocess:\n  id: 42\n  name: Example\nsteps: [{id: end, kind: end}]",
        source_path="identity.flo",
    )
    diagnostic = result.diagnostics[0]

    assert diagnostic.field_path == "process.id"
    assert diagnostic.line == 3
    assert diagnostic.column == 3
    assert diagnostic.message == "E0222: process.id must be a non-empty string"


def test_yaml_merge_key_does_not_break_structural_error_enrichment():
    source = """spec_version: '0.1'
process: {id: example, name: Example}
base: &base {kind: task}
steps:
  - <<: *base
    id: work
    attrs:
      metadata: invalid
"""
    diagnostic = api.compile(source, source_path="merged.flo").diagnostics[0]
    assert diagnostic.field_path == "steps[0].attrs.metadata"
    assert diagnostic.line == 8


@pytest.mark.parametrize("label", ["branch", "bool", "version", "outcome"])
def test_named_branch_paths_do_not_confuse_names_with_validation_internals(label):
    source = f"""spec_version: '0.1'
process: {{id: example, name: Example}}
steps:
  - id: decision
    kind: decision
    outcomes:
      {label}:
        target: finish
        rework: invalid
      other: finish
  - id: finish
    kind: end
"""
    diagnostic = api.compile(source, source_path="branch.flo").diagnostics[0]

    assert diagnostic.code == "E0209"
    assert diagnostic.field_path == f"steps[0].outcomes.{label}.rework"
    assert diagnostic.line == 9
    assert diagnostic.suggestion == "Define a structured handoff or rework object."


def test_attrs_overlay_is_validated_as_the_effective_branch_configuration():
    source = {
        "spec_version": "0.1",
        "process": {"id": "example", "name": "Example"},
        "steps": [
            {
                "id": "branch",
                "kind": "branch",
                "branch": {"mode": "invalid"},
                "attrs": {"branch": {"mode": "dispatch"}},
            }
        ],
    }
    assert compile_adapter(source).nodes[0].attrs["branch"]["mode"] == "dispatch"
    source["steps"][0]["attrs"]["branch"]["mode"] = "invalid"
    with pytest.raises(SourceShapeError) as exc:
        compile_adapter(source)
    assert exc.value.location == ("steps", 0, "attrs", "branch", "mode")
    assert "E0216" in str(exc.value)


def test_models_do_not_rewrite_authored_scalars_annotations_or_omissions():
    source = {
        "spec_version": "0.1",
        "process": {
            "id": "example",
            "name": " Example ",
            "version": 2,
            "extensions": {"example:annotation": {"value": True}},
        },
        "steps": [
            {
                "id": "group",
                "kind": "subprocess",
                "steps": [
                    {
                        "id": "child",
                        "kind": "task",
                        "extensions": {"example:custom": 5},
                    }
                ],
            }
        ],
    }
    before = deepcopy(source)
    model = validate_source_shape(SourceDocument, source)
    process = compile_adapter(source)

    assert model.model_dump(exclude_unset=True) == before
    assert source == before
    assert process.process_version == 2
    assert process.process_metadata["process_name"] == " Example "
    assert process.extensions == {"example:annotation": {"value": True}}
    assert process.nodes[1].subprocess_parent == "group"
    assert process.nodes[1].extensions == {"example:custom": 5}


@pytest.mark.parametrize("value", [True, 1.5])
def test_source_versions_are_not_coerced(value):
    source = {
        "spec_version": "0.1",
        "process": {"id": "example", "name": "Example", "version": value},
        "steps": [{"id": "end", "kind": "end"}],
    }
    with pytest.raises(SourceShapeError) as exc:
        compile_adapter(source)
    assert exc.value.location == ("process", "version")
