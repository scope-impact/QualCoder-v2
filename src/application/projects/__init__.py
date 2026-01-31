"""
Project Application Services.

This module provides the application layer for project management:
- ProjectController: Command handler for project operations
- ProjectSignalBridge: Domain events to Qt signals translation
"""

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
        "ProjectControllerImpl",
        "ProjectPayload",
        "ProjectSignalBridge",
        "SourcePayload",
    ]
except ImportError:
    # Qt not available - only controller is exported
    __all__ = [
        "ProjectControllerImpl",
    ]
