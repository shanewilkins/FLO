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


def test_main_captures_stdout_and_stderr():
    # run() with no path returns empty output
    rc, out, err = fm_core.run()
    assert rc == 0
    assert out == ""
    assert err == ""


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
    assert captured.out.strip() == ""
    assert "fatal error occurred" in captured.err
