"""
Source Use Cases - Functional 5-Step Pattern

Use cases for source file operations:
- add_source: Import a source file into the project
- remove_source: Remove a source from the project
- open_source: Open a source for viewing/coding
- update_source: Update source metadata
"""

from src.application.sources.usecases.add_source import add_source
from src.application.sources.usecases.open_source import open_source
from src.application.sources.usecases.remove_source import remove_source
from src.application.sources.usecases.update_source import update_source

__all__ = [
    "add_source",
    "remove_source",
    "open_source",
    "update_source",
]
