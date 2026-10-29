"""Located validation failures shared across process boundaries."""

from flo.errors import ValidationError


class LocatedValidationError(ValidationError):
    """Retain a typed field path for source-boundary enrichment."""

    def __init__(self, message: str, location: tuple[str | int, ...]) -> None:
        """Keep the authored location separate from the rendered diagnostic."""
        super().__init__(message)
        self.location = location
