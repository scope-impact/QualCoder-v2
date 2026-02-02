"""
Projects Bounded Context.

This context manages research projects, source files, and project navigation.

Structure:
- core/ - Domain layer (entities, events, invariants, derivers)
- infra/ - Infrastructure layer (repositories, schema)
"""

# Re-export core domain layer
from src.contexts.projects.core import *  # noqa: F403, F401

# Note: Infrastructure layer should be imported explicitly when needed
# from src.contexts.projects.infra import SQLiteProjectRepository, etc.
