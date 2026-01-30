"""
Factory functions for creating connected UI components.

These factories wire up the full stack:
    Presentation ← ViewModel ← Controller ← Repositories ← SQLite
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Connection, create_engine
from sqlalchemy.engine import Engine

from src.application.coding import CodingControllerImpl, CodingSignalBridge
from src.application.event_bus import EventBus
from src.infrastructure.coding import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
    create_all,
)
from src.presentation.viewmodels import TextCodingViewModel

if TYPE_CHECKING:
    pass


class CodingContext:
    """
    Container for all coding context dependencies.

    Manages the lifecycle of database connections and provides
    access to repositories, controller, and signal bridge.

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
        controller: CodingControllerImpl,
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

        controller = CodingControllerImpl(
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
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

        controller = CodingControllerImpl(
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
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
