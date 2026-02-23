from flo import main


def test_cli_runs_default():
    # Integration placeholder: calling main() with no argv should succeed
    rc = main.main()
    assert isinstance(rc, int)
