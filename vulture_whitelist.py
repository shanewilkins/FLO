"""Vulture whitelist for current intentional/known false positives.

This module defines a `whitelist` list used when invoking Vulture so CI
reports focus on new/unexpected findings. Items added here are expected to
be temporary for v0.1 and should be removed (un-whitelisted) as the
corresponding features are implemented.
"""

whitelist = [
    "DECISION",
    "START",
    "END",
    "POOL",
    "NUMBER",
    "TIMESTAMP",
    "exc",
    "exc_type",
    "tb",
    "shutdown_called",
    "_shutdown_called",
    "_active_span_processors",
]
