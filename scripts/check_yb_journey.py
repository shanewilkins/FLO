#!/usr/bin/env python3
"""Rehearse FLO's first-run Yellow Belt authoring journey."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


MAX_JOURNEY_SECONDS = 600.0


def _run(command: list[str], *, cwd: Path) -> dict[str, object]:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return {
        "command": command[1],
        "seconds": round(elapsed, 3),
    }


def rehearse(flo_command: str) -> dict[str, object]:
    """Run the scaffold, validate, render, and export journey in isolation."""
    with tempfile.TemporaryDirectory(prefix="flo-yb-journey-") as raw_directory:
        workspace = Path(raw_directory)
        started = time.perf_counter()
        steps = [
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
        ]
        elapsed = time.perf_counter() - started
        source = workspace / "purchase-request.flo"
        svg = workspace / "purchase-request.svg"
        exported = workspace / "purchase-request.json"
        if not source.is_file() or not svg.is_file() or not exported.is_file():
            raise RuntimeError("Journey did not create all required artifacts")
        if "<svg" not in svg.read_text(encoding="utf-8"):
            raise RuntimeError("Journey render is not an SVG artifact")
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
