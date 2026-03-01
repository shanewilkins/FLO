from flo.pipeline import ReadStep


def test_readstep_calls_read_input(monkeypatch):
    called = {}

    def fake_read_input(path):
        called['path'] = path
        return 0, "fake-content", None

    monkeypatch.setattr("flo.pipeline.read_input", fake_read_input)

    step = ReadStep(path="somefile.flo")
    result = step.run(None, services=None)

    assert result == (0, "fake-content", None)
    assert called["path"] == "somefile.flo"
