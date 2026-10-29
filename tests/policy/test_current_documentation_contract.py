"""Keep current instructional YAML executable under the accepted contract."""

import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from flo import api
from flo.process.ir.models import IR
from flo.process.ir.validate_render_intent import validate_render_intent
from flo.source.models import SourceFragment, SourceStep, validate_source_shape

DOCUMENTS = [
    Path("README.md"),
    Path("docs/Quickstart.md"),
    Path("docs/User_Manual.md"),
    *sorted(Path("docs/specs").glob("*.md")),
    Path("docs/design/render_intent_schema.md"),
]


@pytest.mark.parametrize("path", DOCUMENTS, ids=str)
def test_current_instructional_yaml_uses_supported_source_shapes(path):
    content = path.read_text()
    for match in re.finditer(
        r"^```[ \t]*(?:yaml|yml|flo)[ \t]*\n(.*?)^```", content, re.S | re.M
    ):
        line = content[: match.start()].count("\n") + 1
        data = yaml.safe_load(match[1])
        assert isinstance(data, dict), f"{path}:{line}: expected an authored mapping"
        if set(data) & {
            "process",
            "steps",
            "transitions",
            "spec_version",
            "lanes",
            "includes",
            "include",
        }:
            validate_source_shape(SourceFragment, data)
            Draft202012Validator(SourceFragment.model_json_schema()).validate(
                json.loads(json.dumps(data))
            )
            if {"spec_version", "process", "steps"} <= set(data) and not set(data) & {
                "includes",
                "include",
            }:
                result = api.validate(match[1])
                assert result.ok, (path, line, result.diagnostics)
            render = data.get("process", {}).get("render")
            if render is not None:
                validate_render_intent(
                    IR(name="example", nodes=[], render_intent=render)
                )
        else:
            # A standalone timing block documents one work-step field.
            step = {"id": "example", "kind": "task", **data}
            SourceStep.model_validate(step)
            Draft202012Validator(SourceStep.model_json_schema()).validate(step)
