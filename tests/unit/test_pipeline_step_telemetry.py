import time

from types import SimpleNamespace

from flo.pipeline import PipelineRunner, ReadStep, ParseStep


class FakeSpan:
    def __init__(self, record):
        self.record = record

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def set_attribute(self, key, value):
        self.record.append((key, value))


class FakeTracer:
    def __init__(self, record):
        self.record = record

    def start_as_current_span(self, name):
        self.record.append(("span.started", name))
        return FakeSpan(self.record)


def test_per_step_spans(monkeypatch):
    record = []

    def fake_read_input(path):
        return 0, "content", None

    def fake_parse_adapter(content):
        return {"model": True}

    monkeypatch.setattr("flo.pipeline.read_input", fake_read_input)
    monkeypatch.setattr("flo.pipeline.parse_adapter", fake_parse_adapter)

    fake_tracer = FakeTracer(record)
    monkeypatch.setattr("flo.pipeline.get_tracer", lambda name: fake_tracer)

    steps = [ReadStep(path="file.flo"), ParseStep()]
    runner = PipelineRunner(steps)

    rc = runner.run(services=None)
    assert rc == 0
    # ensure spans started and attributes set for each step
    assert ("span.started", "pipeline.step.ReadStep") in record
    assert ("span.started", "pipeline.step.ParseStep") in record
    # verify at least one attribute was set for a step
    assert any(k == "pipeline.step.rc" for k, _ in record if isinstance(k, str))
