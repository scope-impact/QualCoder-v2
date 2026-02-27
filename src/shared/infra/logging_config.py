"""
Centralized logging configuration for QualCoder v2.

Configures a consistent logging hierarchy under the ``qualcoder`` root logger.
Module loggers follow the naming convention::

    qualcoder.<context>.<layer>

Examples:
    qualcoder.coding.core
    qualcoder.sources.infra
    qualcoder.shared.event_bus
    qualcoder.mcp

Usage:
    # Once at startup (in main.py, before anything else)
    from src.shared.infra.logging_config import configure_logging
    configure_logging()

    # In any module
    import logging
    logger = logging.getLogger("qualcoder.coding.core")
    logger.info("Code created: id=%s", code_id)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def configure_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    enable_console: bool = True,
) -> None:
    """
    Configure the ``qualcoder`` logger hierarchy.

    Args:
        level: Root log level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional file path for persistent log output.
        enable_console: Whether to emit to stderr (default True).
    """
    root = logging.getLogger("qualcoder")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Prevent duplicate handlers on repeated calls
    if root.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if enable_console:
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(formatter)
        root.addHandler(console)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
