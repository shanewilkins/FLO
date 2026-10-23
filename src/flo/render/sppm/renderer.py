"""SPPM production orchestration from engine layout through routed geometry to SVG."""

from copy import deepcopy
from dataclasses import replace
from typing import Any

from flo.process.analysis import ProcessTimingAnalysis

from .._artifact import RenderArtifact
from .._diagnostics import build_render_diagnostics_report, log_render_diagnostics
from .._execution import GeometryObserver, SceneObserver
from ..layout_core.elk import execute_elk_layout
from ..layout_core.elk_contracts import ElkLayoutRequest
from ..layout_core.elk_runtime import run_elkjs_layout
from ..layout_core.models import LayoutResult
from ..layout_core.trace import LayoutObserver
from ..options import RenderOptions
from .geometry import finalize_sppm_geometry
from .layout import build_sppm_elk_layout_request
from .scene import finalize_sppm_scene
from .svg import emit_sppm_svg_artifact


def render_sppm_svg_artifact(
    process: Any,
    options: RenderOptions,
    *,
    layout_observer: LayoutObserver | None = None,
    geometry_observer: GeometryObserver | None = None,
    scene_observer: SceneObserver | None = None,
) -> tuple[RenderArtifact, None]:
    """Run the diagram-owned production sequence and optionally observe its stages."""
    request = build_sppm_elk_layout_request(process, options=options)
    if layout_observer is None:
        result = execute_elk_layout(request, engine=run_elkjs_layout)
    else:
        result = execute_elk_layout(
            request, engine=run_elkjs_layout, observer=layout_observer
        )
    return render_sppm_svg_artifact_from_layout(
        process=process,
        options=options,
        request=request,
        result=result,
        geometry_observer=geometry_observer,
        scene_observer=scene_observer,
    )


def render_sppm_svg_artifact_from_layout(
    *,
    process: Any,
    options: RenderOptions,
    request: ElkLayoutRequest,
    result: LayoutResult,
    timing_analysis: ProcessTimingAnalysis | None = None,
    geometry_observer: GeometryObserver | None = None,
    scene_observer: SceneObserver | None = None,
) -> tuple[RenderArtifact, None]:
    """Finalize a precomputed engine stage and emit SVG, without viewport resolution.

    Complete artifact consumers use ``flo.render.render_execution`` instead.
    """
    geometry = finalize_sppm_geometry(result)
    if geometry_observer is not None:
        geometry_observer(replace(geometry, diagnostics=deepcopy(geometry.diagnostics)))
    scene = finalize_sppm_scene(
        process=process,
        options=options,
        request=request,
        geometry=geometry,
        timing_analysis=timing_analysis,
    )
    log_render_diagnostics(
        build_render_diagnostics_report(
            scene.diagnostics,
            diagram="sppm",
            backend="svg",
            artifact_kind="svg",
            strict=options.layout_fit == "fit-strict",
        )
    )
    if scene_observer is not None:
        scene_observer(
            replace(
                scene,
                routed=replace(geometry, diagnostics=deepcopy(geometry.diagnostics)),
                diagnostics=deepcopy(scene.diagnostics),
            )
        )
    return emit_sppm_svg_artifact(
        process=process, options=options, request=request, scene=scene
    )
