"""SPPM SVG anchor spec types and DOT extraction helpers.

These are used exclusively by the Graphviz SVG postprocessor.  Extracting
them to a separate module keeps graphviz.py within the file-length budget.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SppmReturnAnchorSpec:
    """Resolved anchor-spec for one SPPM return-loop or branch edge."""

    anchor_id: str
    source_id: str
    target_id: str


def extract_sppm_return_anchor_specs(dot: str) -> list[SppmReturnAnchorSpec]:
    """Extract return-loop anchor specs from SPPM DOT source."""
    specs: dict[str, SppmReturnAnchorSpec] = {}

    # DOT edges use endpoint notation: "node":port
    # Return-loop second segment: "anchor" -> "target":s [...]
    # First segment (no-arrow): "source":w -> "anchor" [... arrowhead=none ...]
    second_segment_pattern = re.compile(
        r'^\s*"(?P<anchor>__sppm_rework_corridor_[^"]+)"\s*->\s*"(?P<target>[^"]+)":s\s*\[(?P<attrs>[^\]]*)\];\s*$',
        flags=re.MULTILINE,
    )
    first_segment_pattern = re.compile(
        r'^\s*"(?P<source>[^"]+)"(?::[a-z_]+)?\s*->\s*"(?P<anchor>__sppm_rework_corridor_[^"]+)"\s*\[(?P<attrs>[^\]]*)\];\s*$',
        flags=re.MULTILINE,
    )

    first_segment_by_anchor: dict[str, str] = {}
    for match in first_segment_pattern.finditer(dot):
        attrs = match.group("attrs")
        if "arrowhead=none" not in attrs:
            continue
        first_segment_by_anchor[match.group("anchor")] = match.group("source")

    for match in second_segment_pattern.finditer(dot):
        anchor_id = match.group("anchor")
        source_id = first_segment_by_anchor.get(anchor_id)
        if not source_id:
            continue
        specs[anchor_id] = SppmReturnAnchorSpec(
            anchor_id=anchor_id,
            source_id=source_id,
            target_id=match.group("target"),
        )

    return list(specs.values())


def extract_sppm_branch_anchor_specs(dot: str) -> list[SppmReturnAnchorSpec]:
    """Extract branch-down anchor specs from SPPM DOT source."""
    specs: dict[str, SppmReturnAnchorSpec] = {}

    # Branch second segment: "anchor" -> "rework":n [...]
    second_segment_pattern = re.compile(
        r'^\s*"(?P<anchor>__sppm_rework_corridor_[^"]+)"\s*->\s*"(?P<target>[^"]+)":n\s*\[(?P<attrs>[^\]]*)\];\s*$',
        flags=re.MULTILINE,
    )
    # Branch first segment (no arrow): "decision":s -> "anchor" [... arrowhead=none ...]
    first_segment_pattern = re.compile(
        r'^\s*"(?P<source>[^"]+)":s\s*->\s*"(?P<anchor>__sppm_rework_corridor_[^"]+)"\s*\[(?P<attrs>[^\]]*)\];\s*$',
        flags=re.MULTILINE,
    )

    first_segment_by_anchor: dict[str, str] = {}
    for match in first_segment_pattern.finditer(dot):
        if "arrowhead=none" not in match.group("attrs"):
            continue
        first_segment_by_anchor[match.group("anchor")] = match.group("source")

    for match in second_segment_pattern.finditer(dot):
        anchor_id = match.group("anchor")
        source_id = first_segment_by_anchor.get(anchor_id)
        if not source_id:
            continue
        specs[anchor_id] = SppmReturnAnchorSpec(
            anchor_id=anchor_id,
            source_id=source_id,
            target_id=match.group("target"),
        )

    return list(specs.values())
