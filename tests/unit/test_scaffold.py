from pathlib import Path

import pytest

from flo.app.scaffold import create_model, render_template, stable_id


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


def test_create_model_adds_flo_suffix_and_refuses_overwrite(tmp_path: Path):
    target = create_model(tmp_path / "my-process", process_name="My Process")

    assert target.name == "my-process.flo"
    assert target.is_file()
    with pytest.raises(FileExistsError):
        create_model(target, process_name="Replacement")
