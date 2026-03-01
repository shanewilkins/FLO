from flo.services import get_services
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


def test_pipeline_integration_end_to_end(tmp_flo_file, tmp_path):
    services = get_services(verbose=True)

    out_path = tmp_path / "out.dot"

    steps = [
        ReadStep(path=str(tmp_flo_file)),
        ParseStep(),
        CompileStep(),
        ValidateStep(),
        PostprocessStep(),
        RenderStep(),
        OutputStep(options={"output": str(out_path)}),
    ]

    runner = PipelineRunner(steps)
    try:
        rc = runner.run(services=services)

        assert rc == 0
        assert out_path.exists()
        assert out_path.read_text()
    finally:
        # Ensure telemetry exporters are shutdown to avoid test-time warnings
        try:
            services.telemetry.shutdown()
        except Exception:
            pass
