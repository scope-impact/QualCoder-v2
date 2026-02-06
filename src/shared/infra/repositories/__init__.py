"""
Repository Protocols and Backend Abstractions.

This module defines the protocol interfaces that all repository
implementations must follow, enabling swappable backends (SQLite, Convex, etc.).
"""

from src.shared.infra.repositories.factory import RepositoryFactory, RepositorySet
from src.shared.infra.repositories.protocols import (
    BackendType,
    CaseRepositoryProtocol,
    CategoryRepositoryProtocol,
    CodeRepositoryProtocol,
    FolderRepositoryProtocol,
    SegmentRepositoryProtocol,
    SourceRepositoryProtocol,
)

__all__ = [
    "BackendType",
    "CaseRepositoryProtocol",
    "CategoryRepositoryProtocol",
    "CodeRepositoryProtocol",
    "FolderRepositoryProtocol",
    "RepositoryFactory",
    "RepositorySet",
    "SegmentRepositoryProtocol",
    "SourceRepositoryProtocol",
]
