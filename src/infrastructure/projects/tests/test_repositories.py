"""
Project Repository Tests.

Tests for SQLAlchemy Core repository implementations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.domain.projects.entities import Source, SourceStatus, SourceType
from src.domain.shared.types import SourceId

pytestmark = pytest.mark.integration


class TestSQLiteSourceRepository:
    """Tests for SQLiteSourceRepository."""

    def test_save_and_get_by_id(self, source_repo):
        """Test saving and retrieving a source."""
        src = Source(
            id=SourceId(value=1),
            name="interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            file_path=Path("/data/interview.txt"),
            file_size=1024,
            memo="First interview",
            origin="Field Study",
        )

        source_repo.save(src)

        retrieved = source_repo.get_by_id(SourceId(value=1))
        assert retrieved is not None
        assert retrieved.name == "interview.txt"
        assert retrieved.source_type == SourceType.TEXT
        assert retrieved.memo == "First interview"

    def test_get_by_id_not_found(self, source_repo):
        """Test getting a non-existent source returns None."""
        result = source_repo.get_by_id(SourceId(value=999))
        assert result is None

    def test_get_all(self, source_repo):
        """Test getting all sources."""
        # Save multiple sources
        for i in range(3):
            src = Source(
                id=SourceId(value=i + 1),
                name=f"file_{i}.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
            source_repo.save(src)

        all_sources = source_repo.get_all()
        assert len(all_sources) == 3

    def test_get_by_type(self, source_repo):
        """Test filtering sources by type."""
        # Save sources of different types
        source_repo.save(
            Source(
                id=SourceId(value=1),
                name="interview.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
        )
        source_repo.save(
            Source(
                id=SourceId(value=2),
                name="recording.mp3",
                source_type=SourceType.AUDIO,
                status=SourceStatus.IMPORTED,
            )
        )
        source_repo.save(
            Source(
                id=SourceId(value=3),
                name="notes.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
        )

        text_sources = source_repo.get_by_type(SourceType.TEXT)
        assert len(text_sources) == 2

        audio_sources = source_repo.get_by_type(SourceType.AUDIO)
        assert len(audio_sources) == 1

    def test_get_by_status(self, source_repo):
        """Test filtering sources by status."""
        source_repo.save(
            Source(
                id=SourceId(value=1),
                name="coded.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.CODED,
            )
        )
        source_repo.save(
            Source(
                id=SourceId(value=2),
                name="new.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
        )

        coded = source_repo.get_by_status(SourceStatus.CODED)
        assert len(coded) == 1
        assert coded[0].name == "coded.txt"

    def test_update_source(self, source_repo):
        """Test updating an existing source."""
        src = Source(
            id=SourceId(value=1),
            name="original.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
        )
        source_repo.save(src)

        # Update with new data
        updated = Source(
            id=SourceId(value=1),
            name="original.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.CODED,
            memo="Now coded",
        )
        source_repo.save(updated)

        retrieved = source_repo.get_by_id(SourceId(value=1))
        assert retrieved.status == SourceStatus.CODED
        assert retrieved.memo == "Now coded"

    def test_delete_source(self, source_repo):
        """Test deleting a source."""
        src = Source(
            id=SourceId(value=1),
            name="to_delete.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
        )
        source_repo.save(src)

        source_repo.delete(SourceId(value=1))

        assert source_repo.get_by_id(SourceId(value=1)) is None

    def test_exists(self, source_repo):
        """Test checking source existence."""
        assert source_repo.exists(SourceId(value=1)) is False

        src = Source(
            id=SourceId(value=1),
            name="exists.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
        )
        source_repo.save(src)

        assert source_repo.exists(SourceId(value=1)) is True

    def test_name_exists(self, source_repo):
        """Test checking name uniqueness."""
        src = Source(
            id=SourceId(value=1),
            name="Interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
        )
        source_repo.save(src)

        # Case-insensitive check
        assert source_repo.name_exists("interview.txt") is True
        assert source_repo.name_exists("INTERVIEW.TXT") is True
        assert source_repo.name_exists("other.txt") is False

    def test_name_exists_with_exclude(self, source_repo):
        """Test name uniqueness with ID exclusion."""
        src = Source(
            id=SourceId(value=1),
            name="Interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
        )
        source_repo.save(src)

        # Excluding the source's own ID should return False
        assert (
            source_repo.name_exists("Interview.txt", exclude_id=SourceId(value=1))
            is False
        )
        assert (
            source_repo.name_exists("Interview.txt", exclude_id=SourceId(value=2))
            is True
        )

    def test_count(self, source_repo):
        """Test counting sources."""
        assert source_repo.count() == 0

        for i in range(5):
            src = Source(
                id=SourceId(value=i + 1),
                name=f"file_{i}.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
            source_repo.save(src)

        assert source_repo.count() == 5

    def test_count_by_type(self, source_repo):
        """Test counting sources by type."""
        source_repo.save(
            Source(
                id=SourceId(value=1),
                name="a.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
        )
        source_repo.save(
            Source(
                id=SourceId(value=2),
                name="b.mp3",
                source_type=SourceType.AUDIO,
                status=SourceStatus.IMPORTED,
            )
        )
        source_repo.save(
            Source(
                id=SourceId(value=3),
                name="c.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
        )

        assert source_repo.count_by_type(SourceType.TEXT) == 2
        assert source_repo.count_by_type(SourceType.AUDIO) == 1
        assert source_repo.count_by_type(SourceType.VIDEO) == 0

    def test_update_status(self, source_repo):
        """Test updating source status."""
        src = Source(
            id=SourceId(value=1),
            name="processing.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTING,
        )
        source_repo.save(src)

        source_repo.update_status(SourceId(value=1), SourceStatus.IMPORTED)

        retrieved = source_repo.get_by_id(SourceId(value=1))
        assert retrieved.status == SourceStatus.IMPORTED


class TestSQLiteProjectSettingsRepository:
    """Tests for SQLiteProjectSettingsRepository."""

    def test_set_and_get(self, settings_repo):
        """Test setting and getting a value."""
        settings_repo.set("test_key", "test_value")

        result = settings_repo.get("test_key")
        assert result == "test_value"

    def test_get_nonexistent(self, settings_repo):
        """Test getting a non-existent key returns None."""
        result = settings_repo.get("nonexistent")
        assert result is None

    def test_update_value(self, settings_repo):
        """Test updating an existing value."""
        settings_repo.set("key", "value1")
        settings_repo.set("key", "value2")

        result = settings_repo.get("key")
        assert result == "value2"

    def test_delete(self, settings_repo):
        """Test deleting a setting."""
        settings_repo.set("to_delete", "value")
        settings_repo.delete("to_delete")

        assert settings_repo.get("to_delete") is None

    def test_get_all(self, settings_repo):
        """Test getting all settings."""
        settings_repo.set("key1", "value1")
        settings_repo.set("key2", "value2")

        all_settings = settings_repo.get_all()
        assert all_settings == {"key1": "value1", "key2": "value2"}

    def test_project_name_convenience(self, settings_repo):
        """Test project name convenience methods."""
        settings_repo.set_project_name("My Project")

        assert settings_repo.get_project_name() == "My Project"

    def test_project_memo_convenience(self, settings_repo):
        """Test project memo convenience methods."""
        settings_repo.set_project_memo("Project description")

        assert settings_repo.get_project_memo() == "Project description"
