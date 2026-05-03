from flo.pipeline import (
    PipelineRunner,
    ReadStep,
    ParseStep,
    CompileStep,
    ValidateStep,
    PostprocessStep,
    RenderStep,
    OutputStep,
)


def test_pipeline_runner_happy_path(monkeypatch):
    calls = []

    def fake_read_input(path):
        calls.append(("read", path))
        return 0, "content", None

    def fake_parse_adapter(content, source_path=None):
        calls.append(("parse", content))
        return {"model": True}

    def fake_compile_adapter(model):
        calls.append(("compile", model))
        return {"ir": True}

    def fake_validate_ir(ir):
        calls.append(("validate", ir))

    def fake_scc_condense(ir):
        calls.append(("post", ir))
        return {"ir": "condensed"}

    def fake_render_dot(ir):
        calls.append(("render", ir))
        return "dot-content"

    def fake_write_output(out, path):
        calls.append(("write", path))
        return 0, None

    monkeypatch.setattr("flo.pipeline.read_input", fake_read_input)
    monkeypatch.setattr("flo.pipeline.parse_adapter", fake_parse_adapter)
    monkeypatch.setattr("flo.pipeline.compile_adapter", fake_compile_adapter)
    monkeypatch.setattr("flo.pipeline.validate_ir", fake_validate_ir)
    monkeypatch.setattr("flo.pipeline.scc_condense", fake_scc_condense)
    monkeypatch.setattr("flo.pipeline.render_dot", fake_render_dot)
    monkeypatch.setattr("flo.pipeline.write_output", fake_write_output)

    steps = [
        ReadStep(path="file.flo"),
        ParseStep(),
        CompileStep(),
        ValidateStep(),
        PostprocessStep(),
        RenderStep(),
        OutputStep(options={}),
    ]

    runner = PipelineRunner(steps)
    rc = runner.run(services=None)

    assert rc == 0
    assert [c[0] for c in calls] == ["read", "parse", "compile", "validate", "post", "render", "write"]
