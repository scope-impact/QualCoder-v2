"""
Case Manager ViewModel

Connects the CaseManagerScreen to case use cases and repositories.
Handles data transformation between domain entities and UI DTOs.

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case

Architecture (per SKILL.md - calls use cases directly):
    User Action → ViewModel → Use Cases → Domain → Events
                      ↓                              ↓
                    Repo (queries)          SignalBridge → UI Update
                                                     ↓
                                            ViewModel signals → Screen
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from src.contexts.cases.core.commandHandlers import (
    create_case,
    link_source_to_case,
    remove_case,
    set_case_attribute,
    unlink_source_from_case,
    update_case,
)
from src.contexts.cases.interface.signal_bridge import (
    CaseAttributePayload,
    CasePayload,
    CasesSignalBridge,
    SourceLinkPayload,
)
from src.contexts.projects.core.commands import (
    CreateCaseCommand,
    LinkSourceToCaseCommand,
    RemoveCaseCommand,
    SetCaseAttributeCommand,
    UnlinkSourceFromCaseCommand,
    UpdateCaseCommand,
)
from src.shared.common.types import CaseId
from src.shared.presentation.dto import CaseAttributeDTO, CaseDTO, CaseSummaryDTO

if TYPE_CHECKING:
    from typing import Protocol

    from src.contexts.cases.core.entities import Case
    from src.shared.infra.app_context import CasesContext
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.state import ProjectState

    class CaseRepository(Protocol):
        """Protocol for case repository - allows mock injection for testing."""

        def get_all(self) -> list[Case]: ...
        def get_by_id(self, case_id: CaseId) -> Case | None: ...
        def save(self, case: Case) -> None: ...
        def delete(self, case_id: CaseId) -> bool: ...
        def delete_attribute(self, case_id: CaseId, attr_name: str) -> bool: ...


class CaseManagerViewModel(QObject):
    """
    ViewModel for the Case Manager screen.

    Responsibilities:
    - Transform domain Case entities to UI DTOs
    - Handle user actions by calling use cases directly
    - Provide filtering and search capabilities (via repo)
    - Track selection state
    - React to domain events via SignalBridge

    Follows SKILL.md pattern:
    - Queries → Direct to repo (CQRS)
    - Commands → Use cases
    - Events → SignalBridge → ViewModel signals → Screen

    Signals:
        cases_changed: Emitted when case list changes (create/delete)
        case_updated: Emitted when a case is updated (payload: CaseDTO)
        summary_changed: Emitted when summary statistics change
        error_occurred: Emitted on errors (payload: str)
    """

    # Signals for UI updates
    cases_changed = Signal()  # Emitted when case list changes
    case_updated = Signal(object)  # CaseDTO
    summary_changed = Signal()  # Emitted when summary changes
    error_occurred = Signal(str)  # Error message

    def __init__(
        self,
        case_repo: CaseRepository,
        state: ProjectState,
        event_bus: EventBus,
        cases_ctx: CasesContext | None = None,
        signal_bridge: CasesSignalBridge | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._case_repo = case_repo
        self._state = state
        self._event_bus = event_bus
        self._cases_ctx = cases_ctx
        self._signal_bridge = signal_bridge

        # Selection state
        self._selected_case_id: str | None = None

        # Connect to signal bridge if provided
        if self._signal_bridge is not None:
            self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to CasesSignalBridge signals for reactive updates."""
        if self._signal_bridge is None:
            return

        # Case lifecycle
        self._signal_bridge.case_created.connect(self._on_case_created)
        self._signal_bridge.case_updated.connect(self._on_case_updated)
        self._signal_bridge.case_removed.connect(self._on_case_removed)

        # Attributes
        self._signal_bridge.case_attribute_set.connect(self._on_attribute_set)
        self._signal_bridge.case_attribute_removed.connect(self._on_attribute_removed)

        # Source links
        self._signal_bridge.source_linked.connect(self._on_source_linked)
        self._signal_bridge.source_unlinked.connect(self._on_source_unlinked)

    def teardown(self) -> None:
        """Disconnect all signal bridge connections. Call before replacing this ViewModel."""
        if self._signal_bridge is None:
            return

        self._signal_bridge.case_created.disconnect(self._on_case_created)
        self._signal_bridge.case_updated.disconnect(self._on_case_updated)
        self._signal_bridge.case_removed.disconnect(self._on_case_removed)
        self._signal_bridge.case_attribute_set.disconnect(self._on_attribute_set)
        self._signal_bridge.case_attribute_removed.disconnect(
            self._on_attribute_removed
        )
        self._signal_bridge.source_linked.disconnect(self._on_source_linked)
        self._signal_bridge.source_unlinked.disconnect(self._on_source_unlinked)

    # =========================================================================
    # Signal Bridge Handlers - React to domain events
    # =========================================================================

    def _on_case_created(self, _payload: CasePayload) -> None:
        """Handle case created event."""
        self.cases_changed.emit()
        self.summary_changed.emit()

    def _on_case_updated(self, payload: CasePayload) -> None:
        """Handle case updated event."""
        self._emit_case_update(payload.case_id)

    def _on_case_removed(self, payload: CasePayload) -> None:
        """Handle case removed event."""
        if self._selected_case_id == payload.case_id:
            self._selected_case_id = None
        self.cases_changed.emit()
        self.summary_changed.emit()

    def _on_attribute_set(self, payload: CaseAttributePayload) -> None:
        """Handle attribute set event."""
        self._emit_case_update(payload.case_id)
        self.summary_changed.emit()

    def _on_attribute_removed(self, payload: CaseAttributePayload) -> None:
        """Handle attribute removed event."""
        self._emit_case_update(payload.case_id)
        self.summary_changed.emit()

    def _on_source_linked(self, payload: SourceLinkPayload) -> None:
        """Handle source linked event."""
        self._emit_case_update(payload.case_id)
        self.summary_changed.emit()

    def _on_source_unlinked(self, payload: SourceLinkPayload) -> None:
        """Handle source unlinked event."""
        self._emit_case_update(payload.case_id)
        self.summary_changed.emit()

    def _emit_case_update(self, case_id: str) -> None:
        """Fetch a case by ID and emit case_updated if found."""
        case_dto = self.get_case(case_id)
        if case_dto:
            self.case_updated.emit(case_dto)

    # =========================================================================
    # Load Data (AC #4) - Queries go direct to repo (CQRS)
    # =========================================================================

    def load_cases(self) -> list[CaseDTO]:
        """Load all cases and return as DTOs for UI display."""
        cases = self._case_repo.get_all()
        return [self._case_to_dto(c) for c in cases]

    def get_case(self, case_id: str) -> CaseDTO | None:
        """Get a case by ID and return as DTO, or None if not found."""
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        return self._case_to_dto(case) if case else None

    def get_summary(self) -> CaseSummaryDTO:
        """Get case summary statistics."""
        cases = self._case_repo.get_all()

        # Collect unique attribute names
        unique_attrs: set[str] = set()
        cases_with_sources = 0

        for case in cases:
            for attr in case.attributes:
                unique_attrs.add(attr.name)
            if case.source_ids:
                cases_with_sources += 1

        return CaseSummaryDTO(
            total_cases=len(cases),
            cases_with_sources=cases_with_sources,
            total_attributes=sum(len(c.attributes) for c in cases),
            unique_attribute_names=sorted(unique_attrs),
        )

    # =========================================================================
    # Create Case (AC #1) - Commands go through use cases
    # =========================================================================

    def create_case(
        self,
        name: str,
        description: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """Create a new case. Returns True if successful."""
        result = create_case(
            command=CreateCaseCommand(name=name, description=description, memo=memo),
            state=self._state,
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )
        return result.is_success

    # =========================================================================
    # Update Case - Commands go through use cases
    # =========================================================================

    def update_case(
        self,
        case_id: str,
        name: str | None = None,
        description: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """Update a case. Returns True if successful."""
        result = update_case(
            command=UpdateCaseCommand(
                case_id=case_id, name=name, description=description, memo=memo
            ),
            state=self._state,
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )
        return result.is_success

    # =========================================================================
    # Delete Case - Commands go through use cases
    # =========================================================================

    def delete_case(self, case_id: str) -> bool:
        """Delete a case. Returns True if successful."""
        result = remove_case(
            command=RemoveCaseCommand(case_id=case_id),
            state=self._state,
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )

        if result.is_success and self._selected_case_id == case_id:
            self._selected_case_id = None

        return result.is_success

    # =========================================================================
    # Link Source (AC #2) - Commands go through use cases
    # =========================================================================

    def link_source(self, case_id: str, source_id: str) -> bool:
        """Link a source to a case. Returns True if successful."""
        result = link_source_to_case(
            command=LinkSourceToCaseCommand(case_id=case_id, source_id=source_id),
            state=self._state,
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )
        return result.is_success

    def unlink_source(self, case_id: str, source_id: str) -> bool:
        """Unlink a source from a case. Returns True if successful."""
        result = unlink_source_from_case(
            command=UnlinkSourceFromCaseCommand(case_id=case_id, source_id=source_id),
            state=self._state,
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )
        return result.is_success

    # =========================================================================
    # Add Attribute (AC #3) - Commands go through use cases
    # =========================================================================

    def add_attribute(
        self,
        case_id: str,
        name: str,
        attr_type: str,
        value: str | int | float | bool | None = None,
    ) -> bool:
        """Add or update an attribute on a case. Returns True if successful."""
        result = set_case_attribute(
            command=SetCaseAttributeCommand(
                case_id=case_id, attr_name=name, attr_type=attr_type, attr_value=value
            ),
            state=self._state,
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )
        return result.is_success

    def remove_attribute(self, case_id: str, name: str) -> bool:
        """Remove an attribute from a case. Returns True if successful."""
        if self._case_repo is None:
            return False

        case = self._case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return False

        return self._case_repo.delete_attribute(CaseId(value=case_id), name)

    # =========================================================================
    # Selection
    # =========================================================================

    def select_case(self, case_id: str) -> None:
        """Set the selected case."""
        self._selected_case_id = case_id

    def get_selected_case_id(self) -> str | None:
        """Get the ID of the selected case."""
        return self._selected_case_id

    def clear_selection(self) -> None:
        """Clear case selection."""
        self._selected_case_id = None

    # =========================================================================
    # Search - Queries go direct to repo
    # =========================================================================

    def search_cases(self, query: str) -> list[CaseDTO]:
        """Search cases by name (case-insensitive)."""
        query_lower = query.lower()
        matching = [
            c for c in self._case_repo.get_all() if query_lower in c.name.lower()
        ]
        return [self._case_to_dto(c) for c in matching]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _case_to_dto(self, case: Case) -> CaseDTO:
        """Convert a Case entity to DTO."""
        return CaseDTO(
            id=str(case.id.value),
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=[
                CaseAttributeDTO(
                    name=attr.name,
                    attr_type=attr.attr_type.value,
                    value=attr.value,
                )
                for attr in case.attributes
            ],
            source_ids=[str(sid) for sid in case.source_ids],
            source_count=len(case.source_ids),
            created_at=case.created_at.isoformat() if case.created_at else None,
            updated_at=case.updated_at.isoformat() if case.updated_at else None,
        )
