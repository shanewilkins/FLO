from __future__ import annotations

from pathlib import Path

import pytest

from flo.adapters import parse_adapter


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_parse_adapter_resolves_includes_relative_to_source_file(tmp_path: Path):
    root = tmp_path / "process.flo"
    flow_part = tmp_path / "parts" / "flow.yaml"
    resources_part = tmp_path / "parts" / "resources.yaml"

    _write(
        flow_part,
        """
steps:
  - id: start
    kind: start
  - id: end
    kind: end
transitions:
  - source: start
    target: end
""".strip(),
    )
    _write(
        resources_part,
        """
materials:
  - id: flour
    name: Flour
""".strip(),
    )
    _write(
        root,
        """
spec_version: "0.1"
process:
  id: cookie
  name: Cookie
includes:
  - parts/resources.yaml
  - parts/flow.yaml
""".strip(),
    )

    parsed = parse_adapter(root.read_text(encoding="utf-8"), source_path=str(root))
    assert parsed["process"]["id"] == "cookie"
    assert parsed["materials"][0]["id"] == "flour"
    assert [step["id"] for step in parsed["steps"]] == ["start", "end"]
    assert parsed["transitions"][0]["source"] == "start"


def test_parse_adapter_rejects_include_cycles(tmp_path: Path):
    a = tmp_path / "a.flo"
    b = tmp_path / "b.flo"

    _write(a, 'includes: ["b.flo"]')
    _write(b, 'includes: ["a.flo"]')

    with pytest.raises(ValueError, match="include cycle detected"):
        parse_adapter(a.read_text(encoding="utf-8"), source_path=str(a))


def test_parse_adapter_rejects_duplicate_step_ids_across_includes(tmp_path: Path):
    root = tmp_path / "process.flo"
    p1 = tmp_path / "parts" / "a.yaml"
    p2 = tmp_path / "parts" / "b.yaml"

    _write(
        p1,
        """
steps:
  - id: start
    kind: start
""".strip(),
    )
    _write(
        p2,
        """
steps:
  - id: start
    kind: start
""".strip(),
    )
    _write(
        root,
        """
includes:
  - parts/a.yaml
  - parts/b.yaml
""".strip(),
    )

    with pytest.raises(ValueError, match="duplicate step id"):
        parse_adapter(root.read_text(encoding="utf-8"), source_path=str(root))
