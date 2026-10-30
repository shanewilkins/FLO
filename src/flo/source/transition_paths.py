"""Map canonical transition diagnostics back to authored declarations."""

from typing import Any


def authored_transition_path(document: dict[str, Any], path: tuple) -> tuple:
    """Resolve edge ordinals using the compiler's explicit/named edge ordering."""
    if len(path) < 2 or path[0] != "edges" or not isinstance(path[1], int):
        return path
    index = path[1]
    explicit = document.get("transitions")
    if isinstance(explicit, list):
        if 0 <= index < len(explicit) and (
            len(path) == 2 or path[2] in explicit[index]
        ):
            return ("transitions", index, *path[2:])
        return path
    steps = list(_step_paths(document.get("steps", [])))
    declarations = [
        (*step_path, field, name)
        for field in ("outcomes", "routes")
        for step_path, step in steps
        for name in step.get(field, {})
    ]
    if 0 <= index < len(declarations):
        return (*declarations[index], *path[2:])
    return path


def _step_paths(steps: list, prefix: tuple = ("steps",)):
    for index, step in enumerate(steps):
        path = (*prefix, index)
        yield path, step
        yield from _step_paths(step.get("steps", []), (*path, "steps"))
