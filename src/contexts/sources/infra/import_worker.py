"""
Background worker for batch file imports.

Moves the expensive text/PDF extraction off the Qt main thread so the UI
stays responsive.  Only extraction runs in the worker; persistence and
event publishing are signalled back to the main thread (SQLite connections
cannot be shared across threads).

Usage::

    worker = ImportWorker(file_paths, state)
    worker.file_extracted.connect(on_extracted)   # main-thread slot
    worker.file_failed.connect(on_failed)         # main-thread slot
    worker.all_done.connect(on_done)              # main-thread slot
    worker.start()
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
from src.contexts.projects.core.invariants import detect_source_type
from src.contexts.sources.core.commandHandlers.import_file_source import extract_text
from src.shared.common.types import SourceId

logger = logging.getLogger("qualcoder.sources.import_worker")


@dataclass
class ExtractionResult:
    """Data extracted on the worker thread, ready for main-thread persistence."""

    index: int
    file_path: str
    source: Source
    elapsed_ms: float


@dataclass
class ExtractionFailure:
    """Describes a single file that failed extraction."""

    index: int
    file_path: str
    error: str
    elapsed_ms: float


class ImportWorker(QThread):
    """Background thread that validates and extracts text from files.

    Emits per-file signals so the main thread can persist and publish events.
    Checks ``isInterruptionRequested()`` between files to support cancellation.
    """

    # Emitted per-file on success (carries ExtractionResult)
    file_extracted = Signal(object)
    # Emitted per-file on failure (carries ExtractionFailure)
    file_failed = Signal(object)
    # Emitted once when all files have been processed
    # Carries (imported_count: int, failed_count: int, total_elapsed_ms: float)
    all_done = Signal(int, int, float)

    def __init__(
        self,
        file_paths: list[str],
        existing_names: frozenset[str],
        origin: str | None = None,
        memo: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._file_paths = file_paths
        self._existing_names = existing_names
        self._origin = origin
        self._memo = memo

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: C901 – linear, just long
        """Process each file: validate → detect type → extract text.

        Heavy I/O (PDF parsing, docx extraction) happens here, off the
        main thread.  Results are emitted via signals.
        """
        total = len(self._file_paths)
        imported = 0
        failed = 0
        batch_start = time.perf_counter()

        # Track names we've seen in *this* batch to catch duplicates within
        # the same import operation.
        seen_names: set[str] = set()

        logger.info(
            "import_worker: starting batch import of %d file(s)", total
        )

        for idx, raw_path in enumerate(self._file_paths):
            if self.isInterruptionRequested():
                logger.info(
                    "import_worker: cancellation requested after %d/%d files",
                    idx,
                    total,
                )
                break

            file_start = time.perf_counter()
            file_path = Path(raw_path)
            logger.debug(
                "import_worker: [%d/%d] processing %s", idx + 1, total, file_path.name
            )

            try:
                # --- Validate ------------------------------------------------
                source_type = detect_source_type(file_path)
                if source_type == SourceType.UNKNOWN:
                    raise ValueError(f"Unsupported file type: {file_path.suffix}")

                name = file_path.name
                # Uniqueness: check both existing DB names and this-batch names
                if name.lower() in self._existing_names or name.lower() in seen_names:
                    raise ValueError(f"Duplicate source name: {name}")

                file_size = file_path.stat().st_size

                # --- Extract text (THE SLOW PART) ----------------------------
                logger.debug(
                    "import_worker: [%d/%d] extracting text (type=%s, size=%d)",
                    idx + 1,
                    total,
                    source_type.value,
                    file_size,
                )
                extract_start = time.perf_counter()
                fulltext = extract_text(source_type, file_path)
                extract_ms = (time.perf_counter() - extract_start) * 1000
                logger.debug(
                    "import_worker: [%d/%d] extraction took %.1fms",
                    idx + 1,
                    total,
                    extract_ms,
                )

                # --- Build Source entity (no DB write yet) --------------------
                source = Source(
                    id=SourceId.new(),
                    name=name,
                    source_type=source_type,
                    status=SourceStatus.IMPORTED,
                    file_path=file_path,
                    file_size=file_size,
                    origin=self._origin,
                    memo=self._memo,
                    fulltext=fulltext,
                )

                elapsed_ms = (time.perf_counter() - file_start) * 1000
                seen_names.add(name.lower())
                imported += 1

                logger.info(
                    "import_worker: [%d/%d] extracted %s (%.1fms, extract=%.1fms)",
                    idx + 1,
                    total,
                    name,
                    elapsed_ms,
                    extract_ms,
                )
                self.file_extracted.emit(
                    ExtractionResult(
                        index=idx,
                        file_path=raw_path,
                        source=source,
                        elapsed_ms=elapsed_ms,
                    )
                )

            except Exception as exc:
                elapsed_ms = (time.perf_counter() - file_start) * 1000
                failed += 1
                logger.warning(
                    "import_worker: [%d/%d] failed %s: %s (%.1fms)",
                    idx + 1,
                    total,
                    file_path.name,
                    exc,
                    elapsed_ms,
                )
                self.file_failed.emit(
                    ExtractionFailure(
                        index=idx,
                        file_path=raw_path,
                        error=str(exc),
                        elapsed_ms=elapsed_ms,
                    )
                )

        batch_elapsed = (time.perf_counter() - batch_start) * 1000
        logger.info(
            "import_worker: batch complete — %d imported, %d failed, %.1fms total",
            imported,
            failed,
            batch_elapsed,
        )
        self.all_done.emit(imported, failed, batch_elapsed)
