"""
Project Use Cases - Functional 5-Step Pattern

Use cases for project lifecycle operations:
- create_project: Create a new .qda project file
- open_project: Open an existing project
- close_project: Close the current project
"""

from src.application.projects.usecases.close_project import close_project
from src.application.projects.usecases.create_project import create_project
from src.application.projects.usecases.open_project import open_project

__all__ = [
    "create_project",
    "open_project",
    "close_project",
]
