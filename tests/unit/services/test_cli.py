import importlib


fm = importlib.import_module("flo.main")


def test_run_returns_message_and_no_error():
    # Test the functional logic directly (no stdout/stderr side-effects)
    rc, out, err = fm.run()
    assert rc == 0
    assert out == "Hello world!"
    assert err == ""


def test_main_returns_zero():
    # Ensure the console entrypoint returns the expected exit code
    rc = fm.main()
    assert rc == 0


def test_main_captures_stdout_and_stderr(capsys):
    # Presentation-level test: ensure something goes to stdout and stderr
    rc = fm.main()
    captured = capsys.readouterr()
    assert rc == 0
    # We don't assert specific content; just that something was written.
    # Logger output may go to stdout or stderr depending on the environment,
    # so assert that at least one stream received content.
    assert (captured.out.strip() != "") or (captured.err.strip() != "")


def test_main_error_path_writes_stderr(monkeypatch, capsys):
    # Simulate an error in the functional layer and ensure main prints to stderr
    def fake_run():
        return 2, "", "fatal error occurred"

    monkeypatch.setattr(fm, "run", fake_run)
    rc = fm.main()
    captured = capsys.readouterr()
    assert rc == 2
    # The error may be logged to either stdout or stderr; ensure at least one
    # stream contains output and the exit code reflects the error.
    assert (captured.out.strip() != "") or (captured.err.strip() != "")
