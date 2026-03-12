"""
SyncContext - Encapsulates cloud sync infrastructure.

Manages Convex client creation, reachability checks, and SyncEngine lifecycle.
Extracted from _create_contexts to keep domain context wiring focused.
"""

from __future__ import annotations

import logging
import socket
import threading
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
        """Create a SyncContext, initializing SyncEngine if configured.

        The Convex client connection is deferred to a background thread
        so the main/UI thread is never blocked by network I/O.

        Args:
            connection: SQLAlchemy connection for SyncEngine
            backend_config: Backend configuration with convex settings
        """
        ctx = cls()

        if not backend_config.uses_convex:
            return ctx

        from src.shared.infra.sync import SyncEngine

        # Create SyncEngine in offline mode (no Convex client yet).
        # It will queue outbound changes until the client is connected.
        ctx.sync_engine = SyncEngine(connection, convex_client=None)
        logger.info("SyncEngine created in offline mode (Convex check deferred)")

        # Check reachability and connect in a background thread so the
        # UI is never blocked by the up-to-2s TCP handshake timeout.
        threading.Thread(
            target=ctx._connect_convex_async,
            args=(backend_config.convex_url,),
            daemon=True,
            name="ConvexReachabilityCheck",
        ).start()

        return ctx

    def _connect_convex_async(self, convex_url: str) -> None:
        """Background thread: check reachability and inject Convex client."""
        if not _is_convex_reachable(convex_url):
            logger.warning(
                "Convex server unreachable — cloud sync disabled this session"
            )
            return

        from src.shared.infra.convex import ConvexClientWrapper

        try:
            client = ConvexClientWrapper(convex_url)
            logger.info("Connected to Convex for cloud sync: %s", convex_url)
        except Exception as e:
            logger.warning("Failed to connect to Convex (sync disabled): %s", e)
            return

        self.convex_client = client
        if self.sync_engine is not None:
            self.sync_engine.set_convex_client(client)
            logger.info("SyncEngine upgraded to online mode")

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
