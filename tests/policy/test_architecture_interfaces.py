"""Exercise boundary enforcement with new modules, consumers, and import forms."""

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from architecture_interfaces import (  # noqa: E402
    findings,
    import_references,
    interface_violations,
    module_name,
    sppm_classification_violations,
)

PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text())
POLICY = PROJECT["tool"]["flo_architecture"]
CONTRACTS = PROJECT["tool"]["importlinter"]["contracts"]
MODULES = {module_name(path, ROOT / "src") for path in (ROOT / "src/flo").rglob("*.py")}


def test_current_product_and_consumers_obey_declared_interfaces():
    assert findings(ROOT) == []


@pytest.mark.parametrize(
    ("source", "importer", "blocked"),
    [
        ("from flo.process import IR", "flo.app.consumer", False),
        ("from flo.process.ir import IR", "flo.app.consumer", False),
        ("from ..process.ir import IR", "flo.app.consumer", False),
        (
            "from flo.process.ir.validate_graph import validate_graph",
            "flo.app.consumer",
            True,
        ),
        (
            "from flo.process import ir\nir.validate_graph.validate_graph()",
            "flo.app.consumer",
            True,
        ),
        (
            "from flo import render as r\nr.sppm.renderer.render_sppm_svg_artifact()",
            "flo.app.consumer",
            True,
        ),
        ("from flo.render import render_execution", "flo.app.consumer", False),
        ("from flo.render.options import *", "flo.app.consumer", True),
        ("def run():\n    from flo import validate", "flo.process.consumer", True),
        ("import flo.api as api\napi.validate('')", "flo.source.consumer", True),
        ("from flo import validate", "flo.errors", True),
        ("from . import svg", "flo.render.sppm.consumer", False),
    ],
)
def test_cross_subsystem_interfaces_resolve_import_forms(source, importer, blocked):
    references = import_references(source, importer, is_package=False, modules=MODULES)
    assert (
        bool(interface_violations(references, importer, POLICY["interfaces"]))
        is blocked
    )


@pytest.mark.parametrize("name", ["new_policy", "nested.new_policy"])
def test_new_sppm_modules_require_classification(name):
    module = f"flo.render.sppm.{name}"
    modules = MODULES | {module}
    assert sppm_classification_violations(modules, POLICY, CONTRACTS) == [
        f"unclassified SPPM module: {module}"
    ]


@pytest.fixture
def policy_checkout(tmp_path):
    """Copy static inputs only; never mutate the working checkout for probes."""
    shutil.copy(ROOT / "pyproject.toml", tmp_path)
    for path in (ROOT / "src/flo").rglob("*.py"):
        target = tmp_path / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("")
    for relative in POLICY["intermediate_consumers"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / relative, target)
    return tmp_path


@pytest.mark.parametrize("suffix", [".py", ".ipynb"])
def test_new_artifact_consumers_cannot_import_intermediate_pipeline(
    policy_checkout, suffix
):
    consumer = policy_checkout / f"examples/new_lesson{suffix}"
    consumer.parent.mkdir(exist_ok=True)
    source = "def render():\n    from flo.render.sppm import renderer as r\n    r.render_sppm_svg_artifact()"
    if suffix == ".ipynb":
        source = json.dumps(
            {
                "cells": [
                    {"cell_type": "code", "source": source.splitlines(keepends=True)}
                ]
            }
        )
    consumer.write_text(source)
    assert "examples/new_lesson" + suffix in findings(policy_checkout)[0]["evidence"]


def test_intermediate_exception_does_not_allow_additional_implementation_imports(
    policy_checkout,
):
    path = policy_checkout / "scripts/architecture_trace.py"
    path.write_text(
        path.read_text()
        + "\nfrom flo.render.sppm.layout import build_sppm_elk_layout_request\n"
    )
    assert "scripts/architecture_trace.py" in findings(policy_checkout)[0]["evidence"]


def test_notebook_module_aliases_cannot_hide_pipeline_access_in_later_cells(
    policy_checkout,
):
    consumer = policy_checkout / "examples/new_lesson.ipynb"
    consumer.parent.mkdir(exist_ok=True)
    consumer.write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "code", "source": ["import flo as f"]},
                    {
                        "cell_type": "code",
                        "source": ["f.render.sppm.renderer.render_sppm_svg_artifact()"],
                    },
                ]
            }
        )
    )
    assert "examples/new_lesson.ipynb" in findings(policy_checkout)[0]["evidence"]


def test_unused_intermediate_exceptions_fail(policy_checkout):
    (policy_checkout / "scripts/architecture_trace.py").write_text(
        "from flo.render import render_execution\n"
    )
    assert (
        "scripts/architecture_trace.py exception"
        in findings(policy_checkout)[0]["evidence"]
    )


@pytest.mark.parametrize(
    ("contract_name", "sources", "passes"),
    [
        (
            "Shared error and diagnostic contracts are leaves",
            {"flo.errors": "from flo import diagnostics"},
            True,
        ),
        (
            "Shared error and diagnostic contracts are leaves",
            {"flo.errors": "from .app import operation"},
            False,
        ),
        (
            "Shared error and diagnostic contracts are leaves",
            {
                "flo.diagnostics": "from . import helper",
                "flo.helper": "import flo.render",
            },
            False,
        ),
        (
            "SPPM SVG emission cannot run node or route layout policy",
            {"flo.render.sppm.svg": "from . import content"},
            True,
        ),
        (
            "SPPM SVG emission cannot run node or route layout policy",
            {
                "flo.render.sppm.svg": "from . import content",
                "flo.render.sppm.content": "from . import strategy",
            },
            False,
        ),
    ],
)
def test_real_import_contracts_reject_direct_and_indirect_breaches(
    tmp_path, contract_name, sources, passes
):
    contract = next(item for item in CONTRACTS if item["name"] == contract_name)
    names = set(contract["source_modules"] + contract["forbidden_modules"]) | set(
        sources
    )
    names |= {"flo.render.sppm.content", "flo.helper", "flo.diagnostics"}
    packages = {
        "flo",
        "flo.app",
        "flo.process",
        "flo.source",
        "flo.render",
        "flo.render.sppm",
        "flo.render.layout_core",
    }
    for name in sorted(names | packages):
        location = tmp_path / name.replace(".", "/")
        path = (
            location / "__init__.py"
            if name in packages
            else location.with_suffix(".py")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sources.get(name, ""))
    text = (
        '[tool.importlinter]\nroot_package = "flo"\n[[tool.importlinter.contracts]]\n'
    )
    text += "\n".join(f"{key} = {json.dumps(value)}" for key, value in contract.items())
    (tmp_path / "pyproject.toml").write_text(text)
    result = subprocess.run(  # noqa: S603 - Installed linter with isolated test inputs.
        [str(Path(sys.executable).parent / "lint-imports")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert (result.returncode == 0) is passes, result.stdout + result.stderr
