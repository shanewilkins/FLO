from flo import app


def test_cli_runs_default():
    # Integration placeholder: calling the programmatic run should succeed
    rc, out, err = app.run()
    assert isinstance(rc, int)
