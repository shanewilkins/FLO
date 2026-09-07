"""Source-location enrichment for human-facing FLO diagnostics."""

from __future__ import annotations

import re
from dataclasses import dataclass

_NODE_RE = re.compile(r"\bnode '([^']+)'")
_CODE_RE = re.compile(r"\b(E\d{4})\b")


@dataclass(frozen=True)
class SourceDiagnostic:
    """A compact source-aware diagnostic for CLI rendering."""

    code: str | None
    severity: str
    message: str
    source: str | None
    line: int | None
    column: int | None
    excerpt: str | None
    field_path: str | None = None
    suggestion: str | None = None
    include_chain: tuple[str, ...] = ()

    def render(self) -> str:
        """Render the diagnostic in a compiler-style human format."""
        if (
            self.source is None
            or self.line is None
            or self.column is None
            or self.excerpt is None
        ):
            return self.message
        location = f"{self.source}:{self.line}:{self.column}"
        field = f" [{self.field_path}]" if self.field_path else ""
        gutter = str(self.line)
        caret_padding = " " * max(0, self.column - 1)
        return "\n".join(
            (
                f"{location}: {self.message}{field}",
                f"  {gutter} | {self.excerpt}",
                f"  {' ' * len(gutter)} | {caret_padding}^",
            )
        )


def source_diagnostic(
    message: str,
    *,
    content: str,
    source_path: str | None,
    cause: BaseException | None = None,
    include_chain: tuple[str, ...] = (),
) -> SourceDiagnostic:
    """Build a structured, best-available source diagnostic."""
    if not include_chain:
        include_chain = _include_chain_from(cause)
    lines = content.splitlines()
    if not lines:
        return _unlocated_diagnostic(
            message,
            source=_source_label(source_path),
            include_chain=include_chain,
        )

    marked_location = _marked_error_location(cause)
    if marked_location is not None:
        line_index, column_index = marked_location
        return _diagnostic_at(
            message=_parse_message(message, cause),
            source=_source_label(source_path),
            lines=lines,
            line_index=line_index,
            column_index=column_index,
            field_path=None,
            include_chain=include_chain,
        )

    node_match = _NODE_RE.search(message)
    if node_match is None:
        return _unlocated_diagnostic(
            message,
            source=_source_label(source_path),
            include_chain=include_chain,
        )
    node_id = node_match.group(1)
    node_line = _find_node_line(lines, node_id)
    if node_line is None:
        return _unlocated_diagnostic(
            message,
            source=_source_label(source_path),
            include_chain=include_chain,
        )

    field_name = _field_name_from_message(message)
    line_index = _find_field_in_node_block(lines, node_line, field_name)
    field_path = f"steps.{node_id}"
    if field_name:
        field_path = f"{field_path}.{_field_path_suffix(message, field_name)}"
    return _diagnostic_at(
        message=message,
        source=_source_label(source_path),
        lines=lines,
        line_index=line_index,
        column_index=_first_content_column(lines[line_index]),
        field_path=field_path,
        include_chain=include_chain,
    )


def source_aware_message(
    message: str,
    *,
    content: str,
    source_path: str | None,
    cause: BaseException | None = None,
) -> str:
    """Add a best-available source location and excerpt to a diagnostic."""
    diagnostic = source_diagnostic(
        message,
        content=content,
        source_path=source_path,
        cause=cause,
    )
    return diagnostic.render()


def _marked_error_location(cause: BaseException | None) -> tuple[int, int] | None:
    current = cause
    while current is not None:
        mark = getattr(current, "problem_mark", None)
        line = getattr(mark, "line", None)
        column = getattr(mark, "column", None)
        if isinstance(line, int) and isinstance(column, int):
            return max(0, line), max(0, column)
        current = current.__cause__
    return None


def _parse_message(message: str, cause: BaseException | None) -> str:
    problem = getattr(cause, "problem", None)
    if isinstance(problem, str) and problem.strip():
        return f"E0001: invalid YAML: {problem.strip()}"
    first_line = next(
        (line.strip() for line in message.splitlines() if line.strip()), ""
    )
    return f"E0001: invalid YAML: {first_line or 'parse failed'}"


def _find_node_line(lines: list[str], node_id: str) -> int | None:
    pattern = re.compile(rf"^\s*-?\s*id:\s*['\"]?{re.escape(node_id)}['\"]?\s*$")
    return next(
        (index for index, line in enumerate(lines) if pattern.match(line)), None
    )


def _field_name_from_message(message: str) -> str | None:
    candidates = (
        "wait_time",
        "cycle_time",
        "changeover_time",
        "crossover",
        "transfer",
        "buffer_capacity",
        "performed_by",
        "supported_by",
        "inputs",
        "outputs",
        "outcomes",
    )
    return next((candidate for candidate in candidates if candidate in message), None)


def _find_field_in_node_block(
    lines: list[str], node_line: int, field_name: str | None
) -> int:
    if field_name is None:
        return node_line
    node_indent = len(lines[node_line]) - len(lines[node_line].lstrip())
    field_pattern = re.compile(rf"^\s*{re.escape(field_name)}\s*:")
    for index in range(node_line + 1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("- id:"):
            indent = len(line) - len(line.lstrip())
            if indent <= node_indent:
                break
        if field_pattern.match(line):
            return index
    return node_line


def _field_path_suffix(message: str, field_name: str) -> str:
    if f"metadata.{field_name}" in message or field_name in {
        "wait_time",
        "cycle_time",
        "changeover_time",
        "crossover",
        "transfer",
        "buffer_capacity",
    }:
        return f"metadata.{field_name}"
    return field_name


def _first_content_column(line: str) -> int:
    return len(line) - len(line.lstrip())


def _diagnostic_at(
    *,
    message: str,
    source: str,
    lines: list[str],
    line_index: int,
    column_index: int,
    field_path: str | None,
    include_chain: tuple[str, ...],
) -> SourceDiagnostic:
    bounded_line = min(max(0, line_index), len(lines) - 1)
    bounded_column = max(0, column_index)
    code_match = _CODE_RE.search(message)
    return SourceDiagnostic(
        code=code_match.group(1) if code_match is not None else None,
        severity="error",
        message=message,
        source=source,
        line=bounded_line + 1,
        column=bounded_column + 1,
        excerpt=lines[bounded_line],
        field_path=field_path,
        suggestion=_suggestion_for(field_path),
        include_chain=include_chain,
    )


def _unlocated_diagnostic(
    message: str, *, source: str, include_chain: tuple[str, ...]
) -> SourceDiagnostic:
    code_match = _CODE_RE.search(message)
    return SourceDiagnostic(
        code=code_match.group(1) if code_match is not None else None,
        severity="error",
        message=message,
        source=source,
        line=None,
        column=None,
        excerpt=None,
        include_chain=include_chain,
    )


def _include_chain_from(cause: BaseException | None) -> tuple[str, ...]:
    current = cause
    while current is not None:
        include_chain = getattr(current, "include_chain", None)
        if isinstance(include_chain, tuple) and all(
            isinstance(path, str) for path in include_chain
        ):
            return include_chain
        current = current.__cause__
    return ()


def _source_label(source_path: str | None) -> str:
    return "<stdin>" if source_path in {None, "-"} else source_path


def _suggestion_for(field_path: str | None) -> str | None:
    if field_path is not None and field_path.endswith(".metadata.wait_time"):
        return "Move wait_time to a queue step."
    return None
