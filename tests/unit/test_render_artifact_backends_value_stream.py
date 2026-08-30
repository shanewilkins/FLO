from flo.render import render_artifact

from tests.unit.analysis.test_value_stream import _dual_flow_process


def test_value_stream_svg_is_deterministic_and_distinguishes_both_flows() -> None:
    process = _dual_flow_process()

    artifact = render_artifact(process, options={"diagram": "value_stream"})
    rerun = render_artifact(process, options={"diagram": "value_stream"})

    assert artifact.content == rerun.content
    assert 'data-flo-diagram="value_stream"' in artifact.content
    assert 'data-flow-kind="information"' in artifact.content
    assert 'data-flow-kind="material"' in artifact.content
    assert 'data-item-id="ticket"' in artifact.content
    assert "CT 5 min" in artifact.content
    assert "WT 10 min" in artifact.content
    assert "C/O 2 min" in artifact.content
    assert "Modeled lead time: 21 min" in artifact.content
    assert 'data-flo-notice="partial-map"' not in artifact.content
    assert artifact.metadata == {
        "diagram": "value_stream",
        "partial": False,
    }


def test_value_stream_svg_marks_information_only_output_as_partial() -> None:
    process = _dual_flow_process()
    process.items = [item for item in process.items if item["kind"] == "information"]

    artifact = render_artifact(process, options={"diagram": "value_stream"})
    rerun = render_artifact(process, options={"diagram": "value_stream"})

    assert artifact.content == rerun.content
    assert 'data-flow-kind="information"' in artifact.content
    assert 'data-flow-kind="material"' not in artifact.content
    assert 'data-flo-notice="partial-map"' in artifact.content
    assert "no declared material flow" in artifact.content
    assert artifact.metadata["partial"] is True
    assert artifact.metadata["warning"] == (
        "value-stream-partial: value-stream-material-absent"
    )


def test_value_stream_svg_marks_material_only_output_as_partial() -> None:
    process = _dual_flow_process()
    process.items = [item for item in process.items if item["kind"] == "material"]

    artifact = render_artifact(process, options={"diagram": "value_stream"})
    rerun = render_artifact(process, options={"diagram": "value_stream"})

    assert artifact.content == rerun.content
    assert 'data-flow-kind="material"' in artifact.content
    assert 'data-flow-kind="information"' not in artifact.content
    assert "no declared information flow" in artifact.content
    assert artifact.metadata["warning"] == (
        "value-stream-partial: value-stream-information-absent"
    )


def test_value_stream_svg_discloses_missing_optional_metrics() -> None:
    process = _dual_flow_process()
    for node in process.nodes:
        if node.type in {"task", "queue"}:
            node.attrs["metadata"] = {}

    artifact = render_artifact(process, options={"diagram": "value_stream"})
    rerun = render_artifact(process, options={"diagram": "value_stream"})

    assert artifact.content == rerun.content
    assert "CT —" in artifact.content
    assert "WT —" in artifact.content
    assert "C/O —" in artifact.content
    assert "Modeled lead time: not derivable" in artifact.content
