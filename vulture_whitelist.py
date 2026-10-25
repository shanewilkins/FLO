"""Vulture whitelist symbols for intentional false positives.

Keep this file minimal and remove entries as soon as code no longer needs them.
"""

from typing import Any

_dummy: Any = object()

_dummy.decorator_list  # noqa: B018 - unused attribute (ast node normalization assignment)
_dummy.returns  # noqa: B018 - unused attribute (ast node normalization assignment)
_dummy.inspect_cmd  # noqa: B018 - Click registers this command through a decorator
_dummy.start_end  # noqa: B018 - dataclass field is consumed through dynamic theme adaptation
_dummy.BRANCH  # noqa: B018 - enum member is consumed through value-based parsing

# Pydantic consumes this configuration through model metadata.
_dummy.model_config  # noqa: B018
_dummy.resolve_aliases_and_profiles  # noqa: B018 - Pydantic validator callback
_dummy.check_child_and_kind_aliases  # noqa: B018 - Pydantic validator callback
_dummy.check_child_owner  # noqa: B018 - Pydantic validator callback
_dummy.reject_endpoint_aliases  # noqa: B018 - Pydantic validator callback
_dummy.accept_target_shorthand  # noqa: B018 - Pydantic validator callback
_dummy.unique_resources  # noqa: B018 - Pydantic validator callback
_dummy.reject_document_aliases  # noqa: B018 - Pydantic validator callback
_dummy.eligible_resources  # noqa: B018 - Pydantic source field
_dummy.spec_version  # noqa: B018 - Pydantic source field
