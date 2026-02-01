"""
Privacy Controller - Application Service.

Orchestrates privacy domain operations following the 5-step pattern:
1. Validate (Pydantic does automatically)
2. Build current state
3. Derive event (call pure domain function)
4. Persist on success
5. Publish event

This is the "Imperative Shell" that coordinates the "Functional Core".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.privacy.commands import (
    ApplyPseudonymsCommand,
    CreatePseudonymCommand,
    DeletePseudonymCommand,
    RevertAnonymizationCommand,
    UpdatePseudonymCommand,
)
from src.domain.privacy.derivers import (
    PrivacyState,
    derive_create_pseudonym,
    derive_delete_pseudonym,
    derive_update_pseudonym,
)
from src.domain.privacy.entities import (
    AnonymizationSession,
    AnonymizationSessionId,
    Pseudonym,
    PseudonymCategory,
    PseudonymId,
)
from src.domain.privacy.events import (
    AnonymizationReverted,
    PseudonymCreated,
    PseudonymDeleted,
    PseudonymUpdated,
    PseudonymsApplied,
)
from src.domain.privacy.services.anonymizer import TextAnonymizer
from src.domain.shared.types import SourceId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.privacy.repositories import (
        SQLiteAnonymizationSessionRepository,
        SQLitePseudonymRepository,
    )


@dataclass(frozen=True)
class ApplyPseudonymsResult:
    """Result of applying pseudonyms to text."""

    anonymized_text: str
    session_id: AnonymizationSessionId
    replacement_count: int


@dataclass(frozen=True)
class RevertResult:
    """Result of reverting anonymization."""

    original_text: str
    session_id: AnonymizationSessionId


class PrivacyController:
    """
    Application service for privacy operations.

    Orchestrates domain services, repositories, and event publishing.
    Follows the 5-step controller pattern.
    """

    def __init__(
        self,
        pseudonym_repo: SQLitePseudonymRepository,
        session_repo: SQLiteAnonymizationSessionRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            pseudonym_repo: Repository for Pseudonym entities
            session_repo: Repository for AnonymizationSession entities
            event_bus: Event bus for publishing domain events
        """
        self._pseudonym_repo = pseudonym_repo
        self._session_repo = session_repo
        self._event_bus = event_bus

    # =========================================================================
    # Pseudonym Commands
    # =========================================================================

    def create_pseudonym(
        self, command: CreatePseudonymCommand
    ) -> Result[Pseudonym, str]:
        """
        Create a new pseudonym mapping.

        Args:
            command: Create command with real_name, alias, category

        Returns:
            Success with Pseudonym on success, Failure with reason on error
        """
        # Step 2: Build current state
        state = self._build_privacy_state()

        # Step 3: Derive event (pure function)
        result = derive_create_pseudonym(
            real_name=command.real_name,
            alias=command.alias,
            category=command.category,
            notes=command.notes,
            state=state,
        )

        # Step 4: Handle failure or persist
        if isinstance(result, Failure):
            return result

        event: PseudonymCreated = result

        # Create entity from event
        pseudonym = Pseudonym(
            id=event.pseudonym_id,
            real_name=event.real_name,
            alias=event.alias,
            category=PseudonymCategory(event.category),
            notes=command.notes,
        )

        self._pseudonym_repo.save(pseudonym)

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(pseudonym)

    def update_pseudonym(
        self, command: UpdatePseudonymCommand
    ) -> Result[Pseudonym, str]:
        """
        Update an existing pseudonym.

        Args:
            command: Update command with pseudonym_id and new values

        Returns:
            Success with updated Pseudonym on success, Failure on error
        """
        # Step 2: Build state
        state = self._build_privacy_state()

        # Step 3: Derive event
        result = derive_update_pseudonym(
            pseudonym_id=PseudonymId(value=command.pseudonym_id),
            new_alias=command.new_alias,
            new_notes=command.new_notes,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: PseudonymUpdated = result

        # Step 4: Get existing and update
        existing = self._pseudonym_repo.get_by_id(
            PseudonymId(value=command.pseudonym_id)
        )
        if existing is None:
            return Failure("Pseudonym not found")

        updated = existing
        if command.new_alias:
            updated = updated.with_alias(command.new_alias)
        if command.new_notes is not None:
            updated = updated.with_notes(command.new_notes)

        self._pseudonym_repo.save(updated)

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(updated)

    def delete_pseudonym(
        self, command: DeletePseudonymCommand
    ) -> Result[None, str]:
        """
        Delete a pseudonym.

        Args:
            command: Delete command with pseudonym_id

        Returns:
            Success on success, Failure on error
        """
        # Step 2: Build state
        state = self._build_privacy_state()

        # Step 3: Derive event
        result = derive_delete_pseudonym(
            pseudonym_id=PseudonymId(value=command.pseudonym_id),
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: PseudonymDeleted = result

        # Step 4: Delete from repository
        self._pseudonym_repo.delete(PseudonymId(value=command.pseudonym_id))

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(None)

    # =========================================================================
    # Pseudonym Queries
    # =========================================================================

    def get_all_pseudonyms(self) -> list[Pseudonym]:
        """Get all pseudonyms."""
        return self._pseudonym_repo.get_all()

    def get_pseudonyms_by_category(
        self, category: PseudonymCategory
    ) -> list[Pseudonym]:
        """Get pseudonyms filtered by category."""
        return self._pseudonym_repo.get_by_category(category)

    # =========================================================================
    # Apply Pseudonyms
    # =========================================================================

    def apply_pseudonyms(
        self, command: ApplyPseudonymsCommand
    ) -> Result[ApplyPseudonymsResult, str]:
        """
        Apply pseudonyms to source text.

        Args:
            command: Apply command with source_id, source_text, options

        Returns:
            Success with ApplyPseudonymsResult on success, Failure on error
        """
        # Get pseudonyms to apply
        if command.pseudonym_ids:
            pseudonyms = [
                self._pseudonym_repo.get_by_id(PseudonymId(value=pid))
                for pid in command.pseudonym_ids
            ]
            pseudonyms = [p for p in pseudonyms if p is not None]
        else:
            pseudonyms = self._pseudonym_repo.get_all()

        if not pseudonyms:
            return Failure("No pseudonyms to apply")

        # Apply anonymization using domain service
        anonymizer = TextAnonymizer(command.source_text)
        anon_result = anonymizer.apply_pseudonyms(
            pseudonyms=pseudonyms,
            match_case=command.match_case,
            whole_word=command.whole_word,
        )

        # Create session for reversal
        session_id = AnonymizationSessionId.new()
        session = AnonymizationSession(
            id=session_id,
            source_id=SourceId(value=command.source_id),
            original_text=command.source_text,
            pseudonym_ids=tuple(p.id for p in pseudonyms),
            replacements=anon_result.replacements,
        )

        self._session_repo.save(session)

        # Publish event
        event = PseudonymsApplied.create(
            session_id=session_id,
            source_id=SourceId(value=command.source_id),
            pseudonym_count=len(pseudonyms),
            replacement_count=len(anon_result.replacements),
        )
        self._event_bus.publish(event)

        return Success(
            ApplyPseudonymsResult(
                anonymized_text=anon_result.anonymized_text,
                session_id=session_id,
                replacement_count=len(anon_result.replacements),
            )
        )

    # =========================================================================
    # Revert Anonymization
    # =========================================================================

    def revert_anonymization(
        self, command: RevertAnonymizationCommand
    ) -> Result[RevertResult, str]:
        """
        Revert anonymization to original text.

        Args:
            command: Revert command with source_id, session_id

        Returns:
            Success with RevertResult on success, Failure on error
        """
        # Get session
        if command.session_id:
            session = self._session_repo.get_by_id(
                AnonymizationSessionId(value=command.session_id)
            )
        else:
            session = self._session_repo.get_active_session(
                SourceId(value=command.source_id)
            )

        if session is None:
            return Failure("Anonymization session not found")

        if not session.is_reversible():
            return Failure("Session has already been reverted")

        # Mark as reverted
        self._session_repo.mark_reverted(session.id)

        # Publish event
        event = AnonymizationReverted.create(
            session_id=session.id,
            source_id=session.source_id,
        )
        self._event_bus.publish(event)

        return Success(
            RevertResult(
                original_text=session.original_text,
                session_id=session.id,
            )
        )

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _build_privacy_state(self) -> PrivacyState:
        """Build current privacy state from repositories."""
        pseudonyms = self._pseudonym_repo.get_all()
        # Sessions not needed for pseudonym operations
        return PrivacyState(
            existing_pseudonyms=tuple(pseudonyms),
            existing_sessions=(),
        )
