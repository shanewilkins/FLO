"""Vulture whitelist symbols for intentional false positives.

Keep this file minimal and remove entries as soon as code no longer needs them.
"""

from typing import Any

_dummy: Any = object()

_dummy.decorator_list  # noqa: B018 - unused attribute (ast node normalization assignment)
_dummy.returns  # noqa: B018 - unused attribute (ast node normalization assignment)
_dummy.inspect_cmd  # noqa: B018 - Click registers this command through a decorator
_dummy.start_end  # noqa: B018 - dataclass field is consumed through dynamic theme adaptation
