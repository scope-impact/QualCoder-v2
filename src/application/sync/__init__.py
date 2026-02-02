"""
Cross-Context Synchronization Handlers.

Provides handlers that keep denormalized data in sync across bounded contexts.
"""

from src.application.sync.source_sync_handler import SourceSyncHandler

__all__ = ["SourceSyncHandler"]
