"""
Convex Client Wrapper.

A Python wrapper around the Convex client that provides a consistent
interface for calling Convex functions (queries and mutations).
"""

from __future__ import annotations

import os
from typing import Any

from convex import ConvexClient


class ConvexClientWrapper:
    """
    Wrapper around the Convex Python client.

    Provides convenient methods for calling Convex queries and mutations
    with proper error handling and connection management.
    """

    def __init__(self, url: str | None = None) -> None:
        """
        Initialize the Convex client.

        Args:
            url: Convex deployment URL. If not provided, uses CONVEX_URL env var.

        Raises:
            ValueError: If no URL is provided and CONVEX_URL is not set.
        """
        self._url = url or os.environ.get("CONVEX_URL")
        if not self._url:
            raise ValueError(
                "Convex URL must be provided either as argument or via CONVEX_URL env var"
            )
        self._client: ConvexClient | None = None

    @property
    def client(self) -> ConvexClient:
        """Get or create the Convex client (lazy initialization)."""
        if self._client is None:
            self._client = ConvexClient(self._url)
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if client is initialized."""
        return self._client is not None

    def close(self) -> None:
        """Close the Convex client connection."""
        self._client = None

    # =========================================================================
    # Query Methods
    # =========================================================================

    def query(self, function_name: str, **kwargs: Any) -> Any:
        """
        Execute a Convex query function.

        Args:
            function_name: Full function path (e.g., "codes:getAll")
            **kwargs: Arguments to pass to the function

        Returns:
            Query result from Convex
        """
        return self.client.query(function_name, kwargs)

    # =========================================================================
    # Mutation Methods
    # =========================================================================

    def mutation(self, function_name: str, **kwargs: Any) -> Any:
        """
        Execute a Convex mutation function.

        Args:
            function_name: Full function path (e.g., "codes:create")
            **kwargs: Arguments to pass to the function

        Returns:
            Mutation result from Convex
        """
        return self.client.mutation(function_name, kwargs)

    # =========================================================================
    # Coding Context Shortcuts
    # =========================================================================

    def get_all_codes(self) -> list[dict[str, Any]]:
        """Get all codes."""
        return self.query("codes:getAll")

    def get_code_by_id(self, code_id: str) -> dict[str, Any] | None:
        """Get a code by ID."""
        return self.query("codes:getById", id=code_id)

    def create_code(self, **kwargs: Any) -> str:
        """Create a new code and return its ID."""
        return self.mutation("codes:create", **kwargs)

    def update_code(self, code_id: str, **kwargs: Any) -> None:
        """Update a code."""
        self.mutation("codes:update", id=code_id, **kwargs)

    def delete_code(self, code_id: str) -> None:
        """Delete a code."""
        self.mutation("codes:remove", id=code_id)

    def get_all_categories(self) -> list[dict[str, Any]]:
        """Get all categories."""
        return self.query("categories:getAll")

    def get_category_by_id(self, category_id: str) -> dict[str, Any] | None:
        """Get a category by ID."""
        return self.query("categories:getById", id=category_id)

    def create_category(self, **kwargs: Any) -> str:
        """Create a new category and return its ID."""
        return self.mutation("categories:create", **kwargs)

    def update_category(self, category_id: str, **kwargs: Any) -> None:
        """Update a category."""
        self.mutation("categories:update", id=category_id, **kwargs)

    def delete_category(self, category_id: str) -> None:
        """Delete a category."""
        self.mutation("categories:remove", id=category_id)

    def get_all_segments(self) -> list[dict[str, Any]]:
        """Get all segments."""
        return self.query("segments:getAll")

    def get_segments_by_source(self, source_id: str) -> list[dict[str, Any]]:
        """Get segments for a source."""
        return self.query("segments:getBySource", sourceId=source_id)

    def get_segments_by_code(self, code_id: str) -> list[dict[str, Any]]:
        """Get segments for a code."""
        return self.query("segments:getByCode", codeId=code_id)

    def create_segment(self, **kwargs: Any) -> str:
        """Create a new segment and return its ID."""
        return self.mutation("segments:create", **kwargs)

    def update_segment(self, segment_id: str, **kwargs: Any) -> None:
        """Update a segment."""
        self.mutation("segments:update", id=segment_id, **kwargs)

    def delete_segment(self, segment_id: str) -> None:
        """Delete a segment."""
        self.mutation("segments:remove", id=segment_id)

    # =========================================================================
    # Sources Context Shortcuts
    # =========================================================================

    def get_all_sources(self) -> list[dict[str, Any]]:
        """Get all sources."""
        return self.query("sources:getAll")

    def get_source_by_id(self, source_id: str) -> dict[str, Any] | None:
        """Get a source by ID."""
        return self.query("sources:getById", id=source_id)

    def create_source(self, **kwargs: Any) -> str:
        """Create a new source and return its ID."""
        return self.mutation("sources:create", **kwargs)

    def update_source(self, source_id: str, **kwargs: Any) -> None:
        """Update a source."""
        self.mutation("sources:update", id=source_id, **kwargs)

    def delete_source(self, source_id: str) -> None:
        """Delete a source."""
        self.mutation("sources:remove", id=source_id)

    def get_all_folders(self) -> list[dict[str, Any]]:
        """Get all folders."""
        return self.query("folders:getAll")

    def get_folder_by_id(self, folder_id: str) -> dict[str, Any] | None:
        """Get a folder by ID."""
        return self.query("folders:getById", id=folder_id)

    def create_folder(self, **kwargs: Any) -> str:
        """Create a new folder and return its ID."""
        return self.mutation("folders:create", **kwargs)

    def update_folder(self, folder_id: str, **kwargs: Any) -> None:
        """Update a folder."""
        self.mutation("folders:update", id=folder_id, **kwargs)

    def delete_folder(self, folder_id: str) -> None:
        """Delete a folder."""
        self.mutation("folders:remove", id=folder_id)

    # =========================================================================
    # Cases Context Shortcuts
    # =========================================================================

    def get_all_cases(self) -> list[dict[str, Any]]:
        """Get all cases."""
        return self.query("cases:getAll")

    def get_case_by_id(self, case_id: str) -> dict[str, Any] | None:
        """Get a case by ID."""
        return self.query("cases:getById", id=case_id)

    def create_case(self, **kwargs: Any) -> str:
        """Create a new case and return its ID."""
        return self.mutation("cases:create", **kwargs)

    def update_case(self, case_id: str, **kwargs: Any) -> None:
        """Update a case."""
        self.mutation("cases:update", id=case_id, **kwargs)

    def delete_case(self, case_id: str) -> None:
        """Delete a case."""
        self.mutation("cases:remove", id=case_id)

    # =========================================================================
    # Project Settings Shortcuts
    # =========================================================================

    def get_setting(self, key: str) -> str | None:
        """Get a project setting."""
        return self.query("settings:get", key=key)

    def set_setting(self, key: str, value: str | None) -> None:
        """Set a project setting."""
        self.mutation("settings:set", key=key, value=value)

    def get_all_settings(self) -> dict[str, str | None]:
        """Get all project settings."""
        return self.query("settings:getAll")
