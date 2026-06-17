"""Build side-by-side SPPM artifacts for two strategy profiles."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

DEFAULT_MANIFEST = REPO_ROOT / "examples" / "conformance" / "sppm_corpus.json"
DEFAULT_OUTDIR = REPO_ROOT / "renders" / "conformance" / "sppm_profile_compare"
DEFAULT_FROZEN_PROFILE = (
    "part=branch_aligned|port=fixed_order|anchors=always|space=balanced"
)
ENV_PARTITION_MODE = "FLO_SPPM_PARTITION_MODE"
ENV_PORT_CONSTRAINTS = "FLO_SPPM_PORT_CONSTRAINTS"
ENV_HELPER_ANCHORS = "FLO_SPPM_HELPER_ANCHORS"
ENV_SPACING_PROFILE = "FLO_SPPM_SPACING_PROFILE"


def main() -> int:
    parser = argparse.ArgumentParser(prog="compare_sppm_profiles.py")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to the SPPM corpus manifest JSON.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help="Root output directory for comparison artifacts.",
    )
    parser.add_argument(
        "--left-profile",
        default=DEFAULT_FROZEN_PROFILE,
        help="Profile id for the left/frozen build.",
    )
    parser.add_argument(
        "--right-profile",
        required=True,
        help="Profile id for the right/candidate build.",
    )
    parser.add_argument(
        "--left-label",
        default="frozen",
        help="Directory label for the left profile output.",
    )
    parser.add_argument(
        "--right-label",
        default="candidate",
        help="Directory label for the right profile output.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Optional case id to include. Repeat to limit review scope.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the output root before generation.",
    )
    args = parser.parse_args()

    from build_sppm_baseline_artifacts import (
        _build_case,
        _filter_cases,
        _load_cases,
        _resolve_repo_path,
    )

    manifest = _resolve_repo_path(args.manifest)
    outdir = _resolve_repo_path(args.outdir)
    if args.clean and outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    cases = _filter_cases(_load_cases(manifest), case_ids=args.case_id)
    left_profile = _parse_profile_id(args.left_profile)
    right_profile = _parse_profile_id(args.right_profile)

    for label, profile in (
        (args.left_label, left_profile),
        (args.right_label, right_profile),
    ):
        profile_outdir = outdir / label
        profile_outdir.mkdir(parents=True, exist_ok=True)
        with _temporary_profile_env(profile):
            for case in cases:
                _build_case(case=case, outdir=profile_outdir)

    _write_summary(
        outdir=outdir,
        manifest=manifest,
        case_ids=[str(case["id"]) for case in cases],
        left_label=args.left_label,
        left_profile=args.left_profile,
        right_label=args.right_label,
        right_profile=args.right_profile,
    )
    print(f"Wrote comparison artifacts under {outdir.relative_to(REPO_ROOT)}")
    return 0


def _parse_profile_id(profile_id: str) -> dict[str, str]:
    parts = {
        "part": "chain_progressive",
        "port": "fixed_order",
        "anchors": "off",
        "space": "balanced",
    }
    for segment in str(profile_id).split("|"):
        key, sep, value = segment.partition("=")
        if not sep:
            raise ValueError(f"Invalid profile segment: {segment}")
        key = key.strip().lower()
        value = value.strip().lower()
        if key not in parts or not value:
            raise ValueError(f"Invalid profile segment: {segment}")
        parts[key] = value
    return {
        ENV_PARTITION_MODE: parts["part"],
        ENV_PORT_CONSTRAINTS: parts["port"],
        ENV_HELPER_ANCHORS: parts["anchors"],
        ENV_SPACING_PROFILE: parts["space"],
    }


@contextmanager
def _temporary_profile_env(profile: dict[str, str]) -> Iterator[None]:
    previous = {name: os.getenv(name) for name in profile}
    try:
        for name, value in profile.items():
            os.environ[name] = value
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _write_summary(
    *,
    outdir: Path,
    manifest: Path,
    case_ids: list[str],
    left_label: str,
    left_profile: str,
    right_label: str,
    right_profile: str,
) -> None:
    summary = {
        "manifest": str(manifest.relative_to(REPO_ROOT)),
        "case_ids": case_ids,
        "profiles": {
            left_label: left_profile,
            right_label: right_profile,
        },
    }
    (outdir / "comparison.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "comparison.md").write_text(
        "\n".join(
            [
                "# SPPM Profile Comparison",
                "",
                f"- Manifest: `{manifest.relative_to(REPO_ROOT)}`",
                f"- Cases: {', '.join(case_ids)}",
                f"- {left_label}: `{left_profile}`",
                f"- {right_label}: `{right_profile}`",
                "",
                "## Output Roots",
                "",
                f"- `{(outdir / left_label).relative_to(REPO_ROOT)}`",
                f"- `{(outdir / right_label).relative_to(REPO_ROOT)}`",
                "",
                "Review the paired `render.svg`, `layout_result.json`, and `metadata.json` files for each case.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())