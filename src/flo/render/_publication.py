"""Renderer-independent publication model contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PublicationRegionName = Literal["header", "body", "footer"]
PublicationBandName = Literal["header", "footer"]
PublicationSeriesKind = Literal["map", "child_map", "artifact"]
PublicationArtifactKind = Literal["child_map", "artifact"]


@dataclass(frozen=True)
class PublicationMargins:
    """Outer page margins, excluded from content-region geometry."""

    top_px: int = 48
    right_px: int = 48
    bottom_px: int = 48
    left_px: int = 48


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