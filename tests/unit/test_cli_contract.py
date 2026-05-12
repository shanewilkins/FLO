"""Tests for the framework-agnostic CLI dispatch contract."""

import pytest

from flo.core._cli_contract import ParsedArgs, parse_cli_args


def test_parsed_args_contract_stores_components():
    args = ParsedArgs(path="test.flo", command="run", options={"verbose": True})
    assert args.path == "test.flo"
    assert args.command == "run"
    assert args.options == {"verbose": True}


def test_parsed_args_is_frozen():
    """Verify ParsedArgs cannot be mutated after creation."""
    args = ParsedArgs(path="test.flo", command="run", options={})
    with pytest.raises(AttributeError):
        args.path = "other.flo"  # type: ignore


def test_parsed_args_asdict_for_backward_compat():
    args = ParsedArgs(path="test.flo", command="validate", options={"export": "json"})
    d = args.asdict()
    assert d == {"path": "test.flo", "command": "validate", "options": {"export": "json"}}


def test_parse_cli_args_with_none_returns_default():
    parsed = parse_cli_args(None)
    assert parsed.path is None
    assert parsed.command == "run"
    assert parsed.options == {}


def test_parse_cli_args_parses_file_path():
    parsed = parse_cli_args(["test.flo"])
    assert parsed.path == "test.flo"
    assert parsed.command == "run"


def test_parse_cli_args_parses_explicit_command():
    parsed = parse_cli_args(["compile", "test.flo"])
    assert parsed.path == "test.flo"
    assert parsed.command == "compile"


def test_parse_cli_args_respects_validate_flag():
    parsed = parse_cli_args(["test.flo", "--validate"])
    assert parsed.command == "validate"


def test_parse_cli_args_collects_render_options():
    parsed = parse_cli_args(["test.flo", "--diagram", "sppm", "--orientation", "tb"])
    assert parsed.options.get("diagram") == "sppm"
    assert parsed.options.get("orientation") == "tb"


def test_parse_cli_args_parses_verbose_flag():
    parsed = parse_cli_args(["test.flo", "--verbose"])
    assert parsed.options.get("verbose") is True


def test_parse_cli_args_parses_export_format():
    parsed = parse_cli_args(["export", "test.flo", "--export", "json"])
    assert parsed.command == "export"
    assert parsed.options.get("export") == "json"
