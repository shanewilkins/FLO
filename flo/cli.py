"""Command-line interface for the FLO reference implementation.

This module exposes a tiny `main()` function used by the example CLI.
"""

import argparse
import json

from . import parser


def main(argv=None):
    """Parse the given FLO file and print a JSON representation of the AST."""
    p = argparse.ArgumentParser(prog="flo")
    p.add_argument("file", help="FLO file to parse")
    args = p.parse_args(argv)
    result = parser.parse_file(args.file)
    # Convert Process/Task dataclasses to dicts for printing
    proc = result.get("process")
    out = {"process": None, "tasks": []}
    if proc is not None:
        out["process"] = proc.name
        out["tasks"] = [t.name for t in result.get("tasks", [])]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
