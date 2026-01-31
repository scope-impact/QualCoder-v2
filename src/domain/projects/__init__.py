"""
Project Context - Research project lifecycle management.

This bounded context handles:
- Creating and opening QualCoder projects (.qda files)
- Managing source files within projects
- Project navigation and switching
- Recent projects list
"""

from src.domain.projects.entities import (
    Project,
    ProjectId,
    ProjectSummary,
    RecentProject,
    Source,
    SourceStatus,
    SourceType,
)
from src.domain.projects.invariants import (
    can_create_project,
    can_import_source,
    can_open_project,
    detect_source_type,
    is_source_name_unique,
    is_supported_source_type,
    is_valid_project_name,
    is_valid_project_path,
    is_valid_source_name,
)
from src.domain.projects.events import (
    NavigatedToSegment,
    ProjectClosed,
    ProjectCreated,
    ProjectOpened,
    ProjectRenamed,
    ScreenChanged,
    SourceAdded,
    SourceOpened,
    SourceRemoved,
    SourceRenamed,
    SourceStatusChanged,
)
from src.domain.projects.derivers import (
    ProjectState,
    derive_add_source,
    derive_create_project,
    derive_open_project,
    derive_open_source,
    derive_remove_source,
    # Failure reasons
    DuplicateSourceName,
    EmptyProjectName,
    InvalidProjectPath,
    ParentNotWritable,
    ProjectAlreadyExists,
    ProjectNotFound,
    SourceFileNotFound,
    UnsupportedSourceType,
)

__all__ = [
    # Entities
    "Project",
    "ProjectId",
    "ProjectSummary",
    "RecentProject",
    "Source",
    "SourceStatus",
    "SourceType",
    # Invariants
    "can_create_project",
    "can_import_source",
    "can_open_project",
    "detect_source_type",
    "is_source_name_unique",
    "is_supported_source_type",
    "is_valid_project_name",
    "is_valid_project_path",
    "is_valid_source_name",
    # Events
    "NavigatedToSegment",
    "ProjectClosed",
    "ProjectCreated",
    "ProjectOpened",
    "ProjectRenamed",
    "ScreenChanged",
    "SourceAdded",
    "SourceOpened",
    "SourceRemoved",
    "SourceRenamed",
    "SourceStatusChanged",
    # Derivers
    "ProjectState",
    "derive_add_source",
    "derive_create_project",
    "derive_open_project",
    "derive_open_source",
    "derive_remove_source",
    # Failure reasons
    "DuplicateSourceName",
    "EmptyProjectName",
    "InvalidProjectPath",
    "ParentNotWritable",
    "ProjectAlreadyExists",
    "ProjectNotFound",
    "SourceFileNotFound",
    "UnsupportedSourceType",
]
