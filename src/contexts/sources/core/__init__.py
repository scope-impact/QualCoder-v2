"""
Sources Context - Core (Domain Layer)

Pure domain logic for the Sources bounded context.
Provides entities, invariants, events, failure events, and derivers.

Architecture:
    - entities: Immutable data types (Source, SourceType, SourceStatus, Folder)
    - invariants: Pure predicate functions for business rules
    - events: Success events produced by derivers
    - failure_events: Failure events produced by derivers
    - derivers: Pure event generators (command, state) -> SuccessEvent | FailureEvent
    - services: Domain services (SpeakerDetector, etc.)
"""

# Entities
# Derivers
from src.contexts.sources.core.derivers import (
    ProjectState,
    derive_add_source,
    derive_open_source,
    derive_remove_source,
    derive_update_source,
)
from src.contexts.sources.core.entities import (
    Folder,
    Source,
    SourceStatus,
    SourceType,
)

# Events
from src.contexts.sources.core.events import (
    SourceAdded,
    SourceEvent,
    SourceMovedToFolder,
    SourceOpened,
    SourceRemoved,
    SourceRenamed,
    SourceStatusChanged,
    SourceUpdated,
)

# Failure Events
from src.contexts.sources.core.failure_events import (
    SourceFailureEvent,
    SourceNotAdded,
    SourceNotMoved,
    SourceNotOpened,
    SourceNotRemoved,
    SourceNotUpdated,
)

# Invariants
from src.contexts.sources.core.invariants import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    VIDEO_EXTENSIONS,
    can_import_source,
    detect_source_type,
    is_source_name_unique,
    is_supported_source_type,
    is_valid_source_name,
)

# Services
from src.contexts.sources.core.services import (
    Speaker,
    SpeakerDetector,
    SpeakerSegment,
)

__all__ = [
    # Entities
    "Source",
    "SourceType",
    "SourceStatus",
    "Folder",
    # Invariants
    "TEXT_EXTENSIONS",
    "AUDIO_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "PDF_EXTENSIONS",
    "is_valid_source_name",
    "is_source_name_unique",
    "can_import_source",
    "is_supported_source_type",
    "detect_source_type",
    # Events
    "SourceAdded",
    "SourceRemoved",
    "SourceRenamed",
    "SourceOpened",
    "SourceStatusChanged",
    "SourceUpdated",
    "SourceMovedToFolder",
    "SourceEvent",
    # Failure Events
    "SourceNotAdded",
    "SourceNotRemoved",
    "SourceNotOpened",
    "SourceNotUpdated",
    "SourceNotMoved",
    "SourceFailureEvent",
    # Derivers
    "ProjectState",
    "derive_add_source",
    "derive_remove_source",
    "derive_open_source",
    "derive_update_source",
    # Services
    "Speaker",
    "SpeakerDetector",
    "SpeakerSegment",
]
