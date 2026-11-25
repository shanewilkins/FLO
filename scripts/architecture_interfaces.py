"""Enforce declared subsystem interfaces and complete-artifact consumer imports."""

from __future__ import annotations

import ast
import json
import tomllib
from importlib.util import resolve_name
from pathlib import Path

SUBSYSTEMS = frozenset({"app", "process", "render", "source"})


def module_name(path: Path, source: Path) -> str:
    """Resolve a source path to its importable package or module name."""
    parts = path.relative_to(source).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def import_references(
    source: str, importer: str, *, is_package: bool, modules: set[str]
) -> set[tuple[str, str, int]]:
    """Resolve static imports and qualified uses, including aliases and relatives.

    Members are kept separate from modules so a facade import cannot disguise an
    implementation submodule. Dynamic import strings are outside this AST check.
    """
    tree = ast.parse(source)
    package = importer if is_package else importer.rpartition(".")[0]
    references = set()
    aliases = {}

    def record(target: str, line: int) -> None:
        parts = target.split(".")
        for length in range(len(parts), 0, -1):
            module = ".".join(parts[:length])
            if module in modules:
                member = parts[length] if length < len(parts) else ""
                references.add((module, member, line))
                return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                record(alias.name, node.lineno)
                aliases[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                base = resolve_name("." * node.level + base, package)
            for alias in node.names:
                target = f"{base}.{alias.name}"
                record(target, node.lineno)
                aliases[alias.asname or alias.name] = target

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        parts = []
        value = node
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name) and value.id in aliases:
            record(".".join([aliases[value.id], *reversed(parts)]), node.lineno)
    return references


def interface_violations(
    references: set[tuple[str, str, int]],
    importer: str,
    interfaces: dict[str, list[str]],
) -> list[str]:
    """Reject cross-subsystem implementation imports and inward facade shortcuts."""
    owner = importer.split(".")[1]
    violations = []
    for module, member, line in sorted(references):
        target = module.split(".")[1] if "." in module else ""
        if owner in SUBSYSTEMS | {"errors", "diagnostics"} and module in {
            "flo",
            "flo.api",
        }:
            violations.append(f"{importer}:{line}: inward import of facade {module}")
        elif (
            target in SUBSYSTEMS
            and target != owner
            and (
                module not in interfaces[target]
                or member.startswith("_")
                or member == "*"
            )
        ):
            violations.append(
                f"{importer}:{line}: undeclared interface {module}.{member}"
            )
    return violations


def consumer_violations(
    references: set[tuple[str, str, int]],
    allowed: set[str],
    exceptions: set[str],
) -> list[str]:
    """Allow complete-artifact consumers only declared rendering interfaces."""
    return [
        f"line {line}: implementation dependency {module}.{member}"
        for module, member, line in sorted(references)
        if (module == "flo.render" or module.startswith("flo.render."))
        and (
            module not in allowed | exceptions
            or ((member.startswith("_") or member == "*") and module not in exceptions)
        )
    ]


def sppm_classification_violations(
    modules: set[str], config: dict, contracts: list[dict]
) -> list[str]:
    """Require every SPPM module to have an explicit, disjoint responsibility."""
    contract = next(
        item
        for item in contracts
        if item["name"] == "SPPM SVG emission cannot run node or route layout policy"
    )
    groups = [
        set(contract["source_modules"]),
        set(config["sppm_emission_support"]),
        {
            name
            for name in contract["forbidden_modules"]
            if name.startswith("flo.render.sppm.")
        },
    ]
    actual = {
        name
        for name in modules
        if name == "flo.render.sppm" or name.startswith("flo.render.sppm.")
    }
    classified = set.union(*groups)
    violations = [
        f"unclassified SPPM module: {name}" for name in sorted(actual - classified)
    ]
    violations += [
        f"missing SPPM module: {name}" for name in sorted(classified - actual)
    ]
    violations += [
        f"overlapping SPPM responsibilities: {name}"
        for name in sorted(classified)
        if sum(name in group for group in groups) != 1
    ]
    return violations


def findings(root: Path) -> list[dict]:
    """Check all product cross-package imports and script/example consumers."""
    project = tomllib.loads((root / "pyproject.toml").read_text())
    config = project["tool"]["flo_architecture"]
    interfaces = config["interfaces"]
    paths = sorted((root / "src/flo").rglob("*.py"))
    modules = {module_name(path, root / "src") for path in paths}
    evidence = {}
    classification = sppm_classification_violations(
        modules, config, project["tool"]["importlinter"]["contracts"]
    )
    if classification:
        evidence["SPPM responsibilities"] = classification
    for owner, names in interfaces.items():
        invalid = [
            name
            for name in names
            if name not in modules or not name.startswith(f"flo.{owner}")
        ]
        if invalid:
            evidence[f"{owner} interfaces"] = invalid
    for path in paths:
        importer = module_name(path, root / "src")
        references = import_references(
            path.read_text(),
            importer,
            is_package=path.stem == "__init__",
            modules=modules,
        )
        detected = (
            interface_violations(references, importer, interfaces)
            if importer != "flo"
            else []
        )
        if detected:
            evidence[path.relative_to(root).as_posix()] = detected

    exceptions = config["intermediate_consumers"]
    used_exceptions = {}
    consumers = sorted(
        path
        for folder in ("scripts", "examples")
        for path in (root / folder).rglob("*")
        if path.suffix in {".py", ".ipynb"}
    )
    for path in consumers:
        relative = path.relative_to(root).as_posix()
        references = set()
        sources = [path.read_text()]
        if path.suffix == ".ipynb":
            sources = [
                "\n\n".join(
                    "".join(cell["source"])
                    for cell in json.loads(sources[0])["cells"]
                    if cell["cell_type"] == "code"
                )
            ]
        for source in sources:
            references |= import_references(
                source, "consumer", is_package=False, modules=modules
            )
        exception = exceptions.get(relative, {})
        permitted = set(exception.get("modules", []))
        used_exceptions[relative] = {module for module, _, _ in references} & permitted
        detected = consumer_violations(references, set(interfaces["render"]), permitted)
        if detected:
            evidence[relative] = detected
    for relative, exception in exceptions.items():
        if not exception["reason"].strip() or used_exceptions.get(relative) != set(
            exception["modules"]
        ):
            evidence[f"{relative} exception"] = [
                "Missing reason, file, or stale intermediate imports"
            ]
    return (
        [
            {
                "id": "architecture-interfaces",
                "kind": "boundary violation",
                "evidence": evidence,
            }
        ]
        if evidence
        else []
    )
