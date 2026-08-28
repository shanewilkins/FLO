"""Vulture whitelist symbols for intentional false positives.

Keep this file minimal and remove entries as soon as code no longer needs them.
"""

_ = object()

_.decorator_list  # unused attribute (ast node normalization assignment)
_.returns  # unused attribute (ast node normalization assignment)
_.inspect_cmd  # Click registers this command through a decorator
_.start_end  # dataclass field is consumed through dynamic theme adaptation
