"""Renderer-independent publication model contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PublicationRegionName = Literal["header", "body", "footer"]
PublicationBandName = Literal["header", "footer"]
PublicationSeriesKind = Literal["map", "child_map", "artifact"]
PublicationArtifactKind = Literal["child_map", "artifact"]
PublicationPageFormatName = Literal["letter", "a4", "legal", "tabloid"]
PublicationDiagnosticSeverity = Literal["warning", "error"]


@dataclass(frozen=True)
class PublicationMargins:
    """Outer page margins, excluded from content-region geometry."""

    top_px: int = 48
    right_px: int = 48
    bottom_px: int = 48
    left_px: int = 48


@dataclass(frozen=True)
class PublicationPageFormat:
    """Named page-size preset with shared geometry defaults."""

    name: PublicationPageFormatName
    width_px: int
    height_px: int
    margins: PublicationMargins


@dataclass(frozen=True)
class PublicationDiagnostic:
    """A reusable readability or fallback diagnostic for publication output."""

    code: str
    severity: PublicationDiagnosticSeverity
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


_PAGE_FORMAT_PRESETS: dict[str, PublicationPageFormat] = {
    "letter": PublicationPageFormat(
        name="letter",
        width_px=816,
        height_px=1056,
        margins=PublicationMargins(top_px=48, right_px=48, bottom_px=48, left_px=48),
    ),
    "a4": PublicationPageFormat(
        name="a4",
        width_px=794,
        height_px=1123,
        margins=PublicationMargins(top_px=48, right_px=48, bottom_px=48, left_px=48),
    ),
    "legal": PublicationPageFormat(
        name="legal",
        width_px=816,
        height_px=1344,
        margins=PublicationMargins(top_px=48, right_px=48, bottom_px=48, left_px=48),
    ),
    "tabloid": PublicationPageFormat(
        name="tabloid",
        width_px=1056,
        height_px=1632,
        margins=PublicationMargins(top_px=48, right_px=48, bottom_px=48, left_px=48),
    ),
}

_PAGE_FORMAT_ALIASES = {
    "us-letter": "letter",
    "us_legal": "legal",
    "ledger": "tabloid",
}


@dataclass(frozen=True)
class PublicationBounds:
    """Declared bounds for a publication page or canvas."""

    width_px: int | None = None
    height_px: int | None = None


@dataclass(frozen=True)
class PublicationRegion:
    """Named content surface within the usable page canvas."""

    name: PublicationRegionName
    x_px: int | None
    y_px: int | None
    width_px: int | None
    height_px: int | None


@dataclass(frozen=True)
class PublicationCanvas:
    """Page canvas with margins, usable bounds, and named content regions."""

    bounds: PublicationBounds
    margins: PublicationMargins
    usable_region: PublicationRegion
    regions: tuple[PublicationRegion, ...]

    def region(self, name: PublicationRegionName) -> PublicationRegion:
        """Return the named region or raise when it does not exist."""
        for region in self.regions:
            if region.name == name:
                return region
        raise KeyError(name)


@dataclass(frozen=True)
class PublicationBandContent:
    """Semantic content that a renderer can place in a document band."""

    title: str = ""
    rows: tuple[tuple[str, str], ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PublicationBand:
    """Shared top or bottom document band bound to a named content region."""

    name: PublicationBandName
    region: PublicationRegion
    content: PublicationBandContent


@dataclass(frozen=True)
class PublicationPageSpec:
    """Declarative page input used to materialize a publication series."""

    page_key: str
    canvas: PublicationCanvas
    header_content: PublicationBandContent | None = None
    footer_content: PublicationBandContent | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicationPage:
    """One page within a publication series."""

    page_id: str
    page_number: int
    series_id: str
    canvas: PublicationCanvas
    bands: tuple[PublicationBand, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def band(self, name: PublicationBandName) -> PublicationBand | None:
        """Return the named document band when it is present on the page."""
        for band in self.bands:
            if band.name == name:
                return band
        return None


@dataclass(frozen=True)
class PublicationSeries:
    """Ordered page series for one top-level or child artifact."""

    series_id: str
    title: str
    kind: PublicationSeriesKind
    pages: tuple[PublicationPage, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicationArtifactSlot:
    """Reserved slot for a child map or later publication artifact."""

    slot_id: str
    title: str
    kind: PublicationArtifactKind
    parent_series_id: str
    source_node_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicationPlan:
    """Renderer-independent publication plan above IR and below output syntax."""

    title: str
    primary_series_id: str
    series: tuple[PublicationSeries, ...]
    artifact_slots: tuple[PublicationArtifactSlot, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def primary_series(self) -> PublicationSeries:
        """Return the primary publication series for the plan."""
        for series in self.series:
            if series.series_id == self.primary_series_id:
                return series
        raise KeyError(self.primary_series_id)


def materialize_publication_series(
    *,
    series_id: str,
    title: str,
    kind: PublicationSeriesKind,
    page_specs: tuple[PublicationPageSpec, ...] | list[PublicationPageSpec],
    metadata: dict[str, Any] | None = None,
) -> PublicationSeries:
    """Build a concrete page series with deterministic page ids and metadata."""
    normalized_specs = tuple(page_specs)
    pages: list[PublicationPage] = []
    page_count = len(normalized_specs)

    for idx, spec in enumerate(normalized_specs, start=1):
        page_id = _publication_page_id(series_id=series_id, page_key=spec.page_key, page_number=idx)
        page_metadata = {
            **spec.metadata,
            "series_id": series_id,
            "page_id": page_id,
            "page_number": idx,
            "page_count": page_count,
        }
        pages.append(
            PublicationPage(
                page_id=page_id,
                page_number=idx,
                series_id=series_id,
                canvas=spec.canvas,
                bands=build_publication_bands(
                    canvas=spec.canvas,
                    header_content=spec.header_content,
                    footer_content=spec.footer_content,
                ),
                metadata=page_metadata,
            )
        )

    series_metadata = {**(metadata or {}), "page_count": page_count}
    return PublicationSeries(
        series_id=series_id,
        title=title,
        kind=kind,
        pages=tuple(pages),
        metadata=series_metadata,
    )


def _publication_page_id(*, series_id: str, page_key: str, page_number: int) -> str:
    normalized_key = str(page_key).strip()
    if normalized_key:
        return f"{series_id}-{normalized_key}"
    return f"{series_id}-p{page_number}"


def resolve_publication_page_format(name: str) -> PublicationPageFormat:
    """Return the named page-format preset or raise for unsupported names."""
    normalized = str(name).strip().lower()
    canonical = _PAGE_FORMAT_ALIASES.get(normalized, normalized)
    preset = _PAGE_FORMAT_PRESETS.get(canonical)
    if preset is None:
        supported = ", ".join(sorted(_PAGE_FORMAT_PRESETS))
        raise ValueError(f"Unsupported publication_page_format '{name}'. Supported formats: {supported}.")
    return preset


def build_publication_canvas_for_format(
    *,
    page_format: str,
    header_height_px: int = 0,
    footer_height_px: int = 0,
    width_px_override: int | None = None,
) -> PublicationCanvas:
    """Build a page canvas from a shared named page-format preset."""
    preset = resolve_publication_page_format(page_format)
    return build_publication_canvas(
        bounds=PublicationBounds(width_px=width_px_override or preset.width_px, height_px=preset.height_px),
        margins=preset.margins,
        header_height_px=header_height_px,
        footer_height_px=footer_height_px,
    )


def evaluate_publication_fallback(
    *,
    requested_mode: str,
    effective_mode: str,
    fallback_reason: str | None,
    strict: bool,
) -> tuple[PublicationDiagnostic, ...]:
    """Translate a publication fallback into warning or error diagnostics."""
    if fallback_reason is None or requested_mode == effective_mode:
        return ()

    severity: PublicationDiagnosticSeverity = "error" if strict else "warning"
    reason_text = fallback_reason.replace("-", " ")
    return (
        PublicationDiagnostic(
            code="publication-fallback",
            severity=severity,
            message=(
                f"Requested publication mode '{requested_mode}' fell back to '{effective_mode}' "
                f"because {reason_text}."
            ),
            metadata={
                "requested_mode": requested_mode,
                "effective_mode": effective_mode,
                "fallback_reason": fallback_reason,
                "strict": strict,
            },
        ),
    )


def build_publication_canvas(
    *,
    bounds: PublicationBounds,
    margins: PublicationMargins,
    header_height_px: int = 0,
    footer_height_px: int = 0,
) -> PublicationCanvas:
    """Build usable page geometry and named content regions from bounds and margins."""
    usable_x = margins.left_px
    usable_y = margins.top_px
    usable_width = None
    if bounds.width_px is not None:
        usable_width = max(0, bounds.width_px - margins.left_px - margins.right_px)

    usable_height = None
    if bounds.height_px is not None:
        usable_height = max(0, bounds.height_px - margins.top_px - margins.bottom_px)

    body_y = usable_y + header_height_px
    body_height = None
    if usable_height is not None:
        body_height = max(0, usable_height - header_height_px - footer_height_px)

    footer_y = None
    if usable_height is not None:
        footer_y = usable_y + usable_height - footer_height_px

    usable_region = PublicationRegion(
        name="body",
        x_px=usable_x,
        y_px=usable_y,
        width_px=usable_width,
        height_px=usable_height,
    )
    return PublicationCanvas(
        bounds=bounds,
        margins=margins,
        usable_region=usable_region,
        regions=(
            PublicationRegion(
                name="header",
                x_px=usable_x,
                y_px=usable_y,
                width_px=usable_width,
                height_px=header_height_px,
            ),
            PublicationRegion(
                name="body",
                x_px=usable_x,
                y_px=body_y,
                width_px=usable_width,
                height_px=body_height,
            ),
            PublicationRegion(
                name="footer",
                x_px=usable_x,
                y_px=footer_y,
                width_px=usable_width,
                height_px=footer_height_px,
            ),
        ),
    )


def build_publication_bands(
    *,
    canvas: PublicationCanvas,
    header_content: PublicationBandContent | None = None,
    footer_content: PublicationBandContent | None = None,
) -> tuple[PublicationBand, ...]:
    """Build shared band objects for populated top and bottom document regions."""
    bands: list[PublicationBand] = []
    if header_content is not None:
        bands.append(PublicationBand(name="header", region=canvas.region("header"), content=header_content))
    if footer_content is not None:
        bands.append(PublicationBand(name="footer", region=canvas.region("footer"), content=footer_content))
    return tuple(bands)