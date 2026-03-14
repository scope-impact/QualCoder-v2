"""
Cross-Context Sync Handlers.

Provides cross-context handlers for keeping denormalized data in sync
when domain events occur across bounded context boundaries.
"""

from src.shared.core.sync.source_sync_handler import SourceSyncHandler

__all__ = [
    "SourceSyncHandler",
]
