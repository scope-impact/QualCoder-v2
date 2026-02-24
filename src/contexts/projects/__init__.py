"""
Projects Bounded Context.

This context manages research projects, source files, and project navigation.

Structure:
- core/ - Domain layer (entities, events, invariants, derivers)
- infra/ - Infrastructure layer (repositories, schema)

Import from submodules directly:
    from src.contexts.projects.core.entities import Project, Source
    from src.contexts.projects.core.events import ProjectCreated
"""
