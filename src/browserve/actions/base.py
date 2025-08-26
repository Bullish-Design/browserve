"""
Base action framework for browser automation with Pydantic validation.

Provides PlaywrightAction abstract base class and ComposedAction for building
validated, composable browser automation tasks with pre/post execution hooks.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
import time
import asyncio
import logging

from ..models.results import ActionResult, ActionStatus
from ..exceptions import ActionExecutionError, ValidationError, ElementError, ErrorCodes

if TYPE_CHECKING:
    from ..core.page import PageBase

# Configure logger for action execution
logger = logging.getLogger(__name__)


class PlaywrightAction(BaseModel, ABC):
    """
    Abstract base class for browser actions with Pydantic validation.

    Provides a framework for creating validated, executable browser actions
    with pre/post execution hooks, retry logic, and standardized results.
    All concrete actions must inherit from this class.

    Example:
        >>> class CustomAction(PlaywrightAction):
        ...     action_type: str = "custom"
        ...
        ...     async def execute(self, page: PageBase) -> ActionResult:
        ...         # Implementation here
        ...         return ActionResult.success_result()
    """

    action_type: str = Field(description="Unique identifier for this action type")
    timeout: float = Field(30.0, ge=0.1, le=300.0, description="Maximum execution time in seconds")
    retry_count: int = Field(0, ge=0, le=10, description="Number of retries on failure")
    wait_before: float = Field(0.0, ge=0.0, le=60.0, description="Delay before execution in seconds")
    wait_after: float = Field(0.0, ge=0.0, le=60.0, description="Delay after execution in seconds")
    validate_before: bool = Field(True, description="Run pre-execution validation")
    description: Optional[str] = Field(None, description="Human-readable description of this action")

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Ensure action_type is not empty."""
        if not v or not v.strip():
            raise ValueError("action_type cannot be empty")
        return v.strip()

    @abstractmethod
    async def execute(self, page: PageBase) -> ActionResult:
        """
        Execute the action on the target page.

        This method must be implemented by all concrete action classes.
        It should perform the actual browser interaction and return
        a standardized ActionResult.

        Args:
            page: PageBase instance to execute action against

        Returns:
            ActionResult with execution outcome

        Raises:
            Should NOT raise exceptions - return failure ActionResult instead
        """
        pass

    async def pre_execute(self, page: PageBase) -> None:
        """
        Pre-execution hooks for validation and setup.

        Called before main execution. Can be overridden by subclasses
        for custom validation or setup logic. Should raise exceptions
        for validation failures that prevent execution.

        Args:
            page: PageBase instance that will be acted upon

        Raises:
            ActionExecutionError: If page is not ready for action
            ValidationError: If action parameters are invalid for current context
        """
        # Check page is active and ready
        if not page.is_active:
            raise ActionExecutionError(
                "Page is not active - cannot execute action",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type=self.action_type,
            )

        # Wait before execution if specified
        if self.wait_before > 0:
            logger.debug(f"Waiting {self.wait_before}s before {self.action_type}")
            await asyncio.sleep(self.wait_before)

    async def post_execute(self, page: PageBase, result: ActionResult) -> None:
        """
        Post-execution hooks for cleanup and logging.

        Called after main execution with the result. Can be overridden
        by subclasses for custom cleanup, logging, or validation.

        Args:
            page: PageBase instance that action was executed against
            result: ActionResult from the execution
        """
        # Wait after execution if specified
        if self.wait_after > 0:
            logger.debug(f"Waiting {self.wait_after}s after {self.action_type}")
            await asyncio.sleep(self.wait_after)

        # Log execution result
        if result.success:
            logger.info(f"Action {self.action_type} succeeded in {result.execution_time or 0:.2f}s")
        else:
            logger.warning(f"Action {self.action_type} failed: {result.error}")

    async def execute_with_hooks(self, page: PageBase) -> ActionResult:
        """
        Execute action with full pre/post hook cycle and retry logic.

        This is the main entry point for action execution. It handles
        the complete lifecycle including validation, retries, timing,
        and hook execution.

        Args:
            page: PageBase instance to execute against

        Returns:
            ActionResult with complete execution information
        """
        start_time = time.time()
        last_error = None

        for attempt in range(self.retry_count + 1):
            attempt_start = time.time()

            try:
                # Pre-execution hooks and validation
                if self.validate_before:
                    await self.pre_execute(page)

                # Main execution with timeout
                logger.debug(f"Executing {self.action_type} (attempt {attempt + 1}/{self.retry_count + 1})")

                result = await asyncio.wait_for(self.execute(page), timeout=self.timeout)

                # Ensure result has required fields
                if result.action_type is None:
                    result.action_type = self.action_type

                # Add execution timing
                result.execution_time = time.time() - start_time
                result.retry_count = attempt

                # Post-execution hooks
                await self.post_execute(page, result)

                # Success - return immediately
                if result.success:
                    return result

                # Action reported failure but didn't raise exception
                last_error = result.error or "Action reported failure"

                if attempt < self.retry_count:
                    retry_delay = self._calculate_retry_delay(attempt)
                    logger.info(
                        f"Action {self.action_type} failed, retrying in "
                        f"{retry_delay:.1f}s (attempt {attempt + 1}/"
                        f"{self.retry_count + 1})"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # All attempts exhausted, return the last result
                    result.execution_time = time.time() - start_time
                    result.retry_count = attempt
                    return result

            except asyncio.TimeoutError:
                logger.warning(f"Action {self.action_type} timed out after {self.timeout}s (attempt {attempt + 1})")

                if attempt < self.retry_count:
                    await asyncio.sleep(self._calculate_retry_delay(attempt))
                    continue
                else:
                    return ActionResult.timeout_result(self.timeout, self.action_type).add_timing(start_time)

            except Exception as e:
                last_error = str(e)
                logger.error(f"Action {self.action_type} failed with exception: {e}")

                if attempt < self.retry_count:
                    retry_delay = self._calculate_retry_delay(attempt)
                    logger.info(
                        f"Retrying {self.action_type} in {retry_delay:.1f}s "
                        f"(attempt {attempt + 1}/{self.retry_count + 1})"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    break

        # All retries failed
        return (
            ActionResult.failure_result(
                error=f"Action failed after {self.retry_count + 1} attempts: {last_error}", action_type=self.action_type
            )
            .add_timing(start_time)
            .add_metadata(retry_count=self.retry_count)
        )

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay before retry using exponential backoff.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: 0.5s, 1s, 2s, 4s, 8s (capped at 8s)
        return min(0.5 * (2**attempt), 8.0)

    def compose_with(self, other: PlaywrightAction) -> ComposedAction:
        """
        Compose this action with another action into a sequence.

        Args:
            other: Action to execute after this one

        Returns:
            ComposedAction that executes both actions in sequence

        Example:
            >>> click = ClickAction(selector="#button")
            >>> fill = FillAction(selector="#input", value="text")
            >>> sequence = click.compose_with(fill)
        """
        return ComposedAction(actions=[self, other])

    def then(self, other: PlaywrightAction) -> ComposedAction:
        """Alias for compose_with for more fluent chaining."""
        return self.compose_with(other)

    def with_retry(self, count: int) -> PlaywrightAction:
        """
        Create copy of this action with specified retry count.

        Args:
            count: Number of retries to allow

        Returns:
            New action instance with updated retry count
        """
        new_action = self.model_copy()
        new_action.retry_count = count
        return new_action

    def with_timeout(self, timeout: float) -> PlaywrightAction:
        """
        Create copy of this action with specified timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            New action instance with updated timeout
        """
        new_action = self.model_copy()
        new_action.timeout = timeout
        return new_action

    def with_delays(self, wait_before: float = 0.0, wait_after: float = 0.0) -> PlaywrightAction:
        """
        Create copy of this action with specified delays.

        Args:
            wait_before: Delay before execution
            wait_after: Delay after execution

        Returns:
            New action instance with updated delays
        """
        new_action = self.model_copy()
        new_action.wait_before = wait_before
        new_action.wait_after = wait_after
        return new_action


class ComposedAction(PlaywrightAction):
    """
    Composition of multiple actions executed in sequence.

    Allows combining multiple PlaywrightActions into a single action
    that executes them in order. Supports stopping on first failure
    or continuing through failures.

    Example:
        >>> actions = [
        ...     ClickAction(selector="#tab1"),
        ...     FillAction(selector="#input", value="data"),
        ...     ClickAction(selector="#submit")
        ... ]
        >>> composed = ComposedAction(actions=actions)
        >>> result = await composed.execute_with_hooks(page)
    """

    actions: List[PlaywrightAction] = Field(description="Actions to execute in sequence")
    action_type: str = "composed"
    stop_on_failure: bool = Field(True, description="Stop execution if any action fails")
    collect_results: bool = Field(True, description="Collect and return results from all actions")

    @field_validator("actions")
    @classmethod
    def validate_actions_not_empty(cls, v: List[PlaywrightAction]) -> List[PlaywrightAction]:
        """Ensure actions list is not empty."""
        if not v:
            raise ValueError("actions list cannot be empty")
        return v

    async def execute(self, page: PageBase) -> ActionResult:
        """
        Execute all composed actions in sequence.

        Args:
            page: PageBase instance to execute actions against

        Returns:
            ActionResult with aggregated results from all actions
        """
        results = []
        failed_at_step = None

        for i, action in enumerate(self.actions):
            logger.debug(f"Executing composed action step {i + 1}/{len(self.actions)}: {action.action_type}")

            try:
                result = await action.execute_with_hooks(page)

                if self.collect_results:
                    results.append(
                        {
                            "step": i + 1,
                            "action_type": action.action_type,
                            "success": result.success,
                            "error": result.error,
                            "execution_time": result.execution_time,
                            "data": result.data,
                        }
                    )

                if not result.success:
                    failed_at_step = i + 1

                    if self.stop_on_failure:
                        logger.warning(
                            f"Composed action stopping at step {failed_at_step} due to failure: {result.error}"
                        )

                        return ActionResult.failure_result(
                            error=f"Composed action failed at step {failed_at_step} "
                            f"({action.action_type}): {result.error}",
                            action_type=self.action_type,
                        ).add_metadata(
                            completed_steps=i,
                            failed_step=failed_at_step,
                            total_steps=len(self.actions),
                            results=results if self.collect_results else None,
                        )
                    else:
                        logger.warning(f"Composed action step {failed_at_step} failed but continuing: {result.error}")

            except Exception as e:
                error_msg = f"Exception in composed action step {i + 1}: {str(e)}"
                logger.error(error_msg)

                if self.collect_results:
                    results.append(
                        {
                            "step": i + 1,
                            "action_type": action.action_type,
                            "success": False,
                            "error": str(e),
                            "execution_time": None,
                            "data": None,
                        }
                    )

                if self.stop_on_failure:
                    return ActionResult.failure_result(error=error_msg, action_type=self.action_type).add_metadata(
                        completed_steps=i,
                        failed_step=i + 1,
                        total_steps=len(self.actions),
                        results=results if self.collect_results else None,
                    )

        # All actions completed
        success = failed_at_step is None

        return ActionResult.success_result(
            action_type=self.action_type,
            data={"completed_steps": len(self.actions), "total_steps": len(self.actions), "all_succeeded": success},
        ).add_metadata(results=results if self.collect_results else None, failed_step=failed_at_step)


class ConditionalAction(PlaywrightAction):
    """
    Execute action based on a condition check.

    Allows conditional execution of actions based on page state
    or element presence/visibility.
    """

    condition_action: PlaywrightAction = Field(description="Action to check condition (should return success/failure)")
    then_action: PlaywrightAction = Field(description="Action to execute if condition succeeds")
    else_action: Optional[PlaywrightAction] = Field(None, description="Action to execute if condition fails")
    action_type: str = "conditional"

    async def execute(self, page: PageBase) -> ActionResult:
        """Execute conditional action logic."""
        # Check condition
        condition_result = await self.condition_action.execute_with_hooks(page)

        if condition_result.success:
            logger.debug("Condition succeeded, executing then_action")
            result = await self.then_action.execute_with_hooks(page)
            return result.add_metadata(condition_result=True)
        else:
            logger.debug("Condition failed, executing else_action")
            if self.else_action:
                result = await self.else_action.execute_with_hooks(page)
                return result.add_metadata(condition_result=False)
            else:
                return ActionResult.success_result(
                    action_type=self.action_type, data={"condition_result": False, "else_action": None}
                )
