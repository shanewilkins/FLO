"""A browser report must contain real measured glyphs, not partial DOM output."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "svg_browser", Path(__file__).resolve().parents[2] / "scripts/check_svg_browser.py"
)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def test_missing_or_unmeasured_browser_output_cannot_pass():
    for output in (
        "<html></html>",
        '<pre id="result"></pre>',
        '<pre id="result">{"cases":[]}</pre>',
        '<pre id="result">{"cases":[{"text_count":0}]}</pre>',
    ):
        with pytest.raises((ValueError, KeyError)):
            CHECK.parse_result(output)


def test_browser_result_decodes_html_entities():
    result = CHECK.parse_result(
        '<pre id="result">{&quot;cases&quot;:[{&quot;text_count&quot;:3}]}</pre>'
    )
    assert result["cases"][0]["text_count"] == 3
