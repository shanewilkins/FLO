from flo.services import get_services
from flo.core.cli_args import parse_args
import pytest


@pytest.fixture
def services():
    return get_services(verbose=False)


def test_parse_args_none_returns_defaults(services):
    path, command, options, services_out, logger = parse_args(None, services)
    assert path is None
    assert command == "compile"
    assert isinstance(options, dict)
    assert services_out is services


@pytest.mark.parametrize(
    "args, expected_command, expected_output",
    [
        (["/tmp/input.flo", "-v", "-o", "out.txt", "--validate"], "validate", "out.txt"),
        (["file.flo"], "compile", None),
    ],
)
def test_parse_args_with_flags(services, args, expected_command, expected_output):
    path, command, options, services_out, logger = parse_args(args, services)
    assert path == (args[0] if args else None)
    assert command == expected_command
    if expected_output:
        assert options["output"] == expected_output
