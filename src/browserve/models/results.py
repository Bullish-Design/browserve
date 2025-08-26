"""
Action result models for standardized execution outcomes.

Provides ActionResult and related models for tracking action execution
success, failure, timing, and metadata across the Browserve framework.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
import time


class ActionStatus(str, Enum):
    """Enumeration of possible action execution statuses."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RETRY = "retry"
    SKIPPED = "skipped"


class ActionResult(BaseModel):
    """
    Standardized result of action execution.

    Provides comprehensive tracking of action outcomes including success/failure,
    timing information, retry counts, and contextual metadata. Used across all
    PlaywrightAction implementations for consistent result handling.

    Example:
        >>> result = ActionResult.success_result(
        ...     data={"element_found": True},
        ...     selector="#button"
        ... )
        >>> assert result.success
        >>> assert result.status == ActionStatus.SUCCESS
    """

    success: bool = Field(description="Whether action completed successfully")
    status: ActionStatus = Field(description="Detailed execution status")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data from successful execution")
    error: Optional[str] = Field(None, description="Error message if action failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional execution context and metrics")
    execution_time: Optional[float] = Field(None, ge=0.0, description="Total execution time in seconds")
    retry_count: int = Field(0, ge=0, description="Number of retries performed during execution")
    action_type: Optional[str] = Field(None, description="Type of action that was executed")

    @classmethod
    def success_result(
        cls, data: Optional[Dict[str, Any]] = None, action_type: Optional[str] = None, **metadata: Any
    ) -> ActionResult:
        """
        Create a successful action result.

        Args:
            data: Optional result data from execution
            action_type: Type of action that succeeded
            **metadata: Additional context to include

        Returns:
            ActionResult indicating successful execution

        Example:
            >>> result = ActionResult.success_result(
            ...     data={"clicked": True},
            ...     action_type="click",
            ...     selector="#submit-btn"
            ... )
        """
        return cls(
            success=True, status=ActionStatus.SUCCESS, data=data or {}, action_type=action_type, metadata=metadata
        )

    @classmethod
    def failure_result(cls, error: str, action_type: Optional[str] = None, **metadata: Any) -> ActionResult:
        """
        Create a failed action result.

        Args:
            error: Description of what went wrong
            action_type: Type of action that failed
            **metadata: Additional failure context

        Returns:
            ActionResult indicating failed execution

        Example:
            >>> result = ActionResult.failure_result(
            ...     error="Element not found",
            ...     action_type="click",
            ...     selector="#missing"
            ... )
        """
        return cls(success=False, status=ActionStatus.FAILURE, error=error, action_type=action_type, metadata=metadata)

    @classmethod
    def timeout_result(cls, timeout_duration: float, action_type: Optional[str] = None) -> ActionResult:
        """
        Create a timeout action result.

        Args:
            timeout_duration: How long the action waited before timing out
            action_type: Type of action that timed out

        Returns:
            ActionResult indicating timeout failure

        Example:
            >>> result = ActionResult.timeout_result(30.0, "wait")
        """
        return cls(
            success=False,
            status=ActionStatus.TIMEOUT,
            error=f"Action timed out after {timeout_duration}s",
            action_type=action_type,
            metadata={"timeout_duration": timeout_duration},
        )

    @classmethod
    def retry_result(
        cls, attempt: int, max_attempts: int, last_error: str, action_type: Optional[str] = None
    ) -> ActionResult:
        """
        Create a retry-in-progress result.

        Args:
            attempt: Current attempt number
            max_attempts: Total attempts allowed
            last_error: Error from the failed attempt
            action_type: Type of action being retried

        Returns:
            ActionResult indicating retry status
        """
        return cls(
            success=False,
            status=ActionStatus.RETRY,
            error=f"Attempt {attempt}/{max_attempts} failed: {last_error}",
            action_type=action_type,
            retry_count=attempt - 1,
            metadata={"current_attempt": attempt, "max_attempts": max_attempts, "last_error": last_error},
        )

    def add_timing(self, start_time: float) -> ActionResult:
        """
        Add execution timing to result.

        Args:
            start_time: When execution began (from time.time())

        Returns:
            Self for method chaining
        """
        self.execution_time = time.time() - start_time
        return self

    def add_metadata(self, **metadata: Any) -> ActionResult:
        """
        Add additional metadata to result.

        Args:
            **metadata: Key-value pairs to add

        Returns:
            Self for method chaining
        """
        self.metadata.update(metadata)
        return self

    def is_retriable(self) -> bool:
        """
        Check if this result indicates a retriable failure.

        Returns:
            True if the action could be retried
        """
        return self.status in (ActionStatus.TIMEOUT, ActionStatus.FAILURE)

    def summary(self) -> str:
        """
        Get a human-readable summary of the result.

        Returns:
            Brief description of the action outcome
        """
        if self.success:
            time_info = f" ({self.execution_time:.2f}s)" if self.execution_time else ""
            return f"✓ {self.action_type or 'Action'} succeeded{time_info}"
        else:
            retry_info = f" (retry {self.retry_count})" if self.retry_count > 0 else ""
            return f"✗ {self.action_type or 'Action'} failed{retry_info}: {self.error}"


class ActionMetrics(BaseModel):
    """
    Aggregate metrics for action execution tracking.

    Tracks performance and reliability metrics across action executions
    for monitoring and optimization purposes.
    """

    total_actions: int = Field(0, description="Total actions executed")
    successful_actions: int = Field(0, description="Actions that succeeded")
    failed_actions: int = Field(0, description="Actions that failed")
    timeout_actions: int = Field(0, description="Actions that timed out")
    total_execution_time: float = Field(0.0, description="Total time spent in seconds")
    total_retries: int = Field(0, description="Total retry attempts made")

    def record_result(self, result: ActionResult) -> None:
        """
        Record an action result in metrics.

        Args:
            result: ActionResult to add to metrics
        """
        self.total_actions += 1

        if result.success:
            self.successful_actions += 1
        elif result.status == ActionStatus.TIMEOUT:
            self.timeout_actions += 1
        else:
            self.failed_actions += 1

        if result.execution_time:
            self.total_execution_time += result.execution_time

        self.total_retries += result.retry_count

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_actions == 0:
            return 0.0
        return (self.successful_actions / self.total_actions) * 100

    @property
    def average_execution_time(self) -> float:
        """Calculate average execution time."""
        if self.successful_actions == 0:
            return 0.0
        return self.total_execution_time / self.successful_actions

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.timeout_actions = 0
        self.total_execution_time = 0.0
        self.total_retries = 0
