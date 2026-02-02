"""
Factory functions for creating connected UI components.

These factories wire up the full stack:
    Presentation ← ViewModel ← Use Cases ← Repositories ← SQLite
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result
from sqlalchemy import Connection, create_engine
from sqlalchemy.engine import Engine

from src.application.coding import CodingSignalBridge
from src.application.coding.usecases import (
    apply_code,
    change_code_color,
    create_category,
    create_code,
    delete_category,
    delete_code,
    get_all_categories,
    get_all_codes,
    get_segments_for_code,
    get_segments_for_source,
    merge_codes,
    move_code_to_category,
    remove_segment,
    rename_code,
    update_code_memo,
)
from src.application.contexts.coding import CodingContext as AppCodingContext
from src.application.event_bus import EventBus
from src.contexts.coding.infra import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
    create_all,
)
from src.presentation.viewmodels import TextCodingViewModel

if TYPE_CHECKING:
    pass


class CodingOperations:
    """
    Adapter that provides controller-like interface using functional use cases.

    This replaces the old CodingControllerImpl with use case delegation.
    """

    def __init__(
        self,
        coding_ctx: AppCodingContext,
        event_bus: EventBus,
    ) -> None:
        self._coding_ctx = coding_ctx
        self._event_bus = event_bus

    def create_code(self, command) -> Result:
        """Create a new code."""
        return create_code(command, self._coding_ctx, self._event_bus)

    def rename_code(self, command) -> Result:
        """Rename a code."""
        return rename_code(command, self._coding_ctx, self._event_bus)

    def change_code_color(self, command) -> Result:
        """Change a code's color."""
        return change_code_color(command, self._coding_ctx, self._event_bus)

    def delete_code(self, command) -> Result:
        """Delete a code."""
        return delete_code(command, self._coding_ctx, self._event_bus)

    def merge_codes(self, command) -> Result:
        """Merge codes."""
        return merge_codes(command, self._coding_ctx, self._event_bus)

    def update_code_memo(self, command) -> Result:
        """Update a code's memo."""
        return update_code_memo(command, self._coding_ctx, self._event_bus)

    def move_code_to_category(self, command) -> Result:
        """Move a code to a category."""
        return move_code_to_category(command, self._coding_ctx, self._event_bus)

    def apply_code(self, command) -> Result:
        """Apply a code to a segment."""
        return apply_code(command, self._coding_ctx, self._event_bus)

    def remove_segment(self, command) -> Result:
        """Remove a segment."""
        return remove_segment(command, self._coding_ctx, self._event_bus)

    def remove_code(self, command) -> Result:
        """Remove coding from a segment (alias for remove_segment)."""
        return remove_segment(command, self._coding_ctx, self._event_bus)

    def create_category(self, command) -> Result:
        """Create a category."""
        return create_category(command, self._coding_ctx, self._event_bus)

    def delete_category(self, command) -> Result:
        """Delete a category."""
        return delete_category(command, self._coding_ctx, self._event_bus)

    def get_all_codes(self) -> list:
        """Get all codes."""
        return get_all_codes(self._coding_ctx)

    def get_code(self, code_id: int):
        """Get a specific code by ID."""
        from src.application.coding.usecases import get_code

        return get_code(self._coding_ctx, code_id)

    def get_all_categories(self) -> list:
        """Get all categories."""
        return get_all_categories(self._coding_ctx)

    def get_segments_for_source(self, source_id: int) -> list:
        """Get segments for a source."""
        return get_segments_for_source(self._coding_ctx, source_id)

    def get_segments_for_code(self, code_id: int) -> list:
        """Get segments for a code."""
        return get_segments_for_code(self._coding_ctx, code_id)


class CodingContext:
    """
    Container for all coding context dependencies.

    Manages the lifecycle of database connections and provides
    access to repositories, operations, and signal bridge.

    Usage:
        # For in-memory (testing/demo)
        ctx = CodingContext.create_in_memory()

        # For file-based
        ctx = CodingContext.create_for_file("project.qda")

        # Use the context
        viewmodel = ctx.create_text_coding_viewmodel()

        # Cleanup when done
        ctx.close()
    """

    def __init__(
        self,
        engine: Engine,
        connection: Connection,
        event_bus: EventBus,
        code_repo: SQLiteCodeRepository,
        category_repo: SQLiteCategoryRepository,
        segment_repo: SQLiteSegmentRepository,
        controller: CodingOperations,
        signal_bridge: CodingSignalBridge,
    ) -> None:
        self._engine = engine
        self._connection = connection
        self.event_bus = event_bus
        self.code_repo = code_repo
        self.category_repo = category_repo
        self.segment_repo = segment_repo
        self.controller = controller
        self.signal_bridge = signal_bridge

    @classmethod
    def create_in_memory(cls) -> CodingContext:
        """
        Create a coding context with in-memory SQLite.

        Useful for testing and demos.
        """
        engine = create_engine("sqlite:///:memory:", echo=False)
        create_all(engine)

        connection = engine.connect()
        event_bus = EventBus(history_size=100)

        code_repo = SQLiteCodeRepository(connection)
        category_repo = SQLiteCategoryRepository(connection)
        segment_repo = SQLiteSegmentRepository(connection)

        # Create app coding context for use cases
        app_ctx = AppCodingContext(
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
        )

        controller = CodingOperations(
            coding_ctx=app_ctx,
            event_bus=event_bus,
        )

        signal_bridge = CodingSignalBridge(event_bus)
        signal_bridge.start()

        return cls(
            engine=engine,
            connection=connection,
            event_bus=event_bus,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            controller=controller,
            signal_bridge=signal_bridge,
        )

    @classmethod
    def create_for_file(cls, db_path: str) -> CodingContext:
        """
        Create a coding context for a file-based SQLite database.

        Args:
            db_path: Path to the SQLite database file
        """
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        create_all(engine)

        connection = engine.connect()
        event_bus = EventBus(history_size=100)

        code_repo = SQLiteCodeRepository(connection)
        category_repo = SQLiteCategoryRepository(connection)
        segment_repo = SQLiteSegmentRepository(connection)

        # Create app coding context for use cases
        app_ctx = AppCodingContext(
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
        )

        controller = CodingOperations(
            coding_ctx=app_ctx,
            event_bus=event_bus,
        )

        signal_bridge = CodingSignalBridge(event_bus)
        signal_bridge.start()

        return cls(
            engine=engine,
            connection=connection,
            event_bus=event_bus,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            controller=controller,
            signal_bridge=signal_bridge,
        )

    def create_text_coding_viewmodel(self) -> TextCodingViewModel:
        """Create a TextCodingViewModel connected to this context."""
        return TextCodingViewModel(
            controller=self.controller,
            signal_bridge=self.signal_bridge,
        )

    def close(self) -> None:
        """Close the database connection and clean up."""
        self.signal_bridge.stop()
        self._connection.close()
        self._engine.dispose()

    def __enter__(self) -> CodingContext:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
