"""Concrete ELK runtime wrapper backed by Node and elkjs."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from .elk_errors import (
    ElkEngineProtocolError,
    ElkEngineSubprocessError,
    ElkEngineTimeoutError,
    ElkRuntimeUnavailableError,
)

_DEFAULT_TIMEOUT_SECONDS = 10.0


def run_elkjs_layout(
    payload: dict[str, Any],
    *,
    node_command: str = "node",
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Execute ELK via the local Node runtime and return the JSON response."""
    if not shutil.which(node_command):
        raise ElkRuntimeUnavailableError(
            f"Node.js executable '{node_command}' not found on PATH."
        )

    script_path = Path(__file__).with_name("elk_runtime.mjs")
    if not script_path.exists():
        raise ElkRuntimeUnavailableError(
            f"ELK runtime script not found at '{script_path}'."
        )

    try:
        result = subprocess.run(
            [node_command, str(script_path)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise ElkEngineTimeoutError(
            f"ELK runtime timed out after {timeout_seconds:g}s."
        ) from exc
    except OSError as exc:
        raise ElkRuntimeUnavailableError(
            f"Failed to invoke Node.js runtime '{node_command}': {exc}"
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise ElkEngineSubprocessError(
            f"ELK runtime exited with code {result.returncode}"
            + (f": {stderr}" if stderr else "")
        )

    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        stderr = result.stderr.strip()
        detail = f" {stderr}" if stderr else ""
        raise ElkEngineProtocolError(
            f"ELK runtime returned invalid JSON.{detail}"
        ) from exc

    if not isinstance(response, dict):
        raise ElkEngineProtocolError("ELK runtime returned a non-object JSON payload.")
    return response
