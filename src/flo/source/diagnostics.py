"""Source-location enrichment for human-facing FLO diagnostics."""

from __future__ import annotations

import re
from dataclasses import dataclass

_NODE_RE = re.compile(r"\bnode '([^']+)'")
_EDGE_RE = re.compile(r"\bedge '([^']+)'\s*->\s*'([^']+)'")
_CODE_RE = re.compile(r"\b(E\d{4})\b")
_INDEXED_PATH_RE = re.compile(r"\b((steps|transitions)\[(\d+)\](?:\.[A-Za-z_][\w-]*)*)")


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

    edge_match = _EDGE_RE.search(message)
    if edge_match is not None:
        edge_location = _find_transition_location(
            lines,
            source_id=edge_match.group(1),
            target_id=edge_match.group(2),
            preferred_field=_edge_field_name(message),
        )
        if edge_location is not None:
            line_index, field_name = edge_location
            field_path = (
                f"transitions.{edge_match.group(1)}->{edge_match.group(2)}.{field_name}"
            )
            return _diagnostic_at(
                message=message,
                source=_source_label(source_path),
                lines=lines,
                line_index=line_index,
                column_index=_first_content_column(lines[line_index]),
                field_path=field_path,
                suggestion=_suggestion_for_code(message),
                include_chain=include_chain,
            )

    indexed_path_match = _INDEXED_PATH_RE.search(message)
    if indexed_path_match is not None:
        field_path = indexed_path_match.group(1)
        line_index = _find_indexed_path_line(
            lines,
            section=indexed_path_match.group(2),
            item_index=int(indexed_path_match.group(3)),
            field_path=field_path,
        )
        if line_index is not None:
            return _diagnostic_at(
                message=message,
                source=_source_label(source_path),
                lines=lines,
                line_index=line_index,
                column_index=_first_content_column(lines[line_index]),
                field_path=field_path,
                suggestion=_suggestion_for_code(message),
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
        suggestion=_suggestion_for_code(message),
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


def _find_transition_location(
    lines: list[str],
    *,
    source_id: str,
    target_id: str,
    preferred_field: str | None,
) -> tuple[int, str] | None:
    source_pattern = re.compile(
        rf"^\s*-?\s*source:\s*['\"]?{re.escape(source_id)}['\"]?\s*$"
    )
    target_pattern = re.compile(
        rf"^\s*target:\s*['\"]?{re.escape(target_id)}['\"]?\s*$"
    )
    for source_line, line in enumerate(lines):
        if not source_pattern.match(line):
            continue
        source_indent = len(line) - len(line.lstrip())
        for index in range(source_line + 1, len(lines)):
            candidate = lines[index]
            if candidate.strip().startswith("- source:"):
                break
            if target_pattern.match(candidate):
                if preferred_field is not None:
                    preferred_pattern = re.compile(
                        rf"^\s*{re.escape(preferred_field)}\s*:"
                    )
                    for field_index in range(index + 1, len(lines)):
                        field_line = lines[field_index]
                        if field_line.strip().startswith("- source:"):
                            break
                        if preferred_pattern.match(field_line):
                            return field_index, preferred_field
                for field_index in range(index + 1, len(lines)):
                    field_line = lines[field_index]
                    if field_line.strip().startswith("- source:"):
                        break
                    if re.match(r"^\s*outcome\s*:", field_line):
                        return field_index, "outcome"
                    if re.match(r"^\s*(?:edge_type|rework)\s*:", field_line):
                        field_name = field_line.split(":", maxsplit=1)[0].strip()
                        return field_index, field_name
                return index, preferred_field or "outcome"
            indent = len(candidate) - len(candidate.lstrip())
            if candidate.strip() and indent < source_indent:
                break
    return None


def _find_indexed_path_line(
    lines: list[str], *, section: str, item_index: int, field_path: str
) -> int | None:
    section_pattern = re.compile(rf"^\s*{re.escape(section)}\s*:\s*$")
    section_line = next(
        (index for index, line in enumerate(lines) if section_pattern.match(line)),
        None,
    )
    if section_line is None:
        return None

    item_lines: list[int] = []
    section_indent = len(lines[section_line]) - len(lines[section_line].lstrip())
    for index in range(section_line + 1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped and indent <= section_indent:
            break
        if re.match(r"^\s*-\s+", line):
            item_lines.append(index)
    if item_index >= len(item_lines):
        return section_line

    item_line = item_lines[item_index]
    item_indent = len(lines[item_line]) - len(lines[item_line].lstrip())
    field_name = field_path.rsplit(".", maxsplit=1)[-1]
    field_pattern = re.compile(rf"^\s*{re.escape(field_name)}\s*:")
    for index in range(item_line, len(lines)):
        line = lines[index]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if index > item_line and stripped.startswith("-") and indent <= item_indent:
            break
        if field_pattern.match(line):
            return index
    return item_line


def _field_name_from_message(message: str) -> str | None:
    if "E1025" in message:
        return "kind"
    candidates = (
        "wait_time",
        "cycle_time",
        "changeover_time",
        "crossover",
        "transfer",
        "buffer_capacity",
        "performed_by",
        "consumes",
        "produces",
        "uses",
        "supported_by",
        "inputs",
        "outputs",
        "outcomes",
        "branch",
        "route",
    )
    return next((candidate for candidate in candidates if candidate in message), None)


def _edge_field_name(message: str) -> str | None:
    for field_name in ("outcome", "route", "edge_type", "rework"):
        if field_name in message:
            return field_name
    return None


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
    suggestion: str | None = None,
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
        suggestion=suggestion or _suggestion_for(field_path),
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
        return "Use wait_before for canonical work-node waiting evidence."
    return None


def _suggestion_for_code(message: str) -> str | None:
    code_match = _CODE_RE.search(message)
    if code_match is None:
        return None
    return {
        "E0201": "Move outcomes to a decision step.",
        "E0202": "Declare at least two named decision outcomes and their targets.",
        "E0205": "Name the target step directly or add a target field.",
        "E0206": "Add a non-empty target step ID to this outcome branch.",
        "E0209": "Use the YAML boolean true or false without quotes.",
        "E0210": "Replace this value with a metadata object or remove it.",
        "E0211": "Move routes to a branch step.",
        "E0212": "Declare at least two branch routes and their targets.",
        "E0214": "Move branch configuration to a branch step.",
        "E0215": "Declare branch as an object with a mode field.",
        "E0216": "Use dispatch, probabilistic, external, or unspecified as the branch mode.",
        "E0217": "Name the branch policy or remove the policy field.",
        "E0218": "List each eligible resource ID once, using non-empty strings.",
        "E0219": "Keep wait_before and remove the task wait_time alias.",
        "E1020": "Add a unique outcome to every transition leaving the decision.",
        "E1022": "Remove the outcome or make the transition source a decision.",
        "E1023": "Target a process step instead of the start boundary.",
        "E1024": "Remove this transition or change its source from the end boundary.",
        "E1025": "Use decision, branch, or parallel_split to state how outgoing paths are selected.",
        "E1026": "Add a second outgoing route or replace the branch with an ordinary step.",
        "E1027": "Remove the route or make the transition source a branch.",
        "E1028": "Remove route from the decision edge and use its outcome field.",
        "E1029": "Add branch.mode to declare the route-selection mechanism.",
        "E1030": "Use dispatch, probabilistic, external, or unspecified as the branch mode.",
        "E1031": "Remove outcome from the generic branch edge and use route when a name is needed.",
        "E1032": "Give each named route leaving the branch a unique name.",
        "E1312": "Declare the referenced item under process.metadata.items or correct the item ID.",
        "E1313": "Declare the referenced resource under process.metadata.resources or correct the resource ID.",
        "E1314": "Use a resource whose declared kind matches this relation.",
        "E1315": "Declare the eligible resource under process.metadata.resources or correct the resource ID.",
        "E1304": "Use a non-empty measurement_id string or remove it.",
        "E1305": "List one or more unique, non-empty measurement IDs.",
        "E1404": "Use edge_type: rework with rework: true, or omit both fields.",
        "E1503": "Use wait_before on work nodes; wait_time is canonical only on queues.",
        "E1504": "Use wait_time on queues; wait_before belongs on work nodes.",
        "E1505": "Give the queue wait_time and task wait_before the same measurement_id, or keep only one measurement.",
        "E1506": "Give each work-node waiting measurement a unique measurement_id.",
        "E1507": "Reference measurement_id values declared by work-node wait_before metadata.",
    }.get(code_match.group(1))
