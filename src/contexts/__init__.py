"""
Bounded Contexts Package

Each bounded context is organized as:
    src/contexts/{context}/
        core/       - Domain logic (entities, events, derivers, invariants)
        infra/      - Infrastructure (repositories, schemas, external services)

Available contexts:
    - shared: Cross-cutting types and validation utilities
    - settings: User preferences and configuration
    - cases: Qualitative case management
    - sources: Document and media management
    - projects: Project lifecycle and metadata
    - coding: Qualitative coding and categorization
"""
