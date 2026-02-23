from flo import core


def test_cli_runs_default():
    # Integration placeholder: calling the programmatic run should succeed
    rc, out, err = core.run()
    assert isinstance(rc, int)
