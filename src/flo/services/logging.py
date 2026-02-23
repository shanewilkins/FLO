import logging

import structlog


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structlog + stdlib logging for CLI usage.

    Idempotent and safe to call multiple times; uses a simple, readable
    processor chain suitable for CLI output (logs go to stderr).
    """
    # Avoid reconfiguring if handlers already present
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(level)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.KeyValueRenderer(key_order=["event", "message"]),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
