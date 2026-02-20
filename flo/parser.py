"""A tiny parser for the FLO DSL used for tests and examples.

This parser is intentionally small: it recognizes lines like:

  process MyProcess
  task DoSomething

and returns a dict-like structure. It's a starting point for the reference implementation.
"""
from typing import Dict, Any
from .model import Process, Task


def parse(text: str) -> Dict[str, Any]:
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l and not l.startswith("#")]
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
    with open(path, "r", encoding="utf-8") as f:
        return parse(f.read())
