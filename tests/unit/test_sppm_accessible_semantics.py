"""Meaning survives color removal across the maintained SPPM densities."""

import re
import xml.etree.ElementTree as ET
from functools import cache
from pathlib import Path

import pytest

from flo import api
from flo.render import render_artifact
from flo.render.themes import BUILTIN_THEMES

NS = {"s": "http://www.w3.org/2000/svg"}
SOURCE = (
    Path(__file__).resolve().parents[2] / "examples/reference/sppm_feature_showcase.flo"
)


@cache
def _model():
    result = api.validate(SOURCE.read_text(), source_path=str(SOURCE))
    assert result.ok, result.diagnostics
    return result.value


@pytest.mark.parametrize("theme", sorted(BUILTIN_THEMES))
@pytest.mark.parametrize("density", ["full", "compact", "teaching"])
def test_value_classes_and_control_flow_have_visible_noncolor_cues(theme, density):
    artifact = render_artifact(
        _model(),
        options={"diagram": "sppm", "sppm_theme": theme, "sppm_label_density": density},
    )
    root = ET.fromstring(artifact.content)  # noqa: S314 - Renderer-produced SVG.
    text = {element.text for element in root.findall(".//s:text", NS)}
    assert {"Class: VA", "Class: RNVA", "Class: NVA"} <= text
    assert root.find(".//s:g[@data-node-kind='queue']/s:polygon", NS) is not None
    assert root.find(".//s:g[@data-node-kind='decision']/s:polygon", NS) is not None
    for edge in root.findall(".//s:g[@data-edge-kind='rework']/s:polyline", NS):
        assert edge.get("stroke-dasharray")
    assert artifact.metadata["render_diagnostics"] == []
    if theme == "monochrome":
        colors = {
            element.get(attribute)
            for element in root.iter()
            for attribute in ("fill", "stroke")
            if re.fullmatch(r"#[0-9a-fA-F]{6}", element.get(attribute, ""))
        }
        assert all(
            color[1:3].lower() == color[3:5].lower() == color[5:7].lower()
            for color in colors
        )
