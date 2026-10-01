"""Stable error contract for ELK engine execution."""

from __future__ import annotations


class ElkEngineError(RuntimeError):
    """Base class for ELK engine invocation failures."""


class ElkRuntimeUnavailableError(ElkEngineError):
    """The ELK runtime or its host executable is unavailable."""


class ElkEngineSubprocessError(ElkEngineError):
    """The ELK subprocess ran but exited unsuccessfully."""


class ElkEngineTimeoutError(ElkEngineError):
    """The ELK subprocess exceeded its allowed runtime."""


class ElkEngineProtocolError(ElkEngineError):
    """The ELK runtime returned a payload that violated the engine contract."""
