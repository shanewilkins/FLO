import logging

import structlog

from flo.services.errors import handle_error
from flo.services.logging import configure_logging


def test_handle_error_emits_to_stderr(capsys):
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    try:
        root.handlers.clear()
        configure_logging(level=logging.INFO)
        logger = structlog.get_logger()
        handle_error("posix-stderr-check", logger)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "posix-stderr-check" in captured.err
    finally:
        root.handlers = old_handlers
        root.setLevel(old_level)
