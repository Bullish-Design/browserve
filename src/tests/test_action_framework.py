"""
Test suite for Browserve action framework.
"""

from __future__ import annotations
import pytest
import asyncio
import time
import logging
from unittest.mock import AsyncMock, Mock, patch
from pydantic import ValidationError as PydanticValidationError

from browserve.models.results import (
    ActionStatus,
    ActionResult,
    ActionMetrics,
)
from browserve.actions.base import (
    PlaywrightAction,
    ComposedAction,
    ConditionalAction,
)
from browserve.actions.interaction import (
    ClickAction,
    FillAction,
    NavigationAction,
    WaitAction,
    HoverAction,
    ScrollAction,
)
from browserve.exceptions import (
    ActionExecutionError,
    ElementError,
    ValidationError,
)
from browserve.core.page import PageBase

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestActionResult:
    """Test ActionResult model and factory methods."""

    def test_success_result_creation(self) -> None:
        """Test successful result creation."""
        logger.info("Testing ActionResult.success_result creation")

        result = ActionResult.success_result(data={"element_clicked": True}, action_type="click", selector="#button")

        logger.info(f"Created success result: {result}")
        assert result.success is True
        assert result.status == ActionStatus.SUCCESS
        assert result.data == {"element_clicked": True}
        assert result.action_type == "click"
        assert result.metadata == {"selector": "#button"}
        assert result.error is None

    def test_failure_result_creation(self) -> None:
        """Test failure result creation."""
        logger.info("Testing ActionResult.failure_result creation")

        result = ActionResult.failure_result(error="Element not found", action_type="click", selector="#missing")

        logger.info(f"Created failure result: {result}")
        assert result.success is False
        assert result.status == ActionStatus.FAILURE
        assert result.error == "Element not found"
        assert result.action_type == "click"
        assert result.metadata == {"selector": "#missing"}

    def test_timeout_result_creation(self) -> None:
        """Test timeout result creation."""
        logger.info("Testing ActionResult.timeout_result creation")

        result = ActionResult.timeout_result(30.0, "wait")

        logger.info(f"Created timeout result: {result}")
        assert result.success is False
        assert result.status == ActionStatus.TIMEOUT
        assert "timed out after 30.0s" in result.error
        assert result.action_type == "wait"
        assert result.metadata["timeout_duration"] == 30.0

    def test_result_chaining_methods(self) -> None:
        """Test result method chaining."""
        logger.info("Testing ActionResult method chaining")

        start_time = time.time()
        result = (
            ActionResult.success_result(action_type="test").add_timing(start_time).add_metadata(test_key="test_value")
        )

        logger.info(f"Chained result: execution_time={result.execution_time}")
        assert result.execution_time is not None
        assert result.execution_time >= 0
        assert result.metadata["test_key"] == "test_value"

    def test_result_summary(self) -> None:
        """Test result summary generation."""
        logger.info("Testing ActionResult summary generation")

        success_result = ActionResult.success_result(action_type="click")
        success_result.execution_time = 1.5

        failure_result = ActionResult.failure_result(error="Failed", action_type="fill")
        failure_result.retry_count = 2

        success_summary = success_result.summary()
        failure_summary = failure_result.summary()

        logger.info(f"Success summary: {success_summary}")
        logger.info(f"Failure summary: {failure_summary}")

        assert "✓" in success_summary and "click" in success_summary
        assert "✗" in failure_summary and "fill" in failure_summary
        assert "retry 2" in failure_summary

    def test_is_retriable(self) -> None:
        """Test retriable status checking."""
        logger.info("Testing ActionResult.is_retriable()")

        success = ActionResult.success_result()
        timeout = ActionResult.timeout_result(30.0)
        failure = ActionResult.failure_result("Error")

        logger.info(f"Success retriable: {success.is_retriable()}")
        logger.info(f"Timeout retriable: {timeout.is_retriable()}")
        logger.info(f"Failure retriable: {failure.is_retriable()}")

        assert not success.is_retriable()
        assert timeout.is_retriable()
        assert failure.is_retriable()


class TestActionMetrics:
    """Test ActionMetrics for tracking action performance."""

    def test_metrics_recording(self) -> None:
        """Test recording results in metrics."""
        logger.info("Testing ActionMetrics recording")

        metrics = ActionMetrics()

        # Record various results
        success = ActionResult.success_result()
        success.execution_time = 1.0

        failure = ActionResult.failure_result("Error")
        failure.retry_count = 2

        timeout = ActionResult.timeout_result(30.0)

        metrics.record_result(success)
        metrics.record_result(failure)
        metrics.record_result(timeout)

        logger.info(f"Metrics: {metrics}")
        assert metrics.total_actions == 3
        assert metrics.successful_actions == 1
        assert metrics.failed_actions == 1
        assert metrics.timeout_actions == 1
        assert metrics.total_retries == 2
        assert metrics.success_rate == pytest.approx(33.33, rel=0.1)


class MockAction(PlaywrightAction):
    """Mock action for testing base functionality."""

    action_type: str = "mock"
    should_fail: bool = False
    execution_delay: float = 0.0

    async def execute(self, page: PageBase) -> ActionResult:
        """Mock execution with configurable behavior."""
        if self.execution_delay > 0:
            await asyncio.sleep(self.execution_delay)

        if self.should_fail:
            return ActionResult.failure_result("Mock failure", action_type=self.action_type)

        return ActionResult.success_result(data={"mock_data": True}, action_type=self.action_type)


class TestPlaywrightActionBase:
    """Test PlaywrightAction base class functionality."""

    @pytest.fixture
    def mock_page(self) -> PageBase:
        """Create mock PageBase for testing."""
        logger.info("Creating mock PageBase for action testing")

        mock_page = Mock(spec=PageBase)
        mock_page.is_active = True
        mock_page.current_url = "https://example.com"
        mock_page.session_id = "test-session"

        return mock_page

    async def test_action_validation(self) -> None:
        """Test action parameter validation."""
        logger.info("Testing PlaywrightAction validation")

        # Valid action
        action = MockAction(action_type="test", timeout=30.0)
        assert action.action_type == "test"
        assert action.timeout == 30.0

        # Invalid action_type
        with pytest.raises(PydanticValidationError):
            MockAction(action_type="", timeout=30.0)

        # Invalid timeout
        with pytest.raises(PydanticValidationError):
            MockAction(action_type="test", timeout=-1.0)

        # Invalid retry_count
        with pytest.raises(PydanticValidationError):
            MockAction(action_type="test", retry_count=15)

    async def test_successful_execution(self, mock_page: PageBase) -> None:
        """Test successful action execution."""
        logger.info("Testing successful action execution")

        action = MockAction(action_type="test")
        result = await action.execute_with_hooks(mock_page)

        logger.info(f"Execution result: {result}")
        assert result.success is True
        assert result.action_type == "test"
        assert result.execution_time is not None
        assert result.retry_count == 0

    async def test_failed_execution(self, mock_page: PageBase) -> None:
        """Test failed action execution."""
        logger.info("Testing failed action execution")

        action = MockAction(action_type="test", should_fail=True)
        result = await action.execute_with_hooks(mock_page)

        logger.info(f"Failed execution result: {result}")
        assert result.success is False
        assert "Mock failure" in result.error
        assert result.execution_time is not None

    async def test_retry_logic(self, mock_page: PageBase) -> None:
        """Test retry logic with exponential backoff."""
        logger.info("Testing retry logic")

        action = MockAction(action_type="test", should_fail=True, retry_count=3)

        start_time = time.time()
        result = await action.execute_with_hooks(mock_page)
        end_time = time.time()

        logger.info(f"Retry result: {result}")
        logger.info(f"Total time: {end_time - start_time:.2f}s")

        assert result.success is False
        assert result.retry_count == 3
        assert "failed after 4 attempts" in result.error
        # Should have taken some time due to exponential backoff
        assert end_time - start_time > 7.0  # 0.5 + 1 + 2 + 4 = 7.5s

    async def test_timeout_handling(self, mock_page: PageBase) -> None:
        """Test action timeout handling."""
        logger.info("Testing action timeout handling")

        action = MockAction(action_type="test", execution_delay=2.0, timeout=1.0)

        result = await action.execute_with_hooks(mock_page)

        logger.info(f"Timeout result: {result}")
        assert result.success is False
        assert result.status == ActionStatus.TIMEOUT
        assert "timed out after 1.0s" in result.error

    async def test_pre_post_hooks(self, mock_page: PageBase) -> None:
        """Test pre and post execution hooks."""
        logger.info("Testing pre/post execution hooks")

        class HookedAction(MockAction):
            pre_called: bool = False
            post_called: bool = False

            async def pre_execute(self, page: PageBase) -> None:
                await super().pre_execute(page)
                self.pre_called = True
                logger.info("Pre-execute hook called")

            async def post_execute(self, page: PageBase, result: ActionResult) -> None:
                await super().post_execute(page, result)
                self.post_called = True
                logger.info("Post-execute hook called")

        action = HookedAction(action_type="hooked")
        result = await action.execute_with_hooks(mock_page)

        logger.info(f"Hooked execution result: {result}")
        assert action.pre_called is True
        assert action.post_called is True
        assert result.success is True

    async def test_inactive_page_validation(self) -> None:
        """Test validation fails with inactive page."""
        logger.info("Testing validation with inactive page")

        inactive_page = Mock(spec=PageBase)
        inactive_page.is_active = False

        action = MockAction(action_type="test")

        with pytest.raises(ActionExecutionError, match="not active"):
            await action.pre_execute(inactive_page)

    async def test_wait_delays(self, mock_page: PageBase) -> None:
        """Test wait_before and wait_after delays."""
        logger.info("Testing wait delays")

        action = MockAction(action_type="test", wait_before=0.1, wait_after=0.1)

        start_time = time.time()
        result = await action.execute_with_hooks(mock_page)
        end_time = time.time()

        logger.info(f"Delayed execution took: {end_time - start_time:.2f}s")
        assert result.success is True
        assert end_time - start_time >= 0.2  # At least 0.2s for delays

    def test_action_chaining_methods(self) -> None:
        """Test fluent action configuration methods."""
        logger.info("Testing action chaining methods")

        original = MockAction(action_type="test")

        with_retry = original.with_retry(5)
        with_timeout = original.with_timeout(60.0)
        with_delays = original.with_delays(1.0, 2.0)

        logger.info(f"Original retry_count: {original.retry_count}")
        logger.info(f"With retry count: {with_retry.retry_count}")

        assert original.retry_count == 0
        assert with_retry.retry_count == 5
        assert with_timeout.timeout == 60.0
        assert with_delays.wait_before == 1.0
        assert with_delays.wait_after == 2.0


class TestComposedAction:
    """Test ComposedAction for action sequences."""

    @pytest.fixture
    def mock_page(self) -> PageBase:
        """Create mock PageBase."""
        mock_page = Mock(spec=PageBase)
        mock_page.is_active = True
        return mock_page

    async def test_successful_composition(self, mock_page: PageBase) -> None:
        """Test successful execution of composed actions."""
        logger.info("Testing successful action composition")

        action1 = MockAction(action_type="first")
        action2 = MockAction(action_type="second")
        action3 = MockAction(action_type="third")

        composed = ComposedAction(actions=[action1, action2, action3])
        result = await composed.execute_with_hooks(mock_page)

        logger.info(f"Composed result: {result}")
        assert result.success is True
        assert result.data["completed_steps"] == 3
        assert result.data["total_steps"] == 3
        assert len(result.metadata["results"]) == 3

    async def test_composition_with_failure_stop(self, mock_page: PageBase) -> None:
        """Test composition stops on first failure."""
        logger.info("Testing composition with stop_on_failure=True")

        action1 = MockAction(action_type="first")
        action2 = MockAction(action_type="second", should_fail=True)
        action3 = MockAction(action_type="third")

        composed = ComposedAction(actions=[action1, action2, action3], stop_on_failure=True)
        result = await composed.execute_with_hooks(mock_page)

        logger.info(f"Failed composition result: {result}")
        assert result.success is False
        assert "failed at step 2" in result.error
        assert result.metadata["completed_steps"] == 1
        assert result.metadata["failed_step"] == 2

    async def test_composition_continue_on_failure(self, mock_page: PageBase) -> None:
        """Test composition continues through failures."""
        logger.info("Testing composition with stop_on_failure=False")

        action1 = MockAction(action_type="first")
        action2 = MockAction(action_type="second", should_fail=True)
        action3 = MockAction(action_type="third")

        composed = ComposedAction(actions=[action1, action2, action3], stop_on_failure=False)
        result = await composed.execute_with_hooks(mock_page)

        logger.info(f"Continue composition result: {result}")
        assert result.success is True  # Overall success despite one failure
        assert result.data["completed_steps"] == 3
        assert result.metadata["failed_step"] == 2

    def test_compose_with_method(self) -> None:
        """Test action.compose_with() method."""
        logger.info("Testing action.compose_with() method")

        action1 = MockAction(action_type="first")
        action2 = MockAction(action_type="second")

        composed = action1.compose_with(action2)

        logger.info(f"Composed action: {composed}")
        assert isinstance(composed, ComposedAction)
        assert len(composed.actions) == 2
        assert composed.actions[0].action_type == "first"
        assert composed.actions[1].action_type == "second"

    def test_then_method_alias(self) -> None:
        """Test action.then() as alias for compose_with."""
        logger.info("Testing action.then() method alias")

        action1 = MockAction(action_type="first")
        action2 = MockAction(action_type="second")

        composed = action1.then(action2)

        assert isinstance(composed, ComposedAction)
        assert len(composed.actions) == 2

    def test_empty_actions_validation(self) -> None:
        """Test validation prevents empty action lists."""
        logger.info("Testing empty actions list validation")

        with pytest.raises(PydanticValidationError, match="cannot be empty"):
            ComposedAction(actions=[])


class TestConcreteActions:
    """Test concrete action implementations."""

    @pytest.fixture
    async def mock_page_with_playwright(self) -> PageBase:
        """Create PageBase with mocked Playwright functionality."""
        logger.info("Creating PageBase with mock Playwright")

        mock_playwright_page = AsyncMock()
        mock_playwright_page.click = AsyncMock()
        mock_playwright_page.fill = AsyncMock()
        mock_playwright_page.goto = AsyncMock()
        mock_playwright_page.hover = AsyncMock()
        mock_playwright_page.wait_for_selector = AsyncMock()
        mock_playwright_page.locator = AsyncMock()

        # Mock locator methods
        mock_locator = AsyncMock()
        mock_locator.is_visible = AsyncMock(return_value=True)
        mock_locator.is_enabled = AsyncMock(return_value=True)
        mock_locator.text_content = AsyncMock(return_value="Button Text")
        mock_locator.get_attribute = AsyncMock(return_value="test-value")
        mock_locator.scroll_into_view_if_needed = AsyncMock()
        mock_playwright_page.locator.return_value = mock_locator

        # Mock navigation response
        mock_response = Mock()
        mock_response.status = 200
        mock_playwright_page.goto.return_value = mock_response

        page = PageBase(session_id="test-session", url="https://example.com")
        page.set_playwright_page(mock_playwright_page)

        return page

    async def test_click_action_success(self, mock_page_with_playwright: PageBase) -> None:
        """Test successful click action execution."""
        logger.info("Testing ClickAction success")

        action = ClickAction(selector="#test-button", button="left", modifiers=["Shift"])

        result = await action.execute_with_hooks(mock_page_with_playwright)

        logger.info(f"Click result: {result}")
        assert result.success is True
        assert result.data["selector"] == "#test-button"
        assert result.data["button"] == "left"
        assert result.metadata["modifiers"] == ["Shift"]

    async def test_click_action_validation(self) -> None:
        """Test ClickAction parameter validation."""
        logger.info("Testing ClickAction validation")

        # Invalid selector
        with pytest.raises(PydanticValidationError):
            ClickAction(selector="<invalid>")

        # Invalid button
        with pytest.raises(PydanticValidationError):
            ClickAction(selector="#button", button="invalid")

        # Invalid modifier
        with pytest.raises(PydanticValidationError):
            ClickAction(selector="#button", modifiers=["InvalidKey"])

    async def test_fill_action_success(self, mock_page_with_playwright: PageBase) -> None:
        """Test successful fill action execution."""
        logger.info("Testing FillAction success")

        action = FillAction(
            selector="input[name='username']",
            value="testuser",
            clear_first=True,
            verify_fill=False,  # Skip verification for mock
        )

        result = await action.execute_with_hooks(mock_page_with_playwright)

        logger.info(f"Fill result: {result}")
        assert result.success is True
        assert result.data["value"] == "testuser"
        assert result.metadata["cleared_first"] is True

    async def test_navigation_action_success(self, mock_page_with_playwright: PageBase) -> None:
        """Test successful navigation action."""
        logger.info("Testing NavigationAction success")

        action = NavigationAction(
            url="https://example.com/login",
            wait_until="load",
            verify_navigation=False,  # Skip verification for mock
        )

        result = await action.execute_with_hooks(mock_page_with_playwright)

        logger.info(f"Navigation result: {result}")
        assert result.success is True
        assert result.data["target_url"] == "https://example.com/login"
        assert result.data["wait_until"] == "load"

    async def test_wait_action_time_based(self, mock_page_with_playwright: PageBase) -> None:
        """Test time-based wait action."""
        logger.info("Testing WaitAction with time-based wait")

        action = WaitAction(wait_time=0.1)  # Short wait for testing

        start_time = time.time()
        result = await action.execute_with_hooks(mock_page_with_playwright)
        end_time = time.time()

        logger.info(f"Wait result: {result}, duration: {end_time - start_time:.2f}s")
        assert result.success is True
        assert result.data["wait_time"] == 0.1
        assert end_time - start_time >= 0.1

    async def test_wait_action_element_based(self, mock_page_with_playwright: PageBase) -> None:
        """Test element-based wait action."""
        logger.info("Testing WaitAction with element wait")

        action = WaitAction(selector="#loading", state="visible")

        result = await action.execute_with_hooks(mock_page_with_playwright)

        logger.info(f"Element wait result: {result}")
        assert result.success is True
        assert result.data["selector"] == "#loading"
        assert result.data["state"] == "visible"

    async def test_hover_action_success(self, mock_page_with_playwright: PageBase) -> None:
        """Test successful hover action."""
        logger.info("Testing HoverAction success")

        action = HoverAction(selector=".menu-item", position={"x": 10, "y": 5})

        result = await action.execute_with_hooks(mock_page_with_playwright)

        logger.info(f"Hover result: {result}")
        assert result.success is True
        assert result.data["selector"] == ".menu-item"
        assert result.data["position"] == {"x": 10, "y": 5}

    async def test_scroll_action_success(self, mock_page_with_playwright: PageBase) -> None:
        """Test successful scroll action."""
        logger.info("Testing ScrollAction success")

        action = ScrollAction(direction="down", pixels=300)

        result = await action.execute_with_hooks(mock_page_with_playwright)

        logger.info(f"Scroll result: {result}")
        assert result.success is True
        assert result.data["direction"] == "down"
        assert result.data["pixels"] == 300

    def test_action_validation_errors(self) -> None:
        """Test validation errors for various actions."""
        logger.info("Testing action validation errors")

        # NavigationAction with invalid URL
        with pytest.raises(PydanticValidationError):
            NavigationAction(url="invalid-url")

        # WaitAction with invalid state
        with pytest.raises(PydanticValidationError):
            WaitAction(selector="#element", state="invalid_state")

        # ScrollAction with invalid direction
        with pytest.raises(PydanticValidationError):
            ScrollAction(direction="invalid_direction")


class TestActionIntegration:
    """Test action framework integration scenarios."""

    @pytest.fixture
    async def mock_page(self) -> PageBase:
        """Create mock PageBase with comprehensive mocking."""
        mock_playwright_page = AsyncMock()

        # Mock all necessary methods
        mock_playwright_page.click = AsyncMock()
        mock_playwright_page.fill = AsyncMock()
        mock_playwright_page.goto = AsyncMock(return_value=Mock(status=200))
        mock_playwright_page.hover = AsyncMock()
        mock_playwright_page.wait_for_selector = AsyncMock()

        mock_locator = AsyncMock()
        mock_locator.is_visible = AsyncMock(return_value=True)
        mock_locator.is_enabled = AsyncMock(return_value=True)
        mock_locator.text_content = AsyncMock(return_value="Element Text")
        mock_locator.get_attribute = AsyncMock(return_value="attribute-value")
        mock_playwright_page.locator = AsyncMock(return_value=mock_locator)

        page = PageBase(session_id="integration-test", url="https://example.com")
        page.set_playwright_page(mock_playwright_page)

        return page

    async def test_complex_action_workflow(self, mock_page: PageBase) -> None:
        """Test complex workflow with multiple action types."""
        logger.info("Testing complex action workflow")

        # Create a complex workflow
        workflow = ComposedAction(
            actions=[
                NavigationAction(url="https://example.com/login", verify_navigation=False),
                WaitAction(selector="#login-form", state="visible"),
                FillAction(selector="input[name='username']", value="testuser", verify_fill=False),
                FillAction(selector="input[name='password']", value="password123", verify_fill=False),
                ClickAction(selector="button[type='submit']"),
                WaitAction(selector="#dashboard", state="visible"),
            ]
        )

        result = await workflow.execute_with_hooks(mock_page)

        logger.info(f"Workflow result: {result.summary()}")
        assert result.success is True
        assert result.data["completed_steps"] == 6
        assert len(result.metadata["results"]) == 6

    async def test_conditional_action_execution(self, mock_page: PageBase) -> None:
        """Test conditional action execution."""
        logger.info("Testing conditional action execution")

        # Create condition that should succeed
        condition = WaitAction(selector="#element", state="visible")
        then_action = ClickAction(selector="#button")
        else_action = NavigationAction(url="https://example.com/error", verify_navigation=False)

        conditional = ConditionalAction(condition_action=condition, then_action=then_action, else_action=else_action)

        result = await conditional.execute_with_hooks(mock_page)

        logger.info(f"Conditional result: {result}")
        assert result.success is True
        assert result.metadata["condition_result"] is True

    async def test_action_composition_chaining(self, mock_page: PageBase) -> None:
        """Test fluent action composition."""
        logger.info("Testing action composition chaining")

        click1 = ClickAction(selector="#button1")
        click2 = ClickAction(selector="#button2")
        click3 = ClickAction(selector="#button3")

        # Chain actions using compose_with and then
        chain = click1.compose_with(click2).then(click3)

        # This should create a ComposedAction with nested composition
        assert isinstance(chain, ComposedAction)

        result = await chain.execute_with_hooks(mock_page)

        logger.info(f"Action chain result: {result}")
        assert result.success is True

    async def test_action_retry_with_recovery(self, mock_page: PageBase) -> None:
        """Test action retry with eventual success."""
        logger.info("Testing action retry with recovery")

        # Create a mock that fails twice then succeeds
        call_count = 0

        async def failing_click(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary failure")

        mock_page.playwright_page.click.side_effect = failing_click

        action = ClickAction(selector="#flaky-button", retry_count=3)

        result = await action.execute_with_hooks(mock_page)

        logger.info(f"Retry recovery result: {result}")
        assert result.success is True
        assert result.retry_count == 2  # Failed twice, succeeded on third try
        assert call_count == 3

    async def test_performance_metrics_tracking(self, mock_page: PageBase) -> None:
        """Test tracking performance metrics across actions."""
        logger.info("Testing performance metrics tracking")

        metrics = ActionMetrics()

        actions = [
            ClickAction(selector="#button1"),
            FillAction(selector="#input1", value="test", verify_fill=False),
            WaitAction(wait_time=0.01),  # Very short wait
            ClickAction(selector="#button2"),
        ]

        for action in actions:
            result = await action.execute_with_hooks(mock_page)
            metrics.record_result(result)

        logger.info(f"Final metrics: {metrics}")
        assert metrics.total_actions == 4
        assert metrics.successful_actions == 4
        assert metrics.success_rate == 100.0
        assert metrics.total_execution_time > 0
