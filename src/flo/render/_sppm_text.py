"""Text and density helpers for SPPM labels."""

from __future__ import annotations

import textwrap
from typing import Iterable


def normalize_space(value: str) -> str:
    """Collapse repeated whitespace into single spaces."""
    return " ".join(str(value or "").split())


def abbreviate_workers(workers: Iterable[str], max_items: int = 3) -> str:
    """Return a compact worker list for dense labels."""
    cleaned = [normalize_space(str(worker)) for worker in workers if str(worker).strip()]
    if not cleaned:
        return ""

    if len(cleaned) <= max_items:
        return ", ".join(_initials(name) for name in cleaned)

    shown = ", ".join(_initials(name) for name in cleaned[:max_items])
    remaining = len(cleaned) - max_items
    return f"{shown}, +{remaining}"


def format_text_field(
    raw: str,
    *,
    max_len: int | None,
    wrap_strategy: str,
    truncation_policy: str,
    html_break: str,
) -> str:
    """Normalize, wrap, and truncate text according to renderer policy."""
    text = normalize_space(raw)
    if not text:
        return ""

    wrapped = _wrap_text(text, width=max_len, strategy=wrap_strategy)
    wrapped = _enforce_max_length(wrapped, max_len=max_len, policy=truncation_policy)
    return wrapped.replace("\n", html_break)


def apply_density_filter(
    *,
    density: str,
    description: str,
    ct_line: str,
    wt_line: str,
    workers_line: str,
    notes_line: str,
) -> list[str]:
    """Return info-box lines for full/compact/teaching density modes."""
    if density == "teaching":
        key_metric = ct_line or wt_line
        return [line for line in [key_metric, notes_line] if line]

    if density == "compact":
        condensed_metric = " | ".join(line for line in [ct_line, wt_line] if line)
        return [line for line in [condensed_metric, workers_line, notes_line] if line]

    return [line for line in [description, workers_line, ct_line, wt_line, notes_line] if line]


def _initials(name: str) -> str:
    tokens = [token for token in normalize_space(name).replace("_", " ").split(" ") if token]
    if not tokens:
        return ""
    if len(tokens) == 1:
        token = tokens[0]
        return token if len(token) <= 3 else token[:3]
    return "".join(token[0].upper() for token in tokens)


def _wrap_text(text: str, *, width: int | None, strategy: str) -> str:
    if not width or width < 2:
        return text

    if strategy == "hard":
        return "\n".join(text[i : i + width] for i in range(0, len(text), width))

    if strategy == "balanced":
        words = text.split(" ")
        if len(words) < 2 or len(text) <= width:
            return text
        midpoint = len(words) // 2
        left = " ".join(words[:midpoint])
        right = " ".join(words[midpoint:])
        if len(left) <= width and len(right) <= width:
            return f"{left}\n{right}"

    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)) or text


def _enforce_max_length(text: str, *, max_len: int | None, policy: str) -> str:
    if not max_len or max_len <= 0:
        return text

    # Count without manual line breaks when enforcing max display payload.
    flat = text.replace("\n", " ")
    if len(flat) <= max_len:
        return text

    if policy == "none":
        return text
    if policy == "clip":
        return flat[:max_len]

    if max_len <= 3:
        return "." * max_len
    return flat[: max_len - 3] + "..."
