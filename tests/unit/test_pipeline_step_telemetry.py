from flo.pipeline import PipelineRunner, ReadStep, ParseStep


class FakeSpan:
    def __init__(self, record):
        self.record = record

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, exc, _tb):
        return False

    def set_attribute(self, key, value):
        self.record.append((key, value))

    def add_event(self, name, attributes=None, **_):
        self.record.append(("event", name, attributes))


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

    def fake_parse_adapter(content, source_path=None):
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


def test_pipeline_step_degraded_event_on_fail_open(monkeypatch):
    record = []

    class DegradedStep:
        def run(self, _state, _services):
            return (0, {"ok": True}, "fail-open postprocess: scc_condense failed: boom")

    fake_tracer = FakeTracer(record)
    monkeypatch.setattr("flo.pipeline.get_tracer", lambda name: fake_tracer)

    runner = PipelineRunner([DegradedStep()])
    rc = runner.run(services=None)

    assert rc == 0
    assert ("pipeline.step.degraded", True) in record
    assert any(
        item[0] == "event" and item[1] == "pipeline.step.degraded"
        for item in record
        if isinstance(item, tuple) and len(item) >= 2
    )
