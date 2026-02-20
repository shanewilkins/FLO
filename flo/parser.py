"""Tiny parser for the FLO DSL used in tests and examples.

This module provides a minimal, permissive parser that recognizes simple
declarative lines such as `process NAME` and `task NAME` and returns a small
AST-like mapping. It's intentionally small as a starting point for the
reference implementation.
"""

from typing import Dict, Any

from .model import Process, Task


def parse(text: str) -> Dict[str, Any]:
    """Parse FLO source text and return a mapping with `process` and `tasks`.

    The parser ignores blank lines and lines starting with `#`.
    """
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line and not line.startswith("#")]
    proc = None
    tasks = []
    for line in lines:
        low = line.lower()
        if low.startswith("process "):
            name = line[len("process "):].strip()
            proc = Process(name=name)
        elif low.startswith("task "):
            name = line[len("task "):].strip()
            tasks.append(Task(name=name))
        else:
            # ignore unknown lines for now
            continue
    if proc is None:
        return {"process": None, "tasks": []}
    proc.tasks = tasks
    return {"process": proc, "tasks": tasks}


def parse_file(path: str):
    """Parse a FLO file from `path` and return the parse result."""
    with open(path, "r", encoding="utf-8") as f:
        return parse(f.read())
