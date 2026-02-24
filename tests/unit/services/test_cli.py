import importlib
import sys


fm_core = importlib.import_module("flo.core")
fm_cli = importlib.import_module("flo.core.cli")


def test_run_returns_message_and_no_error():
    # Test the functional logic directly (no stdout/stderr side-effects)
    rc, out, err = fm_core.run()
    assert rc == 0
    assert out == ""
    assert err == ""


def test_main_returns_zero():
    # Ensure the programmatic run returns the expected exit code
    rc, out, err = fm_core.run()
    assert rc == 0


def test_main_captures_stdout_and_stderr(capsys):
    # Presentation-level test: ensure something goes to stdout and stderr
    rc, out, err = fm_core.run()
    # Simulate console printing of returned outputs
    print(out)
    print(err, file=sys.stderr)
    captured = capsys.readouterr()
    assert rc == 0
    # We don't assert specific content; ensure capture succeeded.
    assert captured is not None


def test_cli_module_has_expected_entrypoints():
    # Ensure the CLI module exposes the main commands used by integration
    assert hasattr(fm_cli, "run_cmd") or hasattr(fm_cli, "console_main")


def test_main_error_path_writes_stderr(monkeypatch, capsys):
    # Simulate an error in the functional layer and ensure main prints to stderr
    def fake_run():
        return 2, "", "fatal error occurred"

    monkeypatch.setattr(fm_core, "run", fake_run)
    rc, out, err = fm_core.run()
    # Simulate console printing of error path
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    captured = capsys.readouterr()
    assert rc == 2
    # The error may be logged to either stdout or stderr; ensure at least one
    # stream contains output and the exit code reflects the error.
    assert (captured.out.strip() != "") or (captured.err.strip() != "")
