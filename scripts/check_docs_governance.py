#!/usr/bin/env python3
"""Validate FLO's domain-based documentation governance."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_STATUSES = {"proposed", "accepted", "superseded"}
PRIORITIES = {"Must", "Should", "Could"}
REQUIREMENT_STATES = {
    "Proposed",
    "Committed",
    "Implemented",
    "Verified",
    "Deferred",
    "Deprecated",
    "Removed",
}
SPECIAL_RELEASES = {"Current", "Ongoing", "Out of scope", "Post-1.0"}
RELEASE_PATTERN = re.compile(r"(?:0\.1\.x|\d+\.\d+(?:\.\d+)?)")

REQUIREMENT_FILES: dict[Path, dict[str, Any]] = {
    Path("docs/requirements/user_requirements.csv"): {
        "id_pattern": re.compile(r"UR-\d{3}"),
        "headers": [
            "Requirement_ID",
            "Journey",
            "Outcome",
            "Rationale",
            "Priority",
            "Target_Release",
            "State",
            "Acceptance",
            "Contract_Refs",
            "Decision_Record",
        ],
        "scope_field": "Journey",
        "statement_field": "Outcome",
        "criteria_field": "Acceptance",
    },
    Path("docs/requirements/technical_requirements.csv"): {
        "id_pattern": re.compile(r"TR-\d{3}"),
        "headers": [
            "Requirement_ID",
            "Area",
            "Constraint",
            "Priority",
            "Target_Release",
            "State",
            "Verification",
            "Contract_Refs",
            "Decision_Record",
        ],
        "scope_field": "Area",
        "statement_field": "Constraint",
        "criteria_field": "Verification",
    },
}


def _repo_relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return path


def _iter_targets(raw_paths: list[str]) -> list[Path]:
    if raw_paths:
        return [REPO_ROOT / raw for raw in raw_paths]

    targets: list[Path] = []
    for pattern in (
        "docs/**/*.md",
        "docs/requirements/*.csv",
        "examples/**/*.flo",
        "schema/*.json",
        "src/flo/schema/*.json",
        "README.md",
        "src/flo/services/errors.py",
    ):
        targets.extend(sorted(REPO_ROOT.glob(pattern)))
    return targets


def _status_header(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines[:12]:
        if line.startswith("Status:"):
            return line.removeprefix("Status:").strip()
    return None


def _warn_adr_status(targets: Iterable[Path], warnings: list[str]) -> None:
    for path in targets:
        rel = _repo_relative(path)
        if rel.suffix != ".md" or rel.parts[:3] != ("docs", "design", "adr"):
            continue
        status = _status_header(path)
        if status is None:
            warnings.append(f"{rel}: ADR is missing a top-level Status header")
        elif status not in ADR_STATUSES:
            allowed = ", ".join(sorted(ADR_STATUSES))
            warnings.append(
                f"{rel}: invalid ADR status '{status}'; expected one of {allowed}"
            )


def _warn_markdown_fences(targets: Iterable[Path], warnings: list[str]) -> None:
    for path in targets:
        rel = _repo_relative(path)
        if rel.suffix != ".md" or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        fence_count = sum(1 for line in lines if line.lstrip().startswith("```"))
        if fence_count % 2:
            warnings.append(f"{rel}: unbalanced Markdown code fences")


def _release_value_is_valid(value: str) -> bool:
    parts = [part.strip() for part in value.split(";")]
    return bool(parts) and all(
        part in SPECIAL_RELEASES or RELEASE_PATTERN.fullmatch(part) is not None
        for part in parts
    )


def _warn_contract_references(
    *, rel: Path, row_number: int, raw_refs: str, warnings: list[str]
) -> None:
    refs = [ref.strip() for ref in raw_refs.split(";") if ref.strip()]
    if not refs:
        warnings.append(f"{rel}:{row_number}: Contract_Refs must not be blank")
        return

    for ref in refs:
        if ref.startswith(("http://", "https://")):
            continue
        path_text = ref.split("#", maxsplit=1)[0]
        if not (REPO_ROOT / path_text).exists():
            warnings.append(
                f"{rel}:{row_number}: Contract_Refs target does not exist: {ref}"
            )


def _read_requirement_rows(
    rel: Path, config: dict[str, Any], warnings: list[str]
) -> list[dict[str, str]]:
    path = REPO_ROOT / rel
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            actual_headers = reader.fieldnames or []
            expected_headers = config["headers"]
            if actual_headers != expected_headers:
                warnings.append(
                    f"{rel}: headers must exactly match Governance v2 schema; "
                    f"expected {expected_headers}, got {actual_headers}"
                )
                return []
            return list(reader)
    except (OSError, csv.Error) as exc:
        warnings.append(f"{rel}: cannot parse CSV: {exc}")
        return []


def _warn_requirement_catalogs(warnings: list[str]) -> None:
    for rel, config in REQUIREMENT_FILES.items():
        rows = _read_requirement_rows(rel, config, warnings)
        seen: set[str] = set()
        id_pattern = config["id_pattern"]

        for row_number, row in enumerate(rows, start=2):
            requirement_id = (row.get("Requirement_ID") or "").strip()
            if id_pattern.fullmatch(requirement_id) is None:
                warnings.append(
                    f"{rel}:{row_number}: invalid requirement ID '{requirement_id}'"
                )
            elif requirement_id in seen:
                warnings.append(
                    f"{rel}:{row_number}: duplicate requirement ID '{requirement_id}'"
                )
            seen.add(requirement_id)

            for column in (
                config["scope_field"],
                config["statement_field"],
                "Priority",
                "Target_Release",
                "State",
                config["criteria_field"],
            ):
                if not (row.get(column) or "").strip():
                    warnings.append(f"{rel}:{row_number}: {column} must not be blank")

            priority = (row.get("Priority") or "").strip()
            if priority not in PRIORITIES:
                warnings.append(f"{rel}:{row_number}: invalid Priority '{priority}'")

            state = (row.get("State") or "").strip()
            if state not in REQUIREMENT_STATES:
                warnings.append(f"{rel}:{row_number}: invalid State '{state}'")
            if state == "Proposed" and not (row.get("Decision_Record") or "").strip():
                warnings.append(
                    f"{rel}:{row_number}: Proposed requirement needs Decision_Record"
                )

            release = (row.get("Target_Release") or "").strip()
            if not _release_value_is_valid(release):
                warnings.append(
                    f"{rel}:{row_number}: invalid Target_Release '{release}'"
                )

            _warn_contract_references(
                rel=rel,
                row_number=row_number,
                raw_refs=(row.get("Contract_Refs") or "").strip(),
                warnings=warnings,
            )


def _warn_current_user_guidance(targets: Iterable[Path], warnings: list[str]) -> None:
    current_user_docs = {
        Path("README.md"),
        Path("docs/Quickstart.md"),
        Path("docs/User_Manual.md"),
    }
    for path in targets:
        rel = _repo_relative(path)
        if rel not in current_user_docs or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if re.search(r"uv run flo render[^\n]*--diagram flowchart", text):
            warnings.append(f"{rel}: active workflow recommends deprecated flowchart")


def _warn_known_files(targets: Iterable[Path], warnings: list[str]) -> None:
    for path in targets:
        rel = _repo_relative(path)
        if rel == Path("docs/CLI_Error_Contract.md"):
            warnings.append(
                "docs/CLI_Error_Contract.md: interface contract belongs under docs/specs/"
            )


def _warn_schema_copies(targets: Iterable[Path], warnings: list[str]) -> None:
    rels = {_repo_relative(path) for path in targets}
    for name in ("flo_trace.json",):
        root_rel = Path("schema") / name
        packaged_rel = Path("src/flo/schema") / name
        if root_rel not in rels and packaged_rel not in rels:
            continue
        root_path = REPO_ROOT / root_rel
        packaged_path = REPO_ROOT / packaged_rel
        if not root_path.is_file() or not packaged_path.is_file():
            warnings.append(f"{name}: root and packaged schema copies must both exist")
        elif root_path.read_bytes() != packaged_path.read_bytes():
            warnings.append(f"{name}: root and packaged schema copies differ")


def _warn_roadmap_contract(warnings: list[str]) -> None:
    roadmap_path = REPO_ROOT / "docs/ROADMAP.md"
    try:
        roadmap = roadmap_path.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(f"docs/ROADMAP.md: cannot read roadmap: {exc}")
        return

    requirements: dict[str, dict[str, str]] = {}
    read_warnings: list[str] = []
    for rel, config in REQUIREMENT_FILES.items():
        for row in _read_requirement_rows(rel, config, read_warnings):
            requirements[row["Requirement_ID"]] = row
    warnings.extend(read_warnings)

    expected_requirements = {
        "UR-050": ("0.4", "Committed"),
        "UR-062": ("Post-1.0", "Committed"),
    }
    for requirement_id, (release, state) in expected_requirements.items():
        row = requirements.get(requirement_id)
        if row is None:
            warnings.append(
                f"docs/ROADMAP.md: required roadmap anchor {requirement_id} is missing"
            )
            continue
        releases = {part.strip() for part in row["Target_Release"].split(";")}
        if release not in releases or row["State"] != state:
            warnings.append(
                f"docs/ROADMAP.md: {requirement_id} must remain {state} for {release}"
            )

    required_phrases = {
        "FLO 0.4 is the minimum viable product milestone": "0.4 MVP boundary",
        "this complete authoring journey takes": "authoring-over-telemetry tradeoff",
        "The first BPMN bridge is a one-way importer": "post-1.0 BPMN boundary",
    }
    for phrase, label in required_phrases.items():
        if phrase not in roadmap:
            warnings.append(f"docs/ROADMAP.md: missing {label}")


def _release_view() -> str:
    grouped: dict[str, list[tuple[str, str, str]]] = {}
    ignored_warnings: list[str] = []
    for rel, config in REQUIREMENT_FILES.items():
        rows = _read_requirement_rows(rel, config, ignored_warnings)
        statement_field = config["statement_field"]
        for row in rows:
            requirement_id = row["Requirement_ID"]
            state = row["State"]
            statement = row[statement_field]
            for release in row["Target_Release"].split(";"):
                grouped.setdefault(release.strip(), []).append(
                    (requirement_id, state, statement)
                )

    lines = [
        "# FLO Requirement Release View",
        "",
        "Generated from the normative requirement registers. Do not edit as a commitment source.",
        "",
    ]
    for release in sorted(grouped, key=_release_sort_key):
        lines.extend((f"## {release}", ""))
        for requirement_id, state, statement in sorted(grouped[release]):
            lines.append(f"- {requirement_id} [{state}]: {statement}")
        lines.append("")
    return "\n".join(lines)


def _release_sort_key(value: str) -> tuple[int, tuple[int, ...] | str]:
    special_order = {
        "Current": 0,
        "0.1.x": 1,
        "Ongoing": 90,
        "1.0": 100,
        "Post-1.0": 110,
        "Out of scope": 120,
    }
    if value in special_order:
        return special_order[value], value
    if RELEASE_PATTERN.fullmatch(value):
        parts = tuple(int(part) for part in value.split("."))
        return 10 + parts[0], parts
    return 999, value


def main() -> int:
    """Check documentation governance and return a status code."""
    parser = argparse.ArgumentParser(prog="check_docs_governance.py")
    parser.add_argument(
        "--strict", action="store_true", help="fail when warnings are emitted"
    )
    parser.add_argument(
        "--release-view",
        action="store_true",
        help="print a deterministic release view from the normative registers",
    )
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if args.release_view:
        print(_release_view())
        return 0

    targets = _iter_targets(args.paths)
    warnings: list[str] = []

    _warn_adr_status(targets, warnings)
    _warn_markdown_fences(targets, warnings)
    _warn_requirement_catalogs(warnings)
    _warn_current_user_guidance(targets, warnings)
    _warn_known_files(targets, warnings)
    _warn_schema_copies(targets, warnings)
    _warn_roadmap_contract(warnings)

    if not warnings:
        print("Documentation governance check passed.")
        return 0

    for warning in warnings:
        print(f"WARN  {warning}")

    if args.strict:
        print(f"Documentation governance check failed with {len(warnings)} warning(s).")
        return 2

    print(f"Documentation governance check completed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
