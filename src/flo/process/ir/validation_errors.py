"""Domain error locations retained for authored provenance enrichment."""

from flo.process.validation_errors import (
    LocatedValidationError as _LocatedValidationError,
)


class _QuantityValidationError(_LocatedValidationError):
    """Carry a quantity field location for source-boundary enrichment."""

    def __init__(self, message: str, field: str) -> None:
        super().__init__(message, (field,))
