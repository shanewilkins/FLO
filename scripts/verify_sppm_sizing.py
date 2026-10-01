#!/usr/bin/env python3
"""SPPM sizing verification script.

Audits rendered SPPM SVG output against intended dimensions and reports
rendered approximations.

This script consumes FLO's shared dimension model (`px`, `in`, `cm`) so the
verification workflow stays aligned with render/layout option semantics.

Usage:
    python scripts/verify_sppm_sizing.py renders/reference/washnfold.svg [--dpi 96]

Exit codes:
    0 = All checks passed
    1 = Some dimensions out of spec
    2 = Error parsing file or arguments
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple
from xml.etree import ElementTree as ET

from flo.render.options import Dimension, parse_dimension


class DimensionSpec(NamedTuple):
    """Dimension specification with tolerance."""

    value: float  # in pixels
    tolerance: float
    unit: str  # "px" or "diameter"

    def check(self, actual: float) -> bool:
        """Check if actual value is within spec ± tolerance."""
        return abs(actual - self.value) <= self.tolerance


class SizingSpec:
    """SPPM spec dimensions at a given DPI."""

    def __init__(
        self,
        *,
        dpi: int = 96,
        process_box_width: str = "1.5in",
        process_box_height: str = "0.6in",
        data_box_width: str = "1.5in",
        data_box_height: str = "0.4in",
        queue_circle_min: str = "0.5in",
        queue_circle_max: str = "0.7in",
        spacing_h: str = "0.2in",
        spacing_v: str = "0.3in",
    ):
        """Initialize specs at given DPI.

        Input dimensions are parsed through FLO's shared dimension model.
        """
        self.dpi = dpi
        self.px_scale = dpi / 96.0

        # Preserve intended dimension inputs for clearer reporting.
        self.process_box_width_input = process_box_width
        self.process_box_height_input = process_box_height
        self.data_box_width_input = data_box_width
        self.data_box_height_input = data_box_height
        self.queue_circle_min_input = queue_circle_min
        self.queue_circle_max_input = queue_circle_max
        self.spacing_h_input = spacing_h
        self.spacing_v_input = spacing_v

        # Process step box
        self.process_box_width = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(process_box_width), dpi),
            tolerance=5,
            unit="px",
        )
        self.process_box_height = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(process_box_height), dpi),
            tolerance=5,
            unit="px",
        )

        # Data box
        self.data_box_width = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(data_box_width), dpi),
            tolerance=5,
            unit="px",
        )
        self.data_box_height = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(data_box_height), dpi),
            tolerance=5,
            unit="px",
        )

        # Queue circle diameter range
        self.queue_circle_min = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(queue_circle_min), dpi),
            tolerance=2,
            unit="diameter",
        )
        self.queue_circle_max = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(queue_circle_max), dpi),
            tolerance=2,
            unit="diameter",
        )

        # Spacing
        self.spacing_h = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(spacing_h), dpi),
            tolerance=3,
            unit="px",
        )
        self.spacing_v = DimensionSpec(
            value=_scaled_px(_parse_required_dimension(spacing_v), dpi),
            tolerance=3,
            unit="px",
        )


def _parse_required_dimension(value: str) -> Dimension:
    parsed = parse_dimension(value)
    if parsed is None:
        raise ValueError(
            "Invalid dimension value '"
            f"{value}'"
            "; expected positive dimension with px, in, or cm"
        )
    return parsed


def _scaled_px(dimension: Dimension, dpi: int) -> float:
    """Convert shared dimension to pixel target at selected DPI."""
    base_px = float(dimension.to_px())
    return base_px * (dpi / 96.0)


class SVGElement(NamedTuple):
    """Parsed SVG element with bounds."""

    elem_id: str | None
    elem_type: str  # "rect", "circle", "polygon", "text"
    x: float
    y: float
    width: float | None
    height: float | None
    radius: float | None


def parse_polygon_bounds(points_str: str) -> tuple[float, float, float, float]:
    """Parse SVG polygon points string and return bounding box (x, y, w, h).

    Points format: "x1,y1 x2,y2 x3,y3 ..."
    """
    points = []
    for point_pair in points_str.split():
        try:
            x, y = point_pair.split(",")
            points.append((float(x), float(y)))
        except ValueError, AttributeError:
            continue

    if not points:
        return 0, 0, 0, 0

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x
    height = max_y - min_y
    return min_x, min_y, width, height


def extract_svg_dimensions(svg_path: Path) -> list[SVGElement]:
    """Parse SVG file and extract element dimensions."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing SVG: {e}")
        return []

    elements = []

    # Extract rectangles
    for rect in _iter_svg_elements(root, "rect"):
        elem_id = rect.get("id")
        x = float(rect.get("x", 0))
        y = float(rect.get("y", 0))
        width = float(rect.get("width", 0))
        height = float(rect.get("height", 0))
        elements.append(
            SVGElement(
                elem_id=elem_id,
                elem_type="rect",
                x=x,
                y=y,
                width=width,
                height=height,
                radius=None,
            )
        )

    # Extract circles
    for circle in _iter_svg_elements(root, "circle"):
        elem_id = circle.get("id")
        cx = float(circle.get("cx", 0))
        cy = float(circle.get("cy", 0))
        r = float(circle.get("r", 0))
        diameter = r * 2
        elements.append(
            SVGElement(
                elem_id=elem_id,
                elem_type="circle",
                x=cx - r,
                y=cy - r,
                width=diameter,
                height=diameter,
                radius=r,
            )
        )

    # Extract ellipses
    for ellipse in _iter_svg_elements(root, "ellipse"):
        elem_id = ellipse.get("id")
        cx = float(ellipse.get("cx", 0))
        cy = float(ellipse.get("cy", 0))
        rx = float(ellipse.get("rx", 0))
        ry = float(ellipse.get("ry", 0))
        elements.append(
            SVGElement(
                elem_id=elem_id,
                elem_type="ellipse",
                x=cx - rx,
                y=cy - ry,
                width=rx * 2,
                height=ry * 2,
                radius=None,
            )
        )

    # Extract polygons (for table cells in SPPM)
    for polygon in _iter_svg_elements(root, "polygon"):
        elem_id = polygon.get("id")
        points_str = polygon.get("points", "")
        x, y, width, height = parse_polygon_bounds(points_str)
        elements.append(
            SVGElement(
                elem_id=elem_id,
                elem_type="polygon",
                x=x,
                y=y,
                width=width,
                height=height,
                radius=None,
            )
        )

    return elements


def _iter_svg_elements(root: ET.Element, tag: str):
    """Yield elements by local name regardless of namespace form."""
    for element in root.iter():
        if _local_name(element.tag) == tag:
            yield element


def _local_name(tag: str) -> str:
    """Return tag local name from namespaced or plain XML tags."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _content_elements(elements: list[SVGElement]) -> list[SVGElement]:
    content_elements = []
    for element in elements:
        if element.elem_id and (
            element.elem_id.startswith("__flo_canvas")
            or element.elem_id.startswith("__sppm")
        ):
            continue
        content_elements.append(element)

    seen_keys: set[tuple[object, ...]] = set()
    unique_elements: list[SVGElement] = []
    for element in content_elements:
        key = (
            element.elem_id,
            element.elem_type,
            round(element.x, 3),
            round(element.y, 3),
            round(element.width or 0, 3),
            round(element.height or 0, 3),
        )
        if key in seen_keys:
            continue
        unique_elements.append(element)
        seen_keys.add(key)
    return unique_elements


def _build_report_header(*, svg_path: Path, dpi: int, spec: SizingSpec) -> list[str]:
    return [
        f"\n{'SPPM Sizing Verification':^60}",
        "=" * 60,
        f"SVG File: {svg_path.name}",
        f"DPI: {dpi}",
        "Spec inputs (shared dimension model):",
        f"  Process Box: {spec.process_box_width_input} W × {spec.process_box_height_input} H",
        f"  Data Box: {spec.data_box_width_input} W × {spec.data_box_height_input} H",
        f"  Queue Circle: {spec.queue_circle_min_input}–{spec.queue_circle_max_input} diameter",
        f"  Spacing (H): {spec.spacing_h_input}",
        f"  Spacing (V): {spec.spacing_v_input}",
        f"Derived pixel targets (at {dpi} DPI):",
        f"  Process Box: {spec.process_box_width.value:.1f}px W × {spec.process_box_height.value:.1f}px H (±{spec.process_box_width.tolerance}px)",
        f"  Data Box: {spec.data_box_width.value:.1f}px W × {spec.data_box_height.value:.1f}px H (±{spec.data_box_width.tolerance}px)",
        f"  Queue Circle: {spec.queue_circle_min.value:.1f}–{spec.queue_circle_max.value:.1f}px diameter",
        f"  Spacing (H): {spec.spacing_h.value:.1f}px (±{spec.spacing_h.tolerance}px)",
        f"  Spacing (V): {spec.spacing_v.value:.1f}px (±{spec.spacing_v.tolerance}px)",
        f"\n{'Element ID':<20} {'Type':<12} {'Width':<12} {'Height':<12} {'Status':<15}",
        "-" * 71,
    ]


def _rectangle_status(rect: SVGElement, spec: SizingSpec) -> tuple[str, bool]:
    status = "✓"
    passed = True
    if not rect.width or not rect.height:
        return (status, passed)

    aspect_ratio = rect.width / rect.height if rect.height > 0 else 0
    width_spec = spec.data_box_width if aspect_ratio > 2 else spec.process_box_width
    height_spec = spec.data_box_height if aspect_ratio > 2 else spec.process_box_height

    if not width_spec.check(rect.width):
        status = "✗ W out of spec"
        passed = False
    if not height_spec.check(rect.height):
        status = "✗ H out of spec" if status == "✓" else "✗ W,H out of spec"
        passed = False
    return (status, passed)


def _circle_status(circle: SVGElement, spec: SizingSpec) -> tuple[str, bool]:
    diameter = circle.width or 0
    min_diameter = spec.queue_circle_min.value - spec.queue_circle_min.tolerance
    max_diameter = spec.queue_circle_max.value + spec.queue_circle_max.tolerance
    if diameter < min_diameter:
        return (f"✗ Too small ({diameter:.1f}px)", False)
    if diameter > max_diameter:
        return (f"✗ Too large ({diameter:.1f}px)", False)
    return ("✓", True)


def _append_rectangle_report(
    report: list[str], rectangles: list[SVGElement], spec: SizingSpec
) -> bool:
    all_passed = True
    for rect in rectangles:
        elem_id = rect.elem_id or "(no id)"
        status, passed = _rectangle_status(rect, spec)
        all_passed = all_passed and passed
        report.append(
            f"{elem_id:<20} {'rect':<12} {rect.width or 0:<12.1f} {rect.height or 0:<12.1f} {status:<15}"
        )
    return all_passed


def _append_circle_report(
    report: list[str], circles: list[SVGElement], spec: SizingSpec
) -> bool:
    all_passed = True
    for circle in circles:
        elem_id = circle.elem_id or "(queue circle)"
        diameter = circle.width or 0
        status, passed = _circle_status(circle, spec)
        all_passed = all_passed and passed
        report.append(
            f"{elem_id:<20} {circle.elem_type:<12} {diameter:<12.1f} {'-':<12} {status:<15}"
        )
    return all_passed


def _append_polygon_report(report: list[str], polygons: list[SVGElement]) -> None:
    if not polygons:
        return
    report.append(f"\n{'Polygon Elements (Graphviz HTML Table Cells):':<60}")
    report.append(
        "  Note: SPPM nodes use HTML-like tables (polygons) for complex labels."
    )
    report.append("  Individual cell dimensions vary; expected ranges:")
    report.append("    - Colored header: ~140px W × 35–40px H (process name + color)")
    report.append("    - Data rows: ~120–140px W × 35–40px H (CT/WT/Workers)")
    report.append("    - Spacer cells: ~10px W × varies H\n")
    for polygon in polygons[:10]:
        elem_id = polygon.elem_id or f"poly_?_{polygon.x:.0f}_{polygon.y:.0f}"
        report.append(
            f"{elem_id:<20} {'polygon':<12} {polygon.width or 0:<12.1f} {polygon.height or 0:<12.1f} {'~ (cell)':<15}"
        )
    if len(polygons) > 10:
        report.append(f"... and {len(polygons) - 10} more polygons")


def _circles_within_spec(circles: list[SVGElement], spec: SizingSpec) -> bool:
    return all(_circle_status(circle, spec)[1] for circle in circles)


def _append_summary(
    report: list[str],
    *,
    all_passed: bool,
    rectangles: list[SVGElement],
    circles: list[SVGElement],
    polygons: list[SVGElement],
    spec: SizingSpec,
) -> None:
    report.append(f"\n{'-' * 71}")
    report.append("\nSummary:")
    report.append(f"  Rectangles checked: {len(rectangles)}")
    circle_summary = (
        "✓ all within spec"
        if _circles_within_spec(circles, spec)
        else "⚠ some out of spec"
    )
    report.append(f"  Circles/ellipses: {len(circles)} ({circle_summary})")
    report.append(f"  Polygons (table cells): {len(polygons)} (requires manual review)")
    report.append(
        "  Note: SVG geometry reflects rendered approximations from Graphviz/DOT layout."
    )
    report.append(
        "        This check compares those approximations against intended dimensions."
    )
    if all_passed:
        report.append("\n✓ All dimensional checks passed.\n")
    else:
        report.append("\n✗ Some dimensions out of spec. Review rectangles above.\n")


def verify_sizing(
    svg_path: Path,
    *,
    dpi: int = 96,
    process_box_width: str = "1.5in",
    process_box_height: str = "0.6in",
    data_box_width: str = "1.5in",
    data_box_height: str = "0.4in",
    queue_circle_min: str = "0.5in",
    queue_circle_max: str = "0.7in",
    spacing_h: str = "0.2in",
    spacing_v: str = "0.3in",
) -> tuple[bool, list[str]]:
    """Verify SVG sizing against SPPM spec."""
    try:
        spec = SizingSpec(
            dpi=dpi,
            process_box_width=process_box_width,
            process_box_height=process_box_height,
            data_box_width=data_box_width,
            data_box_height=data_box_height,
            queue_circle_min=queue_circle_min,
            queue_circle_max=queue_circle_max,
            spacing_h=spacing_h,
            spacing_v=spacing_v,
        )
    except ValueError as exc:
        return False, [str(exc)]

    elements = extract_svg_dimensions(svg_path)
    if not elements:
        return False, ["No SVG elements found."]

    unique_elements = _content_elements(elements)
    circles = [
        element
        for element in unique_elements
        if element.elem_type in ("circle", "ellipse")
    ]
    rectangles = [element for element in unique_elements if element.elem_type == "rect"]
    polygons = [
        element for element in unique_elements if element.elem_type == "polygon"
    ]

    report = _build_report_header(svg_path=svg_path, dpi=dpi, spec=spec)
    rectangles_ok = _append_rectangle_report(report, rectangles, spec)
    circles_ok = _append_circle_report(report, circles, spec)
    _append_polygon_report(report, polygons)
    all_passed = rectangles_ok and circles_ok
    _append_summary(
        report,
        all_passed=all_passed,
        rectangles=rectangles,
        circles=circles,
        polygons=polygons,
        spec=spec,
    )
    return all_passed, report


def main():
    """Run the sizing verifier as a command-line script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg_file", type=Path, help="Path to SVG file to verify")
    parser.add_argument(
        "--dpi", type=int, default=96, help="DPI for spec conversion (default 96)"
    )
    parser.add_argument(
        "--process-box-width",
        default="1.5in",
        help="Expected process box width (px/in/cm)",
    )
    parser.add_argument(
        "--process-box-height",
        default="0.6in",
        help="Expected process box height (px/in/cm)",
    )
    parser.add_argument(
        "--data-box-width", default="1.5in", help="Expected data box width (px/in/cm)"
    )
    parser.add_argument(
        "--data-box-height", default="0.4in", help="Expected data box height (px/in/cm)"
    )
    parser.add_argument(
        "--queue-min-diameter",
        default="0.5in",
        help="Expected minimum queue diameter (px/in/cm)",
    )
    parser.add_argument(
        "--queue-max-diameter",
        default="0.7in",
        help="Expected maximum queue diameter (px/in/cm)",
    )
    parser.add_argument(
        "--spacing-h",
        default="0.2in",
        help="Expected horizontal spacing target (px/in/cm)",
    )
    parser.add_argument(
        "--spacing-v",
        default="0.3in",
        help="Expected vertical spacing target (px/in/cm)",
    )

    args = parser.parse_args()

    if not args.svg_file.exists():
        print(f"Error: File not found: {args.svg_file}")
        sys.exit(2)

    all_passed, report = verify_sizing(
        args.svg_file,
        dpi=args.dpi,
        process_box_width=args.process_box_width,
        process_box_height=args.process_box_height,
        data_box_width=args.data_box_width,
        data_box_height=args.data_box_height,
        queue_circle_min=args.queue_min_diameter,
        queue_circle_max=args.queue_max_diameter,
        spacing_h=args.spacing_h,
        spacing_v=args.spacing_v,
    )

    for line in report:
        print(line)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
