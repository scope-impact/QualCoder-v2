"""
Cases Bounded Context.

Groups repositories and services for case management.
Owns: cas_case, cas_attribute, cas_source_link tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.cases.infra.case_repository import SQLiteCaseRepository


@dataclass
class CasesContext:
    """
    Cases bounded context - manages research cases and attributes.

    Provides access to:
    - CaseRepository: CRUD for cases and their attributes

    Publishes events:
    - CaseCreated
    - CaseRenamed
    - CaseDeleted
    - SourceLinkedToCase
    - SourceUnlinkedFromCase

    Subscribes to events:
    - SourceRenamed: Updates denormalized source_name in cas_source_link
    """

    case_repo: SQLiteCaseRepository

    @classmethod
    def create(cls, connection: Connection) -> CasesContext:
        """
        Create a CasesContext with all repositories.

        Args:
            connection: SQLAlchemy connection to the project database

        Returns:
            Configured CasesContext
        """
        from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

        return cls(
            case_repo=SQLiteCaseRepository(connection),
        )
