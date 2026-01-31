"""
Project Application Services.

This module provides the application layer for project management:
- ProjectController: Command handler for project operations
- ProjectSignalBridge: Domain events to Qt signals translation
"""

from src.application.projects.controller import ProjectControllerImpl
from src.application.projects.signal_bridge import (
    ProjectPayload,
    ProjectSignalBridge,
    SourcePayload,
)

__all__ = [
    "ProjectControllerImpl",
    "ProjectPayload",
    "ProjectSignalBridge",
    "SourcePayload",
]
