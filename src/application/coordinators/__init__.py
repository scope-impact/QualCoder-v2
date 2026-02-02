"""
Per-Context Coordinators.

This package splits the ApplicationCoordinator into isolated per-context
coordinators to enable parallel sub-agent development without merge conflicts.

Each coordinator owns a specific bounded context:
- SettingsCoordinator: Theme, font, language, backup, AV coding settings
- ProjectsCoordinator: Project lifecycle (open/create/close)
- SourcesCoordinator: Source CRUD operations
- CasesCoordinator: Case CRUD and linking
- FoldersCoordinator: Folder CRUD
- NavigationCoordinator: Screen and segment navigation

The ApplicationCoordinator remains as a thin facade that delegates to these
sub-coordinators while maintaining backward compatibility.
"""

from src.application.coordinators.base import (
    BaseCoordinator,
    CoordinatorInfrastructure,
)
from src.application.coordinators.cases_coordinator import CasesCoordinator
from src.application.coordinators.coding_coordinator import CodingCoordinator
from src.application.coordinators.folders_coordinator import FoldersCoordinator
from src.application.coordinators.navigation_coordinator import NavigationCoordinator
from src.application.coordinators.projects_coordinator import ProjectsCoordinator
from src.application.coordinators.settings_coordinator import SettingsCoordinator
from src.application.coordinators.sources_coordinator import SourcesCoordinator

__all__ = [
    "BaseCoordinator",
    "CasesCoordinator",
    "CodingCoordinator",
    "CoordinatorInfrastructure",
    "FoldersCoordinator",
    "NavigationCoordinator",
    "ProjectsCoordinator",
    "SettingsCoordinator",
    "SourcesCoordinator",
]
