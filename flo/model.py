from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    name: str


@dataclass
class Process:
    name: str
    tasks: List[Task] = field(default_factory=list)
