"""
References Application Layer.

Provides the ReferencesController for handling commands and queries.
"""

from src.application.references.commands import (
    AddReferenceCommand,
    LinkReferenceToSegmentCommand,
    RemoveReferenceCommand,
    UnlinkReferenceFromSegmentCommand,
    UpdateReferenceCommand,
)
from src.application.references.controller import ReferencesControllerImpl

__all__ = [
    "ReferencesControllerImpl",
    "AddReferenceCommand",
    "UpdateReferenceCommand",
    "RemoveReferenceCommand",
    "LinkReferenceToSegmentCommand",
    "UnlinkReferenceFromSegmentCommand",
]
