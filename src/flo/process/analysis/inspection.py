"""Stable model-inspection and projection-readiness reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from flo.process.ir.metadata import extract_node_metadata
from flo.process.ir.models import IR

from .movement import (
    extract_location_spatial_index,
    infer_material_movements,
    infer_people_movements,
)
from .structure import ProcessStructuralAnalysis, analyze_process_structure
from .timing import ProcessTimingAnalysis, analyze_process_timing
from .value_stream import project_value_stream


ReadinessStatus = Literal["ready", "partial", "unavailable"]
ReadinessFindingKind = Literal[
    "missing_required", "missing_optional", "limitation", "unsupported"
]


@dataclass(frozen=True)
class SourceCompositionSummary:
    """Portable entry and include composition for one inspected model."""

    entry_source: str
    included_sources: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "entry_source": self.entry_source,
            "included_sources": list(self.included_sources),
            "source_count": 1 + len(self.included_sources),
            "composed": bool(self.included_sources),
        }


@dataclass(frozen=True)
class EntitySummary:
    """Stable declared-entity IDs grouped by canonical collection."""

    item_ids: tuple[str, ...]
    resource_ids: tuple[str, ...]
    location_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return entity counts and IDs without duplicating entity payloads."""
        return {
            "items": {"count": len(self.item_ids), "ids": list(self.item_ids)},
            "resources": {
                "count": len(self.resource_ids),
                "ids": list(self.resource_ids),
            },
            "locations": {
                "count": len(self.location_ids),
                "ids": list(self.location_ids),
            },
        }


@dataclass(frozen=True)
class NamedViewSummary:
    """One default or named render-intent view available to the model."""

    view_id: str
    label: str | None
    diagram: str | None

    def as_dict(self) -> dict[str, str | None]:
        """Return a stable JSON-compatible representation."""
        return asdict(self)


@dataclass(frozen=True)
class ReadinessFinding:
    """One actionable reason a requested projection is partial or unavailable."""

    code: str
    kind: ReadinessFindingKind
    message: str
    ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "code": self.code,
            "kind": self.kind,
            "message": self.message,
            "ids": list(self.ids),
        }


@dataclass(frozen=True)
class ProjectionReadiness:
    """Readiness of one explicitly requested analysis or diagram."""

    target_type: Literal["analysis", "diagram"]
    target: str
    status: ReadinessStatus
    findings: tuple[ReadinessFinding, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "target_type": self.target_type,
            "target": self.target,
            "status": self.status,
            "findings": [finding.as_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class ModelInspectionReport:
    """Versioned model summary and requested projection-readiness result."""

    report_version: str
    process_id: str
    process_name: str
    process_version: int | str | None
    process_owner: dict[str, Any] | None
    business_unit_ids: tuple[str, ...]
    lane_ids: tuple[str, ...]
    node_count: int
    edge_count: int
    composition: SourceCompositionSummary
    entities: EntitySummary
    views: tuple[NamedViewSummary, ...]
    structure: ProcessStructuralAnalysis
    readiness: tuple[ProjectionReadiness, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return the stable JSON-compatible model-inspection schema."""
        return {
            "report_version": self.report_version,
            "validation_status": "valid",
            "process": {
                "id": self.process_id,
                "name": self.process_name,
                "version": self.process_version,
                "owner": self.process_owner,
                "business_unit_ids": list(self.business_unit_ids),
            },
            "composition": self.composition.as_dict(),
            "model_summary": {
                "node_count": self.node_count,
                "edge_count": self.edge_count,
                "lane_count": len(self.lane_ids),
                "lane_ids": list(self.lane_ids),
            },
            "entities": self.entities.as_dict(),
            "paths": {
                "count": len(self.structure.paths),
                "minimum_edge_count": self.structure.minimum_path_edge_count,
                "maximum_edge_count": self.structure.maximum_path_edge_count,
                "items": [path.as_dict() for path in self.structure.paths],
            },
            "views": [view.as_dict() for view in self.views],
            "readiness": [item.as_dict() for item in self.readiness],
            "diagnostics": [
                asdict(diagnostic) for diagnostic in self.structure.diagnostics
            ],
        }


def inspect_process_model(
    process: IR,
    *,
    entry_source: str = "<memory>",
    included_sources: tuple[str, ...] = (),
    requested_analysis: str | None = None,
    requested_diagram: str | None = None,
    supported_diagrams: tuple[str, ...] = (),
) -> ModelInspectionReport:
    """Build a deterministic report from validated canonical IR and sidecars."""
    if not isinstance(process, IR):
        raise TypeError("inspect_process_model requires canonical IR")

    structure = analyze_process_structure(process)
    process_metadata = process.process_metadata or {}
    process_id = _text(process_metadata.get("process_id")) or process.name
    process_name = _text(process_metadata.get("process_name")) or process.name
    readiness = _requested_readiness(
        process,
        structure=structure,
        requested_analysis=requested_analysis,
        requested_diagram=requested_diagram,
        supported_diagrams=frozenset(supported_diagrams),
    )
    return ModelInspectionReport(
        report_version="0.1",
        process_id=process_id,
        process_name=process_name,
        process_version=process.process_version,
        process_owner=process.process_owner,
        business_unit_ids=_identity_ids(process.business_units),
        lane_ids=_identity_ids(process.lanes),
        node_count=len(process.nodes),
        edge_count=len(process.edges),
        composition=SourceCompositionSummary(
            entry_source=entry_source,
            included_sources=tuple(sorted(set(included_sources))),
        ),
        entities=EntitySummary(
            item_ids=_entity_ids(process.items),
            resource_ids=_entity_ids(process.resources),
            location_ids=_entity_ids(process.locations),
        ),
        views=_named_views(process.render_intent),
        structure=structure,
        readiness=readiness,
    )


def _requested_readiness(
    process: IR,
    *,
    structure: ProcessStructuralAnalysis,
    requested_analysis: str | None,
    requested_diagram: str | None,
    supported_diagrams: frozenset[str],
) -> tuple[ProjectionReadiness, ...]:
    items: list[ProjectionReadiness] = []
    if requested_analysis:
        items.append(
            _analysis_readiness(
                process,
                structure=structure,
                requested_analysis=requested_analysis,
            )
        )
    if requested_diagram:
        items.append(
            _diagram_readiness(
                process,
                requested_diagram=requested_diagram,
                supported_diagrams=supported_diagrams,
            )
        )
    return tuple(items)


def _analysis_readiness(
    process: IR,
    *,
    structure: ProcessStructuralAnalysis,
    requested_analysis: str,
) -> ProjectionReadiness:
    if requested_analysis == "timing":
        return _timing_readiness(process, analyze_process_timing(process))
    if requested_analysis == "structure":
        findings = tuple(
            ReadinessFinding(
                code=diagnostic.code,
                kind="missing_optional"
                if diagnostic.code == "structure-unclassified-steps"
                else "limitation",
                message=diagnostic.message,
                ids=structure.unclassified_node_ids
                if diagnostic.code == "structure-unclassified-steps"
                else (),
            )
            for diagnostic in structure.diagnostics
            if diagnostic.severity == "warning"
        )
        return ProjectionReadiness(
            target_type="analysis",
            target="structure",
            status="partial" if findings else "ready",
            findings=findings,
        )
    return ProjectionReadiness(
        target_type="analysis",
        target=requested_analysis,
        status="unavailable",
        findings=(
            ReadinessFinding(
                code="readiness-analysis-unsupported",
                kind="unsupported",
                message=f"Analysis '{requested_analysis}' is not supported.",
            ),
        ),
    )


def _timing_readiness(
    process: IR, timing: ProcessTimingAnalysis
) -> ProjectionReadiness:
    if not _has_declared_timing(process):
        return ProjectionReadiness(
            target_type="analysis",
            target="timing",
            status="unavailable",
            findings=(
                ReadinessFinding(
                    code="readiness-timing-absent",
                    kind="missing_required",
                    message="No cycle, wait, or changeover timing is declared.",
                ),
            ),
        )
    findings = tuple(
        ReadinessFinding(
            code=diagnostic.code,
            kind="missing_required"
            if diagnostic.code == "timing-incomplete"
            else "limitation",
            message=diagnostic.message,
            ids=(diagnostic.node_id,) if diagnostic.node_id else (),
        )
        for diagnostic in timing.diagnostics
        if diagnostic.severity == "warning"
    )
    return ProjectionReadiness(
        target_type="analysis",
        target="timing",
        status="partial" if findings else "ready",
        findings=findings,
    )


def _diagram_readiness(
    process: IR,
    *,
    requested_diagram: str,
    supported_diagrams: frozenset[str],
) -> ProjectionReadiness:
    if requested_diagram not in supported_diagrams:
        return ProjectionReadiness(
            target_type="diagram",
            target=requested_diagram,
            status="unavailable",
            findings=(
                ReadinessFinding(
                    code="readiness-diagram-unsupported",
                    kind="unsupported",
                    message=f"Diagram '{requested_diagram}' is not currently supported.",
                ),
            ),
        )
    if requested_diagram == "spaghetti":
        return _spaghetti_readiness(process)
    if requested_diagram == "swimlane":
        return _swimlane_readiness(process)
    if requested_diagram == "value_stream":
        return _value_stream_readiness(process)
    return ProjectionReadiness(
        target_type="diagram",
        target=requested_diagram,
        status="ready",
    )


def _spaghetti_readiness(process: IR) -> ProjectionReadiness:
    routes = [
        *infer_material_movements(process),
        *infer_people_movements(process),
    ]
    if not routes:
        return ProjectionReadiness(
            target_type="diagram",
            target="spaghetti",
            status="unavailable",
            findings=(
                ReadinessFinding(
                    code="readiness-spaghetti-routes-absent",
                    kind="missing_required",
                    message="No material or people movement routes can be inferred.",
                ),
            ),
        )
    locations = extract_location_spatial_index(process)
    missing_ids = _unpositioned_route_locations(routes, locations=locations)
    if missing_ids:
        renderable_route_count = sum(
            _route_has_spatial_coordinates(route, locations=locations)
            for route in routes
        )
        return ProjectionReadiness(
            target_type="diagram",
            target="spaghetti",
            status="partial" if renderable_route_count else "unavailable",
            findings=(
                ReadinessFinding(
                    code="readiness-spaghetti-spatial-missing",
                    kind="missing_required",
                    message=(
                        "Spaghetti rendering omits routes without two positioned "
                        "endpoints; strict mode rejects them."
                    ),
                    ids=missing_ids,
                ),
            ),
        )
    return ProjectionReadiness(
        target_type="diagram",
        target="spaghetti",
        status="ready",
    )


def _swimlane_readiness(process: IR) -> ProjectionReadiness:
    if process.lanes:
        return ProjectionReadiness(
            target_type="diagram",
            target="swimlane",
            status="ready",
        )
    return ProjectionReadiness(
        target_type="diagram",
        target="swimlane",
        status="partial",
        findings=(
            ReadinessFinding(
                code="readiness-swimlane-lanes-absent",
                kind="missing_optional",
                message="No lanes are declared; nodes will use the fallback lane.",
            ),
        ),
    )


def _value_stream_readiness(process: IR) -> ProjectionReadiness:
    projection = project_value_stream(process)
    if not projection.nodes:
        return ProjectionReadiness(
            target_type="diagram",
            target="value_stream",
            status="unavailable",
            findings=(
                ReadinessFinding(
                    code="readiness-value-stream-nodes-absent",
                    kind="missing_required",
                    message="No process nodes are available for a value stream map.",
                ),
            ),
        )
    findings = tuple(
        ReadinessFinding(
            code=diagnostic.code,
            kind="missing_optional",
            message=diagnostic.message,
        )
        for diagnostic in projection.diagnostics
    )
    return ProjectionReadiness(
        target_type="diagram",
        target="value_stream",
        status="partial" if findings else "ready",
        findings=findings,
    )


def _named_views(render_intent: dict[str, Any] | None) -> tuple[NamedViewSummary, ...]:
    intent = render_intent if isinstance(render_intent, dict) else {}
    defaults = intent.get("defaults")
    default_mapping = defaults if isinstance(defaults, dict) else {}
    default_diagram = _text(default_mapping.get("diagram"))
    summaries = [
        NamedViewSummary(view_id="default", label="Default", diagram=default_diagram)
    ]
    views = intent.get("views")
    if not isinstance(views, dict):
        return tuple(summaries)
    for view_id in sorted(views):
        raw_view = views[view_id]
        if not isinstance(raw_view, dict):
            continue
        summaries.append(
            NamedViewSummary(
                view_id=str(view_id),
                label=_text(raw_view.get("label")),
                diagram=_text(raw_view.get("diagram")) or default_diagram,
            )
        )
    return tuple(summaries)


def _entity_ids(collection: object) -> tuple[str, ...]:
    found: set[str] = set()

    def collect(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                collect(item)
            return
        if not isinstance(value, dict):
            return
        entity_id = _text(value.get("id"))
        if entity_id:
            found.add(entity_id)
        for key, child in value.items():
            if key not in {"id", "name", "kind", "metadata", "quantity"}:
                collect(child)

    collect(collection)
    return tuple(sorted(found))


def _identity_ids(values: list[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                identity
                for value in values
                if (identity := _text(value.get("id"))) is not None
            }
        )
    )


def _has_declared_timing(process: IR) -> bool:
    timing_fields = {
        "cycle_time",
        "wait_time",
        "crossover_time",
        "transfer_time",
        "changeover_time",
    }
    return any(
        timing_fields.intersection(extract_node_metadata(node))
        for node in process.nodes
    )


def _unpositioned_route_locations(
    routes: list[dict[str, Any]],
    *,
    locations: dict[str, dict[str, Any]],
) -> tuple[str, ...]:
    route_location_ids = {
        location_id
        for route in routes
        for key in ("from_location", "to_location")
        if (location_id := _text(route.get(key))) is not None
    }
    return tuple(
        sorted(
            location_id
            for location_id in route_location_ids
            if not _has_spatial_coordinates(locations.get(location_id))
        )
    )


def _has_spatial_coordinates(info: dict[str, Any] | None) -> bool:
    if not isinstance(info, dict):
        return False
    return isinstance(info.get("x"), (int, float)) and isinstance(
        info.get("y"), (int, float)
    )


def _route_has_spatial_coordinates(
    route: dict[str, Any], *, locations: dict[str, dict[str, Any]]
) -> bool:
    source = _text(route.get("from_location"))
    target = _text(route.get("to_location"))
    return bool(
        source
        and target
        and _has_spatial_coordinates(locations.get(source))
        and _has_spatial_coordinates(locations.get(target))
    )


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
