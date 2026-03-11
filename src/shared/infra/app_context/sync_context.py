"""
SyncContext - Encapsulates cloud sync infrastructure.

Manages Convex client creation, reachability checks, and SyncEngine lifecycle.
Extracted from _create_contexts to keep domain context wiring focused.
"""

from __future__ import annotations

import logging
import socket
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from sqlalchemy import Connection

logger = logging.getLogger(__name__)


@dataclass
class SyncContext:
    """
    Cloud sync infrastructure for a project session.

    Owns the Convex client and SyncEngine lifecycle.
    Created when a project opens; stopped when it closes.
    """

    convex_client: Any = field(default=None, repr=False)
    sync_engine: Any = field(default=None, repr=False)

    @classmethod
    def create(
        cls,
        connection: Connection,
        backend_config: Any,
    ) -> SyncContext:
        """Create a SyncContext, initializing Convex and SyncEngine if configured.

        Args:
            connection: SQLAlchemy connection for SyncEngine
            backend_config: Backend configuration with convex settings
        """
        ctx = cls()

        if not backend_config.uses_convex:
            return ctx

        # Check reachability BEFORE creating the client — the Convex Python
        # client hangs indefinitely on mutation() when the server is down.
        if not _is_convex_reachable(backend_config.convex_url):
            logger.warning(
                "Convex server unreachable — cloud sync disabled this session"
            )
            return ctx

        from src.shared.infra.convex import ConvexClientWrapper

        try:
            ctx.convex_client = ConvexClientWrapper(backend_config.convex_url)
            logger.info(
                "Connected to Convex for cloud sync: %s", backend_config.convex_url
            )
        except Exception as e:
            logger.warning("Failed to connect to Convex (sync disabled): %s", e)
            return ctx

        from src.shared.infra.sync import SyncEngine

        ctx.sync_engine = SyncEngine(connection, ctx.convex_client)
        logger.info("SyncEngine created for SQLite-Convex cloud sync")

        return ctx

    def start(self) -> None:
        """Start the sync engine if available."""
        if self.sync_engine is not None:
            self.sync_engine.start()
            logger.info("SyncEngine started")

    def stop(self) -> None:
        """Stop the sync engine and close the Convex client."""
        if self.sync_engine is not None:
            self.sync_engine.stop()
            self.sync_engine = None

        if self.convex_client is not None:
            self.convex_client.close()
            self.convex_client = None


def _is_convex_reachable(url: str | None) -> bool:
    """Quick TCP check to see if the Convex server is accepting connections."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=2.0):
            return True
    except (OSError, ValueError):
        return False
