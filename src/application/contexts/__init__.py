"""
Bounded Context Objects.

Context objects group repositories and services for each bounded context,
providing a clean API for the Coordinator to interact with.
"""

from src.application.contexts.cases import CasesContext
from src.application.contexts.coding import CodingContext
from src.application.contexts.projects import ProjectsContext
from src.application.contexts.sources import SourcesContext

__all__ = [
    "CasesContext",
    "CodingContext",
    "ProjectsContext",
    "SourcesContext",
]
