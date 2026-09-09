#!/usr/bin/env python3
"""Rehearse FLO's first-run White Belt authoring journey.

The established script name is retained for release-automation compatibility.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_JOURNEY_SECONDS = 600.0


def _run(
    command: list[str], *, cwd: Path, label: str | None = None
) -> dict[str, object]:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return {
        "command": label or command[1],
        "seconds": round(elapsed, 3),
    }


def rehearse(flo_command: str) -> dict[str, object]:
    """Run the scaffold, validate, render, and export journey in isolation."""
    with tempfile.TemporaryDirectory(prefix="flo-yb-journey-") as raw_directory:
        workspace = Path(raw_directory)
        resolved_flo = shutil.which(flo_command) or flo_command
        sibling_python = Path(resolved_flo).with_name("python")
        python_command = (
            str(sibling_python) if sibling_python.is_file() else sys.executable
        )
        started = time.perf_counter()
        steps = [
            _run([flo_command, "--version"], cwd=workspace, label="version"),
            _run(
                [
                    flo_command,
                    "new",
                    "purchase-request.flo",
                    "--name",
                    "Purchase Request",
                ],
                cwd=workspace,
            ),
            _run(
                [flo_command, "validate", "purchase-request.flo"],
                cwd=workspace,
            ),
            _run(
                [
                    flo_command,
                    "render",
                    "purchase-request.flo",
                    "--layout-width",
                    "8.5in",
                    "--layout-height",
                    "11in",
                    "--render-to",
                    "purchase-request.svg",
                ],
                cwd=workspace,
            ),
            _run(
                [
                    flo_command,
                    "export",
                    "purchase-request.flo",
                    "-o",
                    "purchase-request.json",
                ],
                cwd=workspace,
            ),
            _run(
                [
                    python_command,
                    "-c",
                    (
                        "from pathlib import Path; import flo; "
                        "source = Path('purchase-request.flo').read_text(); "
                        "validated = flo.validate(source, source_path='purchase-request.flo'); "
                        "assert validated.ok; "
                        "exported = flo.export(source, source_path='purchase-request.flo'); "
                        "assert exported.ok and exported.value"
                    ),
                ],
                cwd=workspace,
                label="public-api",
            ),
        ]
        elapsed = time.perf_counter() - started
        source = workspace / "purchase-request.flo"
        svg = workspace / "purchase-request.svg"
        exported = workspace / "purchase-request.json"
        if not source.is_file() or not svg.is_file() or not exported.is_file():
            raise RuntimeError("Journey did not create all required artifacts")
        svg_content = svg.read_text(encoding="utf-8")
        if "<svg" not in svg_content:
            raise RuntimeError("Journey render is not an SVG artifact")
        svg_root = svg_content.partition(">")[0]
        if (
            'data-flo-diagram="sppm"' not in svg_root
            or 'width="816"' not in svg_root
            or 'height="1056"' not in svg_root
        ):
            raise RuntimeError(
                "Journey render is not a default SPPM artifact on an exact "
                "8.5-by-11-inch canvas"
            )
        payload = json.loads(exported.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not payload.get("nodes"):
            raise RuntimeError("Journey export is not canonical process JSON")
        if elapsed > MAX_JOURNEY_SECONDS:
            raise RuntimeError(
                f"Journey took {elapsed:.1f}s; budget is {MAX_JOURNEY_SECONDS:.0f}s"
            )
        return {
            "status": "passed",
            "elapsed_seconds": round(elapsed, 3),
            "budget_seconds": MAX_JOURNEY_SECONDS,
            "steps": steps,
            "artifacts": [source.name, svg.name, exported.name],
        }


def main() -> int:
    """Run the automated journey rehearsal and print JSON evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--flo",
        default=shutil.which("flo") or "flo",
        help="Path to the FLO executable under test.",
    )
    args = parser.parse_args()
    print(json.dumps(rehearse(args.flo), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
