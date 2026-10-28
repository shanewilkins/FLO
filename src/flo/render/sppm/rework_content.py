"""SPPM structured rework-relation display content."""

from __future__ import annotations


def build_sppm_rework_metadata_lines(rework: object) -> tuple[str, ...]:
    """Present canonical frequency, reason and note without metadata fallbacks."""
    if not isinstance(rework, dict):
        return ()
    lines: list[str] = []
    frequency = rework.get("frequency")
    if isinstance(frequency, dict):
        numerator, denominator = (
            frequency.get("numerator"),
            frequency.get("denominator"),
        )
        if (
            isinstance(numerator, (int, float))
            and isinstance(denominator, (int, float))
            and denominator > 0
        ):
            lines.append(f"Rate: {numerator / denominator * 100:g}%")
    for key in ("reason", "note"):
        text = rework.get(key)
        if isinstance(text, str) and text.strip():
            lines.append(f"{key.title()}: {text.strip()}")
    return tuple(lines)
