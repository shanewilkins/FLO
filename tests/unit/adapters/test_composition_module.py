from __future__ import annotations

from pathlib import Path

import pytest

import flo.adapters.composition as composition


def test_normalize_include_entries_supports_empty_string_string_and_list():
    assert composition._normalize_include_entries({}) == []
    assert composition._normalize_include_entries({"include": "   "}) == []
    assert composition._normalize_include_entries({"include": "  part.yaml  "}) == ["part.yaml"]
    assert composition._normalize_include_entries({"includes": [" a.yaml ", "b.yaml"]}) == ["a.yaml", "b.yaml"]


def test_normalize_include_entries_rejects_invalid_shapes():
    with pytest.raises(ValueError, match="include/includes must be a string or list of strings"):
        composition._normalize_include_entries({"includes": 42})

    with pytest.raises(ValueError, match=r"includes\[1\] must be a non-empty string path"):
        composition._normalize_include_entries({"includes": ["ok.yaml", ""]})


def test_resolve_include_path_supports_absolute_and_cwd_relative(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    absolute_target = tmp_path / "abs.yaml"
    resolved_abs = composition._resolve_include_path(str(absolute_target), current_path=tmp_path / "root.flo")
    assert resolved_abs == absolute_target.resolve()

    monkeypatch.chdir(tmp_path)
    resolved_rel = composition._resolve_include_path("parts/flow.yaml", current_path=None)
    assert resolved_rel == (tmp_path / "parts" / "flow.yaml").resolve()


def test_load_include_mapping_rejects_cycle_missing_and_non_mapping(tmp_path: Path):
    cycle_path = tmp_path / "cycle.yaml"
    cycle_path.write_text("a: 1", encoding="utf-8")
    with pytest.raises(ValueError, match="include cycle detected"):
        composition._load_include_mapping(cycle_path, include_stack=[cycle_path])

    missing = tmp_path / "missing.yaml"
    with pytest.raises(ValueError, match="include file not found"):
        composition._load_include_mapping(missing, include_stack=[])

    not_mapping = tmp_path / "list.yaml"
    not_mapping.write_text("- item", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        composition._load_include_mapping(not_mapping, include_stack=[])


def test_merge_list_values_covers_none_and_validation_errors():
    assert composition._merge_list_values("steps", base_value=[{"id": "a"}], incoming_value=None) == [{"id": "a"}]
    assert composition._merge_list_values("steps", base_value="bad", incoming_value=None) == []

    with pytest.raises(ValueError, match="steps must be a list"):
        composition._merge_list_values("steps", base_value=[], incoming_value="bad")

    with pytest.raises(ValueError, match="steps must be a list"):
        composition._merge_list_values("steps", base_value="bad", incoming_value=[])


def test_merge_resource_values_covers_list_dict_and_type_mismatch():
    assert composition._merge_resource_values("materials", base_value=None, incoming_value=[{"id": "a"}]) == [{"id": "a"}]
    assert composition._merge_resource_values("materials", base_value=[{"id": "a"}], incoming_value=None) == [{"id": "a"}]

    merged_lists = composition._merge_resource_values(
        "materials",
        base_value=[{"id": "a"}],
        incoming_value=[{"id": "b"}],
    )
    assert merged_lists == [{"id": "a"}, {"id": "b"}]

    merged_dicts = composition._merge_resource_values(
        "materials",
        base_value={
            "name": "Base",
            "group": {"items": [{"id": "a"}]},
        },
        incoming_value={
            "name": "Incoming",
            "group": {"items": [{"id": "b"}]},
            "extra": [{"id": "c"}],
        },
    )
    assert merged_dicts["name"] == "Base"
    assert merged_dicts["group"]["items"] == [{"id": "a"}, {"id": "b"}]
    assert merged_dicts["extra"] == [{"id": "c"}]

    with pytest.raises(ValueError, match="materials include merge type mismatch"):
        composition._merge_resource_values("materials", base_value={}, incoming_value=[])


def test_merge_process_covers_none_metadata_merge_and_type_error():
    assert composition._merge_process(None, {"id": "p"}) == {"id": "p"}
    assert composition._merge_process({"id": "p"}, None) == {"id": "p"}

    merged = composition._merge_process(
        {"name": "old", "metadata": {"a": 1}},
        {"name": "new", "metadata": {"b": 2}},
    )
    assert merged["name"] == "new"
    assert merged["metadata"] == {"a": 1, "b": 2}

    with pytest.raises(ValueError, match="process must be an object when present"):
        composition._merge_process([], {})


def test_merge_documents_preserves_existing_spec_version_and_merges_known_keys():
    merged = composition._merge_documents(
        base={"spec_version": "0.1", "other": "old", "steps": [{"id": "a"}]},
        incoming={
            "spec_version": "0.2",
            "steps": [{"id": "b"}],
            "materials": [{"id": "flour"}],
            "process": {"id": "cookie"},
            "other": "new",
        },
    )

    assert merged["spec_version"] == "0.1"
    assert [step["id"] for step in merged["steps"]] == ["a", "b"]
    assert merged["materials"] == [{"id": "flour"}]
    assert merged["process"] == {"id": "cookie"}
    assert merged["other"] == "new"


def test_ensure_unique_id_list_skips_non_dict_or_missing_id_and_raises_for_duplicate():
    composition._ensure_unique_id_list(
        {"steps": ["skip", {"name": "skip"}, {"id": "ok"}]},
        key="steps",
    )

    with pytest.raises(ValueError, match="duplicate lane id 'ops' detected"):
        composition._ensure_unique_id_list(
            {"lanes": [{"id": "ops"}, {"id": "ops"}]},
            key="lanes",
        )


def test_resolve_includes_without_source_path_uses_current_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    include_file = tmp_path / "fragment.yaml"
    include_file.write_text("steps:\n  - id: s1\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    composed = composition.resolve_includes({"include": "fragment.yaml"})

    assert composed["steps"] == [{"id": "s1"}]
