"""
Repository Protocols and Backend Abstractions.

This module defines the protocol interfaces that all repository
implementations must follow, enabling swappable backends.
"""

from src.shared.infra.repositories.protocols import (
    CaseRepositoryProtocol,
    CategoryRepositoryProtocol,
    CodeRepositoryProtocol,
    FolderRepositoryProtocol,
    SegmentRepositoryProtocol,
    SourceRepositoryProtocol,
)

__all__ = [
    "CaseRepositoryProtocol",
    "CategoryRepositoryProtocol",
    "CodeRepositoryProtocol",
    "FolderRepositoryProtocol",
    "SegmentRepositoryProtocol",
    "SourceRepositoryProtocol",
]
