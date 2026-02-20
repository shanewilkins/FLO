"""Data model for the FLO reference implementation.

This module defines small dataclasses used by the parser and later stages of
the reference implementation.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    """A single named task inside a `Process`."""

    name: str


@dataclass
class Process:
    """A process containing an ordered list of `Task` objects."""

    name: str
    tasks: List[Task] = field(default_factory=list)
