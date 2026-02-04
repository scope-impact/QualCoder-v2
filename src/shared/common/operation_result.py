"""
Shared Domain: OperationResult

Rich result type for use cases that serves both UI and AI consumers.
Provides machine-readable error codes, recovery suggestions, and undo support.

Usage:
    # Success
    return OperationResult.ok(data=created_code, rollback=DeleteCodeCommand(...))

    # Failure
    return OperationResult.fail(
        error="Code name already exists",
        error_code="CODE_NOT_CREATED/DUPLICATE_NAME",
        suggestions=("Use a different name", "Rename the existing code"),
    )

    # From failure event
    return OperationResult.from_failure(failure_event)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from src.shared.common.failure_events import FailureEvent

T = TypeVar("T")


@dataclass(frozen=True)
class OperationResult:
    """
    Rich result type for use case operations.

    Serves both human UI and AI agent consumers by providing:
    - Machine-readable error codes for programmatic handling
    - Human-readable error messages for display
    - Recovery suggestions for guided error resolution
    - Rollback commands for undo functionality

    Attributes:
        success: Whether the operation succeeded
        data: The result data on success (entity, DTO, etc.)
        error: Human-readable error message on failure
        error_code: Machine-readable error code (format: ENTITY_NOT_OP/REASON)
        suggestions: Recovery hints for the user/agent
        rollback_command: Command to undo the operation (for undo stack)
    """

    success: bool
    data: Any | None = None
    error: str | None = None
    error_code: str | None = None
    suggestions: tuple[str, ...] = field(default_factory=tuple)
    rollback_command: Any | None = None

    # =========================================================================
    # Factory Methods
    # =========================================================================

    @classmethod
    def ok(
        cls,
        data: Any = None,
        rollback: Any | None = None,
    ) -> OperationResult:
        """
        Create a successful result.

        Args:
            data: The operation result (created entity, updated entity, etc.)
            rollback: Command to undo this operation (for undo stack)

        Example:
            return OperationResult.ok(
                data=created_code,
                rollback=DeleteCodeCommand(code_id=created_code.id),
            )
        """
        return cls(
            success=True,
            data=data,
            rollback_command=rollback,
        )

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: str | None = None,
        suggestions: tuple[str, ...] | list[str] = (),
    ) -> OperationResult:
        """
        Create a failed result.

        Args:
            error: Human-readable error message
            error_code: Machine-readable code (format: ENTITY_NOT_OP/REASON)
            suggestions: Recovery hints for user/agent

        Example:
            return OperationResult.fail(
                error="Code name 'Theme' already exists",
                error_code="CODE_NOT_CREATED/DUPLICATE_NAME",
                suggestions=("Use a different name", "Rename the existing code"),
            )
        """
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            suggestions=tuple(suggestions)
            if isinstance(suggestions, list)
            else suggestions,
        )

    @classmethod
    def from_failure(cls, event: FailureEvent) -> OperationResult:
        """
        Create a failed result from a domain failure event.

        Extracts error_code from event_type and message from event.

        Args:
            event: A domain failure event

        Example:
            event = CodeCreationFailed.duplicate_name("Theme")
            return OperationResult.from_failure(event)
        """
        # Extract suggestions if the event has them
        suggestions: tuple[str, ...] = ()
        if hasattr(event, "suggestions"):
            suggestions = event.suggestions

        return cls(
            success=False,
            error=event.message,
            error_code=event.event_type,
            suggestions=suggestions,
        )

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def is_success(self) -> bool:
        """Alias for success."""
        return self.success

    @property
    def is_failure(self) -> bool:
        """Inverse of success."""
        return not self.success

    # =========================================================================
    # Unwrap Methods
    # =========================================================================

    def unwrap(self) -> Any:
        """
        Get the data, raising if failed.

        Returns:
            The data on success

        Raises:
            ValueError: If the operation failed
        """
        if not self.success:
            raise ValueError(f"Cannot unwrap failed result: {self.error}")
        return self.data

    def unwrap_or(self, default: T) -> T | Any:
        """
        Get the data or a default value.

        Args:
            default: Value to return if operation failed

        Returns:
            The data on success, default on failure
        """
        return self.data if self.success else default

    def unwrap_error(self) -> str:
        """
        Get the error message, raising if succeeded.

        Returns:
            The error message on failure

        Raises:
            ValueError: If the operation succeeded
        """
        if self.success:
            raise ValueError("Cannot unwrap_error on successful result")
        return self.error or ""

    # =========================================================================
    # Transformation Methods
    # =========================================================================

    def map(self, fn: callable) -> OperationResult:
        """
        Transform the data if successful.

        Args:
            fn: Function to apply to data

        Returns:
            New OperationResult with transformed data, or self if failed
        """
        if not self.success:
            return self
        return OperationResult(
            success=True,
            data=fn(self.data),
            rollback_command=self.rollback_command,
        )

    def with_rollback(self, command: Any) -> OperationResult:
        """
        Add or replace the rollback command.

        Args:
            command: The rollback command

        Returns:
            New OperationResult with the rollback command
        """
        return OperationResult(
            success=self.success,
            data=self.data,
            error=self.error,
            error_code=self.error_code,
            suggestions=self.suggestions,
            rollback_command=command,
        )

    # =========================================================================
    # Serialization (for MCP Tools)
    # =========================================================================

    def to_dict(self) -> dict:
        """
        Convert to dictionary for MCP tool responses.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        result = {"success": self.success}

        if self.success:
            if self.data is not None:
                # Try to serialize data
                if hasattr(self.data, "to_dict"):
                    result["data"] = self.data.to_dict()
                elif hasattr(self.data, "__dict__"):
                    result["data"] = self.data.__dict__
                else:
                    result["data"] = self.data
        else:
            result["error"] = self.error
            if self.error_code:
                result["error_code"] = self.error_code
            if self.suggestions:
                result["suggestions"] = list(self.suggestions)

        return result
