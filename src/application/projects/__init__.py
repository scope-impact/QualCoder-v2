"""
Project Application Services.

This module provides the application layer for project management:
- Use cases: Functional operations for project management
- ProjectSignalBridge: Domain events to Qt signals translation
- Commands: DTOs for controller operations
"""

# Commands are pure Python - always available
from src.application.projects.commands import (
    AddSourceCommand,
    CreateCaseCommand,
    CreateFolderCommand,
    CreateProjectCommand,
    DeleteFolderCommand,
    LinkSourceToCaseCommand,
    MoveSourceToFolderCommand,
    NavigateToScreenCommand,
    NavigateToSegmentCommand,
    OpenProjectCommand,
    OpenSourceCommand,
    RemoveCaseCommand,
    RemoveSourceCommand,
    RenameFolderCommand,
    SetCaseAttributeCommand,
    UnlinkSourceFromCaseCommand,
    UpdateCaseCommand,
    UpdateSourceCommand,
)

# Use cases are pure Python - always available
from src.application.projects.usecases import (
    close_project,
    create_project,
    open_project,
)

# Signal Bridge has Qt dependencies - conditional import
try:
    from src.application.projects.signal_bridge import (
        FolderPayload,
        ProjectPayload,
        ProjectSignalBridge,
        SourceMovedPayload,
        SourcePayload,
    )

    __all__ = [
        # Commands
        "AddSourceCommand",
        "CreateCaseCommand",
        "CreateFolderCommand",
        "CreateProjectCommand",
        "DeleteFolderCommand",
        "LinkSourceToCaseCommand",
        "MoveSourceToFolderCommand",
        "NavigateToScreenCommand",
        "NavigateToSegmentCommand",
        "OpenProjectCommand",
        "OpenSourceCommand",
        "RemoveCaseCommand",
        "RemoveSourceCommand",
        "RenameFolderCommand",
        "SetCaseAttributeCommand",
        "UnlinkSourceFromCaseCommand",
        "UpdateCaseCommand",
        "UpdateSourceCommand",
        # Use cases
        "create_project",
        "open_project",
        "close_project",
        # Signal Bridge
        "FolderPayload",
        "ProjectPayload",
        "ProjectSignalBridge",
        "SourceMovedPayload",
        "SourcePayload",
    ]
except ImportError:
    # Qt not available - only use cases and commands are exported
    __all__ = [
        # Commands
        "AddSourceCommand",
        "CreateCaseCommand",
        "CreateFolderCommand",
        "CreateProjectCommand",
        "DeleteFolderCommand",
        "LinkSourceToCaseCommand",
        "MoveSourceToFolderCommand",
        "NavigateToScreenCommand",
        "NavigateToSegmentCommand",
        "OpenProjectCommand",
        "OpenSourceCommand",
        "RemoveCaseCommand",
        "RemoveSourceCommand",
        "RenameFolderCommand",
        "SetCaseAttributeCommand",
        "UnlinkSourceFromCaseCommand",
        "UpdateCaseCommand",
        "UpdateSourceCommand",
        # Use cases
        "create_project",
        "open_project",
        "close_project",
    ]
