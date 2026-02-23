import logging

from flo.services.logging import configure_logging


def test_configure_logging_sets_handler_and_level(monkeypatch):
    root = logging.getLogger()
    # backup handlers
    old_handlers = list(root.handlers)
    try:
        # remove handlers to force configuration
        root.handlers.clear()
        configure_logging(level=logging.DEBUG)
        assert root.level == logging.DEBUG
        assert len(root.handlers) >= 1
    finally:
        # restore original handlers
        root.handlers = old_handlers
