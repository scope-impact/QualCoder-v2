"""
Pure Mock Providers for ViewModel Unit Tests

These mocks implement the Provider protocols WITHOUT any real infrastructure.
They are designed to:
1. Return configurable success/failure responses
2. Track method calls for verification
3. Test all error paths in ViewModels
4. Run without database or Qt dependencies

For E2E tests with real infrastructure, see src/tests/e2e/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.shared.core.types import CaseId, SourceId
from src.presentation.dto import CaseSummaryDTO

if TYPE_CHECKING:
    from src.contexts.ai_services.core.entities import (
        CodeSuggestion,
        DuplicateCandidate,
    )
    from src.contexts.coding.core.entities import Code
    from src.contexts.projects.core.entities import Folder, ProjectSummary, Source


# =============================================================================
# Mock Configuration
# =============================================================================


@dataclass
class MockConfig:
    """
    Configuration for mock behavior.

    Use this to configure how mocks respond in tests.
    """

    # Force specific operations to fail
    fail_create: bool = False
    fail_update: bool = False
    fail_delete: bool = False
    fail_link: bool = False
    fail_add_attribute: bool = False
    fail_suggest: bool = False
    fail_detect_duplicates: bool = False
    fail_approve: bool = False

    # Error messages for failures
    create_error: str = "Mock create failure"
    update_error: str = "Mock update failure"
    delete_error: str = "Mock delete failure"
    link_error: str = "Mock link failure"
    attribute_error: str = "Mock attribute failure"
    suggest_error: str = "Mock suggest failure"
    duplicates_error: str = "Mock duplicates failure"
    approve_error: str = "Mock approve failure"


# =============================================================================
# Mock Case Repository (for new ViewModel pattern per SKILL.md)
# =============================================================================


@dataclass
class MockCaseRepository:
    """
    Pure mock implementation of CaseRepository protocol.

    Follows SKILL.md pattern: ViewModels call repos directly for queries.
    """

    config: MockConfig = field(default_factory=MockConfig)

    # Internal state
    _cases: dict[int, Case] = field(default_factory=dict)
    _next_id: int = 1

    # Call tracking for verification
    calls: list[tuple[str, dict]] = field(default_factory=list)

    def _track_call(self, method: str, **kwargs: Any) -> None:
        """Track method calls for test verification."""
        self.calls.append((method, kwargs))

    def reset(self) -> None:
        """Reset mock state for next test."""
        self._cases.clear()
        self._next_id = 1
        self.calls.clear()

    def seed_case(
        self,
        name: str,
        description: str | None = None,
        memo: str | None = None,
        attributes: tuple[CaseAttribute, ...] = (),
        source_ids: tuple[int, ...] = (),
    ) -> Case:
        """Add a case to mock storage for testing."""
        case_id = self._next_id
        self._next_id += 1

        case = Case(
            id=CaseId(value=case_id),
            name=name,
            description=description,
            memo=memo,
            attributes=attributes,
            source_ids=source_ids,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id] = case
        return case

    # =========================================================================
    # Repository Protocol Methods
    # =========================================================================

    def get_all(self) -> list[Case]:
        """Get all cases in the mock storage."""
        self._track_call("get_all")
        return list(self._cases.values())

    def get_by_id(self, case_id: CaseId) -> Case | None:
        """Get a case by ID."""
        self._track_call("get_by_id", case_id=case_id)
        return self._cases.get(case_id.value)

    def get_by_name(self, name: str) -> Case | None:
        """Get a case by name (case-insensitive)."""
        self._track_call("get_by_name", name=name)
        for case in self._cases.values():
            if case.name.lower() == name.lower():
                return case
        return None

    def save(self, case: Case) -> None:
        """Save a case to the mock storage."""
        self._track_call("save", case=case)
        self._cases[case.id.value] = case

    def delete(self, case_id: CaseId) -> bool:
        """Delete a case from the mock storage."""
        self._track_call("delete", case_id=case_id)
        if case_id.value in self._cases:
            del self._cases[case_id.value]
            return True
        return False

    def count(self) -> int:
        """Count cases in storage."""
        return len(self._cases)

    def link_source(self, case_id: CaseId, source_id: SourceId) -> bool:
        """Link a source to a case."""
        self._track_call("link_source", case_id=case_id, source_id=source_id)
        case = self._cases.get(case_id.value)
        if case is None:
            return False
        new_source_ids = tuple(set(case.source_ids) | {source_id.value})
        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=case.attributes,
            source_ids=new_source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id.value] = updated
        return True

    def unlink_source(self, case_id: CaseId, source_id: SourceId) -> bool:
        """Unlink a source from a case."""
        self._track_call("unlink_source", case_id=case_id, source_id=source_id)
        case = self._cases.get(case_id.value)
        if case is None:
            return False
        new_source_ids = tuple(sid for sid in case.source_ids if sid != source_id.value)
        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=case.attributes,
            source_ids=new_source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id.value] = updated
        return True

    def set_attribute(self, case_id: CaseId, attr: CaseAttribute) -> bool:
        """Set an attribute on a case."""
        self._track_call("set_attribute", case_id=case_id, attr=attr)
        case = self._cases.get(case_id.value)
        if case is None:
            return False
        new_attrs = tuple(a for a in case.attributes if a.name != attr.name) + (attr,)
        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=new_attrs,
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id.value] = updated
        return True

    def delete_attribute(self, case_id: CaseId, attr_name: str) -> bool:
        """Delete an attribute from a case."""
        self._track_call("delete_attribute", case_id=case_id, attr_name=attr_name)
        case = self._cases.get(case_id.value)
        if case is None:
            return False
        new_attrs = tuple(a for a in case.attributes if a.name != attr_name)
        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=new_attrs,
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id.value] = updated
        return True


# =============================================================================
# Mock EventBus (for new ViewModel pattern per SKILL.md)
# =============================================================================


@dataclass
class MockEventBus:
    """Mock EventBus for testing - tracks published events."""

    events: list[Any] = field(default_factory=list)
    calls: list[tuple[str, dict]] = field(default_factory=list)

    def publish(self, event: Any) -> None:
        """Publish an event (stores for verification)."""
        self.events.append(event)
        self.calls.append(("publish", {"event": event}))

    def subscribe(self, event_type: type, handler: Any) -> None:
        """Subscribe to an event type (no-op for tests)."""
        self.calls.append(("subscribe", {"event_type": event_type}))

    def reset(self) -> None:
        """Reset mock state."""
        self.events.clear()
        self.calls.clear()


# =============================================================================
# Mock ProjectState (for new ViewModel pattern per SKILL.md)
# =============================================================================


@dataclass
class MockProjectState:
    """Mock ProjectState for testing."""

    project: Any = None  # Mock project
    cases: list[Case] = field(default_factory=list)

    def add_case(self, case: Case) -> None:
        """Add a case to state."""
        self.cases.append(case)

    def remove_case(self, case_id: int) -> None:
        """Remove a case from state."""
        self.cases = [c for c in self.cases if c.id.value != case_id]

    def update_case(self, case: Case) -> None:
        """Update a case in state."""
        self.cases = [c if c.id != case.id else case for c in self.cases]

    def get_case(self, case_id: int) -> Case | None:
        """Get a case by ID."""
        return next((c for c in self.cases if c.id.value == case_id), None)


# =============================================================================
# Mock CasesContext (for new ViewModel pattern per SKILL.md)
# =============================================================================


@dataclass
class MockCasesContext:
    """Mock CasesContext wrapping the mock repository."""

    case_repo: MockCaseRepository = field(default_factory=MockCaseRepository)


# =============================================================================
# Mock CaseManagerProvider (LEGACY - kept for backward compatibility)
# =============================================================================


@dataclass
class MockCaseManagerProvider:
    """
    Pure mock implementation of CaseManagerProvider protocol.

    Features:
    - No database dependency
    - Configurable failures via MockConfig
    - Tracks all method calls
    - In-memory case storage
    """

    config: MockConfig = field(default_factory=MockConfig)

    # Internal state
    _cases: dict[int, Case] = field(default_factory=dict)
    _next_id: int = 1

    # Call tracking for verification
    calls: list[tuple[str, dict]] = field(default_factory=list)

    def _track_call(self, method: str, **kwargs) -> None:
        """Track method calls for test verification."""
        self.calls.append((method, kwargs))

    def reset(self) -> None:
        """Reset mock state for next test."""
        self._cases.clear()
        self._next_id = 1
        self.calls.clear()

    # =========================================================================
    # Seed Data (for setting up test state)
    # =========================================================================

    def seed_case(
        self,
        name: str,
        description: str | None = None,
        memo: str | None = None,
        attributes: tuple[CaseAttribute, ...] = (),
        source_ids: tuple[int, ...] = (),
    ) -> Case:
        """Add a case to mock storage for testing."""
        case_id = self._next_id
        self._next_id += 1

        case = Case(
            id=CaseId(value=case_id),
            name=name,
            description=description,
            memo=memo,
            attributes=attributes,
            source_ids=source_ids,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id] = case
        return case

    # =========================================================================
    # Load Operations
    # =========================================================================

    def get_all_cases(self) -> list[Case]:
        """Get all cases in the mock storage."""
        self._track_call("get_all_cases")
        return list(self._cases.values())

    def get_case(self, case_id: int) -> Case | None:
        """Get a case by ID."""
        self._track_call("get_case", case_id=case_id)
        return self._cases.get(case_id)

    def get_summary(self) -> CaseSummaryDTO:
        """Get case summary statistics."""
        self._track_call("get_summary")

        cases = list(self._cases.values())
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
    # CRUD Operations
    # =========================================================================

    def create_case(
        self,
        name: str,
        description: str | None = None,
        memo: str | None = None,
    ) -> Result[Case, str]:
        """Create a new case."""
        self._track_call("create_case", name=name, description=description, memo=memo)

        if self.config.fail_create:
            return Failure(self.config.create_error)

        # Check for duplicate name
        for case in self._cases.values():
            if case.name == name:
                return Failure(f"Case with name '{name}' already exists")

        case = self.seed_case(name=name, description=description, memo=memo)
        return Success(case)

    def update_case(
        self,
        case_id: int,
        name: str | None = None,
        description: str | None = None,
        memo: str | None = None,
    ) -> Result[Case, str]:
        """Update a case."""
        self._track_call(
            "update_case",
            case_id=case_id,
            name=name,
            description=description,
            memo=memo,
        )

        if self.config.fail_update:
            return Failure(self.config.update_error)

        case = self._cases.get(case_id)
        if case is None:
            return Failure(f"Case {case_id} not found")

        updated = Case(
            id=case.id,
            name=name if name is not None else case.name,
            description=description if description is not None else case.description,
            memo=memo if memo is not None else case.memo,
            attributes=case.attributes,
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id] = updated
        return Success(updated)

    def delete_case(self, case_id: int) -> Result[None, str]:
        """Delete a case."""
        self._track_call("delete_case", case_id=case_id)

        if self.config.fail_delete:
            return Failure(self.config.delete_error)

        if case_id not in self._cases:
            return Failure(f"Case {case_id} not found")

        del self._cases[case_id]
        return Success(None)

    # =========================================================================
    # Source Link Operations
    # =========================================================================

    def link_source(self, case_id: int, source_id: int) -> Result[None, str]:
        """Link a source to a case."""
        self._track_call("link_source", case_id=case_id, source_id=source_id)

        if self.config.fail_link:
            return Failure(self.config.link_error)

        case = self._cases.get(case_id)
        if case is None:
            return Failure(f"Case {case_id} not found")

        # Add source_id to the tuple
        new_source_ids = tuple(set(case.source_ids) | {source_id})
        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=case.attributes,
            source_ids=new_source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id] = updated
        return Success(None)

    def unlink_source(self, case_id: int, source_id: int) -> Result[None, str]:
        """Unlink a source from a case."""
        self._track_call("unlink_source", case_id=case_id, source_id=source_id)

        if self.config.fail_link:
            return Failure(self.config.link_error)

        case = self._cases.get(case_id)
        if case is None:
            return Failure(f"Case {case_id} not found")

        # Remove source_id from the tuple
        new_source_ids = tuple(sid for sid in case.source_ids if sid != source_id)
        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=case.attributes,
            source_ids=new_source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id] = updated
        return Success(None)

    # =========================================================================
    # Attribute Operations
    # =========================================================================

    def add_attribute(
        self,
        case_id: int,
        name: str,
        attr_type: str,
        value: str | int | float | bool | None = None,
    ) -> Result[None, str]:
        """Add or update an attribute on a case."""
        self._track_call(
            "add_attribute",
            case_id=case_id,
            name=name,
            attr_type=attr_type,
            value=value,
        )

        if self.config.fail_add_attribute:
            return Failure(self.config.attribute_error)

        case = self._cases.get(case_id)
        if case is None:
            return Failure(f"Case {case_id} not found")

        # Map string to enum
        type_map = {
            "text": AttributeType.TEXT,
            "number": AttributeType.NUMBER,
            "boolean": AttributeType.BOOLEAN,
            "date": AttributeType.DATE,
        }
        attr_type_enum = type_map.get(attr_type, AttributeType.TEXT)

        # Create new attribute (update if exists)
        new_attr = CaseAttribute(name=name, attr_type=attr_type_enum, value=value)
        new_attrs = tuple(a for a in case.attributes if a.name != name) + (new_attr,)

        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=new_attrs,
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id] = updated
        return Success(None)

    def remove_attribute(self, case_id: int, name: str) -> Result[None, str]:
        """Remove an attribute from a case."""
        self._track_call("remove_attribute", case_id=case_id, name=name)

        if self.config.fail_add_attribute:
            return Failure(self.config.attribute_error)

        case = self._cases.get(case_id)
        if case is None:
            return Failure(f"Case {case_id} not found")

        new_attrs = tuple(a for a in case.attributes if a.name != name)
        updated = Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=new_attrs,
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )
        self._cases[case_id] = updated
        return Success(None)

    # =========================================================================
    # Search Operations
    # =========================================================================

    def search_cases(self, query: str) -> list[Case]:
        """Search cases by name."""
        self._track_call("search_cases", query=query)

        query_lower = query.lower()
        return [c for c in self._cases.values() if query_lower in c.name.lower()]


# =============================================================================
# Mock AICodingProvider
# =============================================================================


@dataclass
class MockAICodingProvider:
    """
    Pure mock implementation of AICodingProvider protocol.

    Features:
    - No AI service dependency
    - Configurable failures via MockConfig
    - Tracks all method calls
    - In-memory suggestion storage
    """

    config: MockConfig = field(default_factory=MockConfig)

    # Internal state
    _suggestions: dict[str, CodeSuggestion] = field(default_factory=dict)
    _duplicates: list[DuplicateCandidate] = field(default_factory=list)

    # Call tracking
    calls: list[tuple[str, dict]] = field(default_factory=list)

    def _track_call(self, method: str, **kwargs) -> None:
        """Track method calls for test verification."""
        self.calls.append((method, kwargs))

    def reset(self) -> None:
        """Reset mock state for next test."""
        self._suggestions.clear()
        self._duplicates.clear()
        self.calls.clear()

    # =========================================================================
    # Seed Data
    # =========================================================================

    def seed_suggestion(self, suggestion: CodeSuggestion) -> None:
        """Add a suggestion to mock storage."""
        self._suggestions[suggestion.id] = suggestion

    def seed_duplicates(self, duplicates: list[DuplicateCandidate]) -> None:
        """Set duplicate candidates for detection."""
        self._duplicates = duplicates

    # =========================================================================
    # Suggestion Operations
    # =========================================================================

    def suggest_codes(
        self,
        text: str,
        source_id: int,
        max_suggestions: int = 5,
    ) -> Result[list[CodeSuggestion], str]:
        """Request AI code suggestions for text."""
        self._track_call(
            "suggest_codes",
            text=text,
            source_id=source_id,
            max_suggestions=max_suggestions,
        )

        if self.config.fail_suggest:
            return Failure(self.config.suggest_error)

        # Return pre-seeded suggestions
        suggestions = list(self._suggestions.values())[:max_suggestions]
        return Success(suggestions)

    def get_suggestion(self, suggestion_id: str) -> CodeSuggestion | None:
        """Get a suggestion by ID from cache."""
        self._track_call("get_suggestion", suggestion_id=suggestion_id)
        return self._suggestions.get(suggestion_id)

    def approve_suggestion(
        self,
        suggestion_id: str,
        name: str,
        color: str,
        memo: str | None = None,
    ) -> Result[Code, str]:
        """Approve a suggestion and create the code."""
        self._track_call(
            "approve_suggestion",
            suggestion_id=suggestion_id,
            name=name,
            color=color,
            memo=memo,
        )

        if self.config.fail_approve:
            return Failure(self.config.approve_error)

        suggestion = self._suggestions.get(suggestion_id)
        if suggestion is None:
            return Failure(f"Suggestion {suggestion_id} not found")

        # Remove from suggestions
        del self._suggestions[suggestion_id]

        # Create mock code - importing here to avoid circular imports
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.shared.core.types import CodeId

        code = Code(
            id=CodeId(value=hash(suggestion_id) % 10000),
            name=name,
            color=Color.from_hex(color),
            memo=memo,
        )
        return Success(code)

    def reject_suggestion(self, suggestion_id: str) -> None:
        """Reject a suggestion (removes from cache)."""
        self._track_call("reject_suggestion", suggestion_id=suggestion_id)
        self._suggestions.pop(suggestion_id, None)

    def dismiss_all_suggestions(self) -> None:
        """Dismiss all current suggestions."""
        self._track_call("dismiss_all_suggestions")
        self._suggestions.clear()

    def has_suggestions(self) -> bool:
        """Check if there are any current suggestions."""
        self._track_call("has_suggestions")
        return len(self._suggestions) > 0

    # =========================================================================
    # Duplicate Detection Operations
    # =========================================================================

    def detect_duplicates(
        self,
        threshold: float = 0.8,
    ) -> Result[list[DuplicateCandidate], str]:
        """Detect duplicate codes in the scheme."""
        self._track_call("detect_duplicates", threshold=threshold)

        if self.config.fail_detect_duplicates:
            return Failure(self.config.duplicates_error)

        return Success(self._duplicates)

    def approve_merge(
        self,
        source_code_id: int,
        target_code_id: int,
    ) -> Result[Code, str]:
        """Approve merging duplicate codes."""
        self._track_call(
            "approve_merge",
            source_code_id=source_code_id,
            target_code_id=target_code_id,
        )

        if self.config.fail_approve:
            return Failure(self.config.approve_error)

        # Create mock merged code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.shared.core.types import CodeId

        code = Code(
            id=CodeId(value=target_code_id),
            name=f"merged_code_{target_code_id}",
            color=Color.from_hex("#888888"),
        )
        return Success(code)


# =============================================================================
# Mock FileManagerController
# =============================================================================


@dataclass
class MockFileManagerController:
    """
    Pure mock implementation of FileManagerController protocol.

    Features:
    - No infrastructure dependency
    - Configurable failures via MockConfig
    - Tracks all method calls
    - In-memory source/folder storage
    """

    config: MockConfig = field(default_factory=MockConfig)

    # Internal state
    _sources: dict[int, Source] = field(default_factory=dict)
    _folders: dict[int, Folder] = field(default_factory=dict)
    _cases: list[Case] = field(default_factory=list)
    _project_summary: ProjectSummary | None = None

    # Call tracking
    calls: list[tuple[str, dict]] = field(default_factory=list)

    def _track_call(self, method: str, **kwargs) -> None:
        """Track method calls for test verification."""
        self.calls.append((method, kwargs))

    def reset(self) -> None:
        """Reset mock state for next test."""
        self._sources.clear()
        self._folders.clear()
        self._cases.clear()
        self._project_summary = None
        self.calls.clear()

    # =========================================================================
    # Seed Data
    # =========================================================================

    def seed_source(self, source: Source) -> None:
        """Add a source to mock storage."""
        self._sources[source.id.value] = source

    def seed_folder(self, folder: Folder) -> None:
        """Add a folder to mock storage."""
        self._folders[folder.id.value] = folder

    def seed_project_summary(self, summary: ProjectSummary) -> None:
        """Set the project summary."""
        self._project_summary = summary

    # =========================================================================
    # Source Operations
    # =========================================================================

    def get_sources(self) -> list[Source]:
        """Get all sources in the current project."""
        self._track_call("get_sources")
        return list(self._sources.values())

    def get_source(self, source_id: int) -> Source | None:
        """Get a specific source by ID."""
        self._track_call("get_source", source_id=source_id)
        return self._sources.get(source_id)

    def add_source(self, command) -> Result:
        """Add a source file to the current project."""
        self._track_call("add_source", command=command)

        if self.config.fail_create:
            return Failure(self.config.create_error)

        return Success(None)

    def remove_source(self, command) -> Result:
        """Remove a source from the current project."""
        self._track_call("remove_source", command=command)

        if self.config.fail_delete:
            return Failure(self.config.delete_error)

        source_id = command.source_id
        if source_id in self._sources:
            del self._sources[source_id]

        return Success(None)

    def open_source(self, command) -> Result:
        """Open a source for viewing/coding."""
        self._track_call("open_source", command=command)
        return Success(None)

    def update_source(self, command) -> Result:
        """Update source metadata."""
        self._track_call("update_source", command=command)

        if self.config.fail_update:
            return Failure(self.config.update_error)

        return Success(None)

    def get_segment_count_for_source(self, source_id: int) -> int:
        """Get the count of coded segments for a source."""
        self._track_call("get_segment_count_for_source", source_id=source_id)
        return 0  # Default to 0 for mocks

    # =========================================================================
    # Folder Operations
    # =========================================================================

    def get_folders(self) -> list[Folder]:
        """Get all folders in the current project."""
        self._track_call("get_folders")
        return list(self._folders.values())

    def create_folder(self, command) -> Result:
        """Create a new folder."""
        self._track_call("create_folder", command=command)

        if self.config.fail_create:
            return Failure(self.config.create_error)

        return Success(None)

    def rename_folder(self, command) -> Result:
        """Rename a folder."""
        self._track_call("rename_folder", command=command)

        if self.config.fail_update:
            return Failure(self.config.update_error)

        return Success(None)

    def delete_folder(self, command) -> Result:
        """Delete an empty folder."""
        self._track_call("delete_folder", command=command)

        if self.config.fail_delete:
            return Failure(self.config.delete_error)

        return Success(None)

    def move_source_to_folder(self, command) -> Result:
        """Move a source to a folder."""
        self._track_call("move_source_to_folder", command=command)

        if self.config.fail_update:
            return Failure(self.config.update_error)

        return Success(None)

    # =========================================================================
    # Case Operations
    # =========================================================================

    def get_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        self._track_call("get_cases")
        return self._cases

    # =========================================================================
    # Project Operations
    # =========================================================================

    def get_project_summary(self) -> ProjectSummary | None:
        """Get summary statistics for the current project."""
        self._track_call("get_project_summary")
        return self._project_summary
