import io
from flo.services import get_services
from flo.cli_args import parse_args


def test_parse_args_none_returns_defaults():
    services = get_services(verbose=False)
    path, command, options, services_out, logger = parse_args(None, services)
    assert path is None
    assert command == "compile"
    assert isinstance(options, dict)
    assert services_out is services


def test_parse_args_with_flags(tmp_path):
    services = get_services(verbose=False)
    args = ["/tmp/input.flo", "-v", "-o", "out.txt", "--validate"]
    path, command, options, services_out, logger = parse_args(args, services)
    assert path == "/tmp/input.flo"
    assert command == "validate"
    assert options["verbose"] is True
    assert options["output"] == "out.txt"
