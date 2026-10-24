"""Keep the accepted no-browser-runtime render architecture enforceable."""

import ast
import re
import tomllib
from pathlib import Path

BROWSER_LIBRARIES = frozenset({"playwright", "selenium", "pyppeteer", "puppeteer"})
ROOT = Path(__file__).resolve().parents[2]


def _browser_imports(source):
    modules = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module.split(".")[0])
    return set(modules) & BROWSER_LIBRARIES


def test_no_browser_runtime_in_product_rendering():
    offenders = {
        str(path.relative_to(ROOT)): sorted(_browser_imports(path.read_text()))
        for path in (ROOT / "src/flo").rglob("*.py")
        if _browser_imports(path.read_text())
    }
    assert offenders == {}
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependencies = {
        re.split(r"[<>=!~;\[ ]", value.lower(), maxsplit=1)[0]
        for value in project["project"]["dependencies"]
    }
    assert not dependencies & BROWSER_LIBRARIES


def test_browser_runtime_detector_catches_nested_imports_but_not_test_consumer_text():
    assert _browser_imports(
        "def render():\n    from playwright.sync_api import sync_playwright"
    ) == {"playwright"}
    assert _browser_imports("import selenium.webdriver") == {"selenium"}
    assert not _browser_imports('description = "CI may open an SVG in a browser"')
