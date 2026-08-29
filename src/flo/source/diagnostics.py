"""Source-location enrichment for human-facing FLO diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import re


_NODE_RE = re.compile(r"\bnode '([^']+)'")


@dataclass(frozen=True)
class SourceDiagnostic:
    """A compact source-aware diagnostic for CLI rendering."""

    message: str
    source: str
    line: int
    column: int
    excerpt: str
    field_path: str | None = None

    def render(self) -> str:
        """Render the diagnostic in a compiler-style human format."""
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


def source_aware_message(
    message: str,
    *,
    content: str,
    source_path: str | None,
    cause: BaseException | None = None,
) -> str:
    """Add a best-available source location and excerpt to a diagnostic."""
    lines = content.splitlines()
    if not lines:
        return message

    marked_location = _marked_error_location(cause)
    if marked_location is not None:
        line_index, column_index = marked_location
        return _render_at(
            message=_parse_message(message, cause),
            source=source_path or "<stdin>",
            lines=lines,
            line_index=line_index,
            column_index=column_index,
            field_path=None,
        )

    node_match = _NODE_RE.search(message)
    if node_match is None:
        return message
    node_id = node_match.group(1)
    node_line = _find_node_line(lines, node_id)
    if node_line is None:
        return message

    field_name = _field_name_from_message(message)
    line_index = _find_field_in_node_block(lines, node_line, field_name)
    field_path = f"steps.{node_id}"
    if field_name:
        field_path = f"{field_path}.{_field_path_suffix(message, field_name)}"
    column_index = _first_content_column(lines[line_index])
    return _render_at(
        message=message,
        source=source_path or "<stdin>",
        lines=lines,
        line_index=line_index,
        column_index=column_index,
        field_path=field_path,
    )


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


def _render_at(
    *,
    message: str,
    source: str,
    lines: list[str],
    line_index: int,
    column_index: int,
    field_path: str | None,
) -> str:
    bounded_line = min(max(0, line_index), len(lines) - 1)
    bounded_column = max(0, column_index)
    return SourceDiagnostic(
        message=message,
        source=source,
        line=bounded_line + 1,
        column=bounded_column + 1,
        excerpt=lines[bounded_line],
        field_path=field_path,
    ).render()
