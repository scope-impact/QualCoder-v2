"""
Project Application Services.

This module provides the application layer for project management:
- ProjectController: Command handler for project operations
- ProjectSignalBridge: Domain events to Qt signals translation
- Commands: DTOs for controller operations
"""

# Commands are pure Python - always available
from src.application.projects.commands import (
    AddSourceCommand,
    CreateCaseCommand,
    CreateProjectCommand,
    LinkSourceToCaseCommand,
    NavigateToScreenCommand,
    NavigateToSegmentCommand,
    OpenProjectCommand,
    OpenSourceCommand,
    RemoveCaseCommand,
    RemoveSourceCommand,
    SetCaseAttributeCommand,
    UnlinkSourceFromCaseCommand,
    UpdateCaseCommand,
)

# Controller is pure Python - always available
from src.application.projects.controller import ProjectControllerImpl

# Signal Bridge has Qt dependencies - conditional import
try:
    from src.application.projects.signal_bridge import (
        ProjectPayload,
        ProjectSignalBridge,
        SourcePayload,
    )

    __all__ = [
        # Commands
        "AddSourceCommand",
        "CreateCaseCommand",
        "CreateProjectCommand",
        "LinkSourceToCaseCommand",
        "NavigateToScreenCommand",
        "NavigateToSegmentCommand",
        "OpenProjectCommand",
        "OpenSourceCommand",
        "RemoveCaseCommand",
        "RemoveSourceCommand",
        "SetCaseAttributeCommand",
        "UnlinkSourceFromCaseCommand",
        "UpdateCaseCommand",
        # Controller
        "ProjectControllerImpl",
        # Signal Bridge
        "ProjectPayload",
        "ProjectSignalBridge",
        "SourcePayload",
    ]
except ImportError:
    # Qt not available - only controller and commands are exported
    __all__ = [
        # Commands
        "AddSourceCommand",
        "CreateCaseCommand",
        "CreateProjectCommand",
        "LinkSourceToCaseCommand",
        "NavigateToScreenCommand",
        "NavigateToSegmentCommand",
        "OpenProjectCommand",
        "OpenSourceCommand",
        "RemoveCaseCommand",
        "RemoveSourceCommand",
        "SetCaseAttributeCommand",
        "UnlinkSourceFromCaseCommand",
        "UpdateCaseCommand",
        # Controller
        "ProjectControllerImpl",
    ]
