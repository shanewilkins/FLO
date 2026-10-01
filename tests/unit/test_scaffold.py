from pathlib import Path

import pytest

from flo.app.scaffold import (
    SUPPORTED_TEMPLATES,
    create_model,
    render_template,
    stable_id,
)
from flo.process.ir.validate import validate_ir
from flo.source import compile_adapter, parse_adapter


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Purchase Request", "purchase_request"),
        ("  First Model  ", "first_model"),
        ("2026 Intake", "process_2026_intake"),
        ("***", "simple_process"),
    ],
)
def test_stable_id_is_readable_and_yaml_safe(name: str, expected: str):
    assert stable_id(name) == expected


def test_render_simple_process_template_has_explicit_stable_ids():
    content = render_template(
        template="simple-process",
        process_name="Purchase Request",
    )

    assert "id: purchase_request" in content
    assert "- id: start" in content
    assert "- id: receive_request" in content
    assert "- id: complete_work" in content
    assert "- id: finish" in content


@pytest.mark.parametrize("template", SUPPORTED_TEMPLATES)
def test_templates_compile_to_valid_models(template: str):
    content = render_template(template=template, process_name="Purchase Request")

    process = compile_adapter(parse_adapter(content))

    validate_ir(process)
    assert process.process_metadata is not None
    assert process.process_metadata["process_id"] == "purchase_request"


def test_create_model_adds_flo_suffix_and_refuses_overwrite(tmp_path: Path):
    target = create_model(tmp_path / "my-process", process_name="My Process")

    assert target.name == "my-process.flo"
    assert target.is_file()
    with pytest.raises(FileExistsError):
        create_model(target, process_name="Replacement")
