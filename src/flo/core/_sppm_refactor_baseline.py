"""Baseline measurements for the SPPM renderer refactor.

The helper is intentionally reusable so the same measurements can be
recomputed from the issue body, from a wrapper script, or from other FLO
quality-gate tooling.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence, cast

try:
    from radon.complexity import cc_visit
except Exception:  # pragma: no cover - optional dev dependency
    cc_visit = None


DEFAULT_SPPM_REFACTOR_BASELINE_FILES: tuple[str, ...] = (
    "src/flo/render/_sppm_publication.py",
    "src/flo/render/_svg_sppm.py",
    "src/flo/render/_svg_sppm_edges.py",
    "src/flo/render/_svg_sppm_nodes.py",
    "src/flo/render/_svg_sppm_rows.py",
    "src/flo/render/layout_core/elk_sppm_helpers.py",
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = _REPO_ROOT / "src"
_RENDER_BACKEND_NEUTRAL_SHARED_FILES: tuple[str, ...] = (
    "src/flo/render/_publication.py",
)
_LAYER_PATHS: dict[str, tuple[str, ...]] = {
    "services": ("src/flo/services/", "src/flo/io/"),
    "adapters": ("src/flo/adapters/",),
    "compiler": ("src/flo/compiler/", "src/flo/ir/", "src/flo/analysis/"),
    "export": ("src/flo/export/",),
    "render": ("src/flo/render/",),
    "core": ("src/flo/core.py", "src/flo/main.py", "src/flo/cli.py"),
}
_ALLOWED_IMPORTS: dict[str, frozenset[str]] = {
    "services": frozenset(),
    "adapters": frozenset({"services"}),
    "compiler": frozenset({"adapters", "services"}),
    "export": frozenset({"compiler", "services"}),
    "render": frozenset({"compiler", "services"}),
    "core": frozenset({"services", "adapters", "compiler", "export", "render"}),
}


@dataclass(frozen=True)
class ImportViolation:
    """A concrete layer or boundary import violation."""

    path: Path
    lineno: int
    imported_module: str
    rule: str


@dataclass(frozen=True)
class DryViolation:
    """A normalized clone group suggesting a DRY violation."""

    files: tuple[Path, ...]
    functions: tuple[str, ...]
    span_lines: int


@dataclass(frozen=True)
class FunctionBaseline:
    """Function-level structural baseline for one file."""

    name: str
    lineno: int
    end_lineno: int
    span_lines: int
    complexity: int | None = None


@dataclass(frozen=True)
class FileBaseline:
    """Baseline measurements for one Python file."""

    path: Path
    line_count: int
    max_line_length: int
    long_lines_gt_100: int
    function_count: int
    longest_function: FunctionBaseline | None
    complexity_findings: tuple[FunctionBaseline, ...]


@dataclass(frozen=True)
class BaselineReport:
    """Full baseline report for the SPPM refactor."""

    files: tuple[FileBaseline, ...]
    layer_violations: tuple[ImportViolation, ...]
    dry_violations: tuple[DryViolation, ...]


def collect_sppm_refactor_baseline(
    files: Sequence[str | Path] | None = None,
) -> BaselineReport:
    """Collect structural, boundary, and DRY baselines for the requested files."""
    resolved_files = [
        Path(raw) for raw in (files or DEFAULT_SPPM_REFACTOR_BASELINE_FILES)
    ]
    file_stats = tuple(collect_file_baseline(path) for path in resolved_files)
    return BaselineReport(
        files=file_stats,
        layer_violations=_collect_layer_violations(resolved_files),
        dry_violations=_collect_dry_violations(resolved_files),
    )


def collect_file_baseline(path: Path) -> FileBaseline:
    """Collect baseline measurements for one Python file."""
    path = _normalize_repo_path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    line_count = len(lines)
    max_line_length = max((len(line) for line in lines), default=0)
    long_lines_gt_100 = sum(1 for line in lines if len(line) > 100)

    tree = ast.parse(text)
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    function_stats: list[FunctionBaseline] = []
    for fn in functions:
        end_lineno = getattr(fn, "end_lineno", fn.lineno)
        span_lines = end_lineno - fn.lineno + 1
        function_stats.append(
            FunctionBaseline(
                name=fn.name,
                lineno=fn.lineno,
                end_lineno=end_lineno,
                span_lines=span_lines,
            )
        )

    longest_function = max(
        function_stats, key=lambda item: item.span_lines, default=None
    )
    complexity_findings = _collect_complexity_findings(path)
    return FileBaseline(
        path=path,
        line_count=line_count,
        max_line_length=max_line_length,
        long_lines_gt_100=long_lines_gt_100,
        function_count=len(functions),
        longest_function=longest_function,
        complexity_findings=complexity_findings,
    )


def _collect_complexity_findings(path: Path) -> tuple[FunctionBaseline, ...]:
    if cc_visit is None:
        return ()

    try:
        blocks = cc_visit(path.read_text(encoding="utf-8"))
    except Exception:
        return ()

    findings: list[FunctionBaseline] = []
    for block in blocks:
        complexity = int(getattr(block, "complexity", 0) or 0)
        if complexity <= 0:
            continue
        lineno = int(getattr(block, "lineno", 0) or 0)
        span_lines = 1
        findings.append(
            FunctionBaseline(
                name=str(getattr(block, "name", "")),
                lineno=lineno,
                end_lineno=lineno,
                span_lines=span_lines,
                complexity=complexity,
            )
        )
    findings.sort(key=lambda item: (-int(item.complexity or 0), item.name, item.lineno))
    return tuple(findings)


def format_sppm_refactor_baseline_report(report: BaselineReport) -> str:
    """Format the baseline measurements as a markdown report."""
    lines: list[str] = []
    stats = report.files
    lines.append(
        "| File | Lines | Max line | >100 chars | Functions | Longest function | Complexity |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
    for item in stats:
        longest = _format_longest_function(item.longest_function)
        complexity = _format_complexity(item.complexity_findings)
        lines.append(
            f"| {_workspace_relative_path(item.path)} | {item.line_count} | {item.max_line_length} | {item.long_lines_gt_100} | {item.function_count} | {longest} | {complexity} |"
        )
    lines.append("")
    lines.append("## Layer Violations")
    lines.extend(_format_layer_violations(report.layer_violations))
    lines.append("")
    lines.append("## DRY Violations")
    lines.extend(_format_dry_violations(report.dry_violations))
    return "\n".join(lines)


def _collect_layer_violations(files: Sequence[Path]) -> tuple[ImportViolation, ...]:
    violations: list[ImportViolation] = []
    for path in _iter_render_shared_core_paths():
        violations.extend(_collect_renderer_boundary_violations(path))
    for path in files:
        violations.extend(_collect_architecture_layer_violations(path))
    violations.sort(
        key=lambda item: (
            item.path.as_posix(),
            item.lineno,
            item.imported_module,
            item.rule,
        )
    )
    return tuple(violations)


def _iter_render_shared_core_paths() -> tuple[Path, ...]:
    paths = [Path(raw) for raw in _RENDER_BACKEND_NEUTRAL_SHARED_FILES]
    return tuple(
        _normalize_repo_path(path)
        for path in paths
        if _normalize_repo_path(path).exists()
    )


def _collect_renderer_boundary_violations(path: Path) -> list[ImportViolation]:
    path = _normalize_repo_path(path)
    violations: list[ImportViolation] = []
    for lineno, imported_module in _iter_imports(path):
        if imported_module.startswith("flo.render._sppm"):
            violations.append(
                ImportViolation(
                    path=path,
                    lineno=lineno,
                    imported_module=imported_module,
                    rule="shared renderer helpers must not import SPPM-specific modules",
                )
            )
    return violations


def _collect_architecture_layer_violations(path: Path) -> list[ImportViolation]:
    path = _normalize_repo_path(path)
    path_layer = _layer_for_path(path)
    if path_layer is None:
        return []

    allowed_layers = _ALLOWED_IMPORTS.get(path_layer, frozenset())
    violations: list[ImportViolation] = []
    for lineno, imported_module in _iter_imports(path):
        imported_path = _path_from_module(imported_module)
        if imported_path is None:
            continue
        imported_layer = _layer_for_path(imported_path)
        if imported_layer is None or imported_layer == path_layer:
            continue
        if imported_layer not in allowed_layers:
            violations.append(
                ImportViolation(
                    path=path,
                    lineno=lineno,
                    imported_module=imported_module,
                    rule=f"{path_layer} layer must not import {imported_layer}",
                )
            )
    return violations


def _iter_imports(path: Path) -> list[tuple[int, str]]:
    path = _normalize_repo_path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[tuple[int, str]] = []
    package_name = _module_name_from_path(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported = _resolve_import_from(module_name=package_name, node=node)
            if imported is not None:
                imports.append((node.lineno, imported))
    return imports


def _module_name_from_path(path: Path) -> str:
    path = _normalize_repo_path(path)
    rel = path.relative_to(_SRC_ROOT)
    return ".".join(rel.with_suffix("").parts)


def _resolve_import_from(*, module_name: str, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    package_parts = module_name.split(".")[:-1]
    if node.level > len(package_parts) + 1:
        return node.module
    anchor_parts = package_parts[: len(package_parts) - node.level + 1]
    if node.module:
        anchor_parts.extend(node.module.split("."))
    return ".".join(part for part in anchor_parts if part)


def _path_from_module(module_name: str) -> Path | None:
    if not module_name.startswith("flo."):
        return None
    rel_path = Path(*module_name.split(".")).with_suffix(".py")
    candidate = _SRC_ROOT / rel_path
    if candidate.exists():
        return candidate
    package_init = _SRC_ROOT / Path(*module_name.split(".")) / "__init__.py"
    if package_init.exists():
        return package_init
    return None


def _layer_for_path(path: Path) -> str | None:
    path_text = _workspace_relative_path(path)
    for layer, prefixes in _LAYER_PATHS.items():
        for prefix in prefixes:
            if path_text == prefix or path_text.startswith(prefix):
                return layer
    return None


def _normalize_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else (_REPO_ROOT / path)


def _workspace_relative_path(path: Path) -> str:
    path = _normalize_repo_path(path)
    try:
        return path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _collect_dry_violations(files: Sequence[Path]) -> tuple[DryViolation, ...]:
    groups: dict[str, list[tuple[Path, str, int]]] = {}
    for path in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            end_lineno = getattr(node, "end_lineno", node.lineno)
            span_lines = end_lineno - node.lineno + 1
            if span_lines < 8:
                continue
            fingerprint = _normalized_function_fingerprint(node)
            groups.setdefault(fingerprint, []).append((path, node.name, span_lines))

    dry_violations: list[DryViolation] = []
    for items in groups.values():
        unique_files = {path for path, _name, _span in items}
        if len(unique_files) < 2:
            continue
        sorted_items = sorted(items, key=lambda item: (item[0].as_posix(), item[1]))
        dry_violations.append(
            DryViolation(
                files=tuple(path for path, _name, _span in sorted_items),
                functions=tuple(name for _path, name, _span in sorted_items),
                span_lines=max(span for _path, _name, span in sorted_items),
            )
        )
    dry_violations.sort(
        key=lambda item: (
            -item.span_lines,
            tuple(path.as_posix() for path in item.files),
        )
    )
    return tuple(dry_violations)


def _normalized_function_fingerprint(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    normalized = _NormalizeFunctionClone().visit(
        ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    )
    return ast.dump(normalized, include_attributes=False)


class _NormalizeFunctionClone(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        return self._normalize_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        return self._normalize_function(node)

    def visit_Name(self, node: ast.Name) -> ast.Name:
        return ast.copy_location(ast.Name(id="NAME", ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.arg:
        return ast.copy_location(
            ast.arg(arg="ARG", annotation=None, type_comment=None), node
        )

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        value = self.visit(node.value)
        return ast.copy_location(
            ast.Attribute(value=value, attr="ATTR", ctx=node.ctx), node
        )

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        value = node.value
        if isinstance(value, str):
            value = "STR"
        elif isinstance(value, bytes):
            value = b"B"
        elif isinstance(value, (int, float, complex)):
            value = 0
        return ast.copy_location(ast.Constant(value=value), node)

    def _normalize_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.FunctionDef | ast.AsyncFunctionDef:
        clone = cast(ast.FunctionDef | ast.AsyncFunctionDef, self.generic_visit(node))
        clone.name = "FUNCTION"
        # Drop decorations and return annotations so dry-analysis compares
        # implementation structure only, not declaration metadata.
        clone.decorator_list = []
        clone.returns = None
        return clone


def _format_layer_violations(violations: Sequence[ImportViolation]) -> list[str]:
    if not violations:
        return ["- None detected."]
    lines = ["| File | Line | Imported module | Rule |", "| --- | ---: | --- | --- |"]
    for item in violations:
        lines.append(
            f"| {_workspace_relative_path(item.path)} | {item.lineno} | {item.imported_module} | {item.rule} |"
        )
    return lines


def _format_dry_violations(violations: Sequence[DryViolation]) -> list[str]:
    if not violations:
        return [
            "- No normalized cross-file clone groups detected in the tracked SPPM modules."
        ]
    lines = ["| Files | Functions | Max span |", "| --- | --- | ---: |"]
    for item in violations:
        file_text = ", ".join(_workspace_relative_path(path) for path in item.files)
        function_text = ", ".join(item.functions)
        lines.append(f"| {file_text} | {function_text} | {item.span_lines} |")
    return lines


def _format_longest_function(item: FunctionBaseline | None) -> str:
    if item is None:
        return "-"
    return f"{item.name}:{item.span_lines}"


def _format_complexity(items: Sequence[FunctionBaseline]) -> str:
    if not items:
        return "-"
    return ", ".join(f"{item.name}({item.complexity})" for item in items[:3])


def main(argv: Sequence[str] | None = None) -> int:
    """Emit the current SPPM refactor baseline report."""
    files = [Path(raw) for raw in (argv or DEFAULT_SPPM_REFACTOR_BASELINE_FILES)]
    report = collect_sppm_refactor_baseline(files)
    print(format_sppm_refactor_baseline_report(report))
    return 0


__all__ = [
    "BaselineReport",
    "DEFAULT_SPPM_REFACTOR_BASELINE_FILES",
    "collect_sppm_refactor_baseline",
    "format_sppm_refactor_baseline_report",
    "main",
]
