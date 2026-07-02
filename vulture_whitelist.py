"""Vulture whitelist symbols for intentional false positives.

Keep this file minimal and remove entries as soon as code no longer needs them.
"""

_.decorator_list  # unused attribute (ast node normalization assignment)
_.returns  # unused attribute (ast node normalization assignment)
