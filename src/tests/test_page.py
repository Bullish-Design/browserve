"""
Test suite for PageBase core page interface.
"""

from __future__ import annotations
import pytest
import asyncio
import time
import logging
from unittest.mock import AsyncMock, Mock, patch
from pydantic import ValidationError as PydanticValidationError

from browserve.core.page import PageBase
from browserve.events import InteractionEvent, NavigationEvent
from browserve.exceptions import ActionExecutionError, ElementError, ValidationError, ErrorCodes
from browserve.models.config import ConfigBase, BrowserConfig

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPageBaseInitialization:
    """Test PageBase creation and validation."""

    def test_valid_initialization(self) -> None:
        """Test creating PageBase with valid parameters."""
        logger.info("Testing PageBase initialization with valid parameters")

        page = PageBase(session_id="test-session-123", url="https://example.com")

        logger.info(f"Created PageBase with session_id: {page.session_id}")
        logger.info(f"PageBase URL: {page.url}")
        logger.info(f"PageBase is_active: {page.is_active}")

        assert page.session_id == "test-session-123"
        assert page.url == "https://example.com"
        assert isinstance(page.config, ConfigBase)
        assert page.is_active is False  # No Playwright page set yet

        logger.info("✓ Valid initialization test passed")

    def test_initialization_with_config(self) -> None:
        """Test PageBase with custom configuration."""
        logger.info("Testing PageBase initialization with custom config")

        config = ConfigBase(browser_config=BrowserConfig(headless=False, timeout=45.0))
        logger.info(
            f"Created custom config: headless={config.browser_config.headless}, timeout={config.browser_config.timeout}"
        )

        page = PageBase(session_id="test-session", url="https://example.com", config=config)

        logger.info(f"PageBase config headless: {page.config.browser_config.headless}")
        logger.info(f"PageBase config timeout: {page.config.browser_config.timeout}")

        assert page.config.browser_config.headless is False
        assert page.config.browser_config.timeout == 45.0

        logger.info("✓ Custom config initialization test passed")

    def test_invalid_url_validation(self) -> None:
        """Test URL validation during initialization."""
        logger.info("Testing PageBase URL validation with invalid URLs")

        invalid_urls = [
            ("", "empty URL"),
            ("example.com", "URL without scheme"),
            ("https://", "URL without domain"),
            ("ftp://example.com", "invalid scheme"),
        ]

        for url, description in invalid_urls:
            logger.info(f"Testing {description}: '{url}'")
            with pytest.raises(PydanticValidationError):
                PageBase(session_id="test", url=url)
            logger.info(f"✓ Correctly rejected {description}")

        logger.info("✓ URL validation test passed")

    def test_invalid_session_id_validation(self) -> None:
        """Test session ID validation."""
        logger.info("Testing PageBase session ID validation")

        invalid_session_ids = [("", "empty session ID"), ("   ", "whitespace only session ID")]

        for session_id, description in invalid_session_ids:
            logger.info(f"Testing {description}: '{session_id}'")
            with pytest.raises(PydanticValidationError):
                PageBase(session_id=session_id, url="https://example.com")
            logger.info(f"✓ Correctly rejected {description}")

        logger.info("✓ Session ID validation test passed")

    def test_valid_urls(self) -> None:
        """Test various valid URL formats."""
        logger.info("Testing PageBase with various valid URL formats")

        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://subdomain.example.com/path?param=value",
            "http://192.168.1.1:3000",
        ]

        for url in valid_urls:
            logger.info(f"Testing valid URL: {url}")
            page = PageBase(session_id="test", url=url)
            assert page.url == url
            logger.info(f"✓ Successfully created PageBase with URL: {url}")

        logger.info("✓ Valid URLs test passed")


class TestPageBasePlaywrightIntegration:
    """Test PageBase integration with Playwright."""

    @pytest.fixture
    def mock_playwright_page(self) -> AsyncMock:
        """Create mock Playwright page."""
        logger.info("Creating mock Playwright page for testing")

        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.click = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.hover = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.reload = AsyncMock()
        mock_page.go_back = AsyncMock()
        mock_page.go_forward = AsyncMock()

        # Mock locator
        mock_locator = AsyncMock()
        mock_locator.is_visible = AsyncMock(return_value=True)
        mock_locator.is_enabled = AsyncMock(return_value=True)
        mock_locator.text_content = AsyncMock(return_value="Button Text")
        mock_locator.get_attribute = AsyncMock(return_value="test-value")
        mock_locator.evaluate = AsyncMock(return_value="button")
        mock_page.locator = AsyncMock(return_value=mock_locator)

        logger.info("✓ Mock Playwright page created with all methods")
        return mock_page

    @pytest.fixture
    def page_with_playwright(self, mock_playwright_page: AsyncMock) -> PageBase:
        """Create PageBase with mock Playwright page."""
        logger.info("Creating PageBase with mock Playwright integration")

        page = PageBase(session_id="test-session", url="https://example.com")
        page.set_playwright_page(mock_playwright_page)

        logger.info(f"PageBase created with session_id: {page.session_id}")
        logger.info(f"Playwright page set, is_active: {page.is_active}")

        return page

    def test_set_playwright_page(self, mock_playwright_page: AsyncMock) -> None:
        """Test setting Playwright page instance."""
        logger.info("Testing PageBase.set_playwright_page() method")

        page = PageBase(session_id="test", url="https://example.com")
        logger.info(f"Initial is_active state: {page.is_active}")
        assert not page.is_active

        page.set_playwright_page(mock_playwright_page)
        logger.info(f"After setting Playwright page - is_active: {page.is_active}")
        logger.info(f"URL updated to: {page.url}")

        assert page.is_active
        assert page.url == mock_playwright_page.url

        logger.info("✓ Playwright page integration test passed")

    def test_current_url_property(self, page_with_playwright: PageBase) -> None:
        """Test current_url property gets URL from Playwright."""
        logger.info("Testing PageBase.current_url property")

        # Should return Playwright page URL when available
        current_url = page_with_playwright.current_url
        logger.info(f"Current URL from Playwright page: {current_url}")
        assert current_url == "https://example.com"

        # Should return stored URL when Playwright not available
        page_without_playwright = PageBase(session_id="test", url="https://stored.com")
        stored_url = page_without_playwright.current_url
        logger.info(f"Current URL from stored value: {stored_url}")
        assert stored_url == "https://stored.com"

        logger.info("✓ Current URL property test passed")


class TestPageBaseInteractions:
    """Test PageBase browser interaction methods."""

    @pytest.fixture
    def page_with_playwright(self) -> tuple[PageBase, AsyncMock]:
        """Create PageBase with mock Playwright page and return both."""
        logger.info("Setting up PageBase with mock Playwright for interaction testing")

        mock_playwright_page = AsyncMock()
        mock_playwright_page.url = "https://example.com"
        mock_playwright_page.click = AsyncMock()
        mock_playwright_page.fill = AsyncMock()
        mock_playwright_page.goto = AsyncMock()
        mock_playwright_page.hover = AsyncMock()

        # Mock response for navigation
        mock_response = Mock()
        mock_response.status = 200
        mock_playwright_page.goto.return_value = mock_response
        mock_playwright_page.reload.return_value = mock_response
        mock_playwright_page.go_back.return_value = mock_response
        mock_playwright_page.go_forward.return_value = mock_response

        # Mock locator for element info
        mock_locator = AsyncMock()
        mock_locator.text_content = AsyncMock(return_value="Button")
        mock_locator.evaluate = AsyncMock(return_value="button")
        mock_playwright_page.locator = AsyncMock(return_value=mock_locator)

        page = PageBase(session_id="test-session", url="https://example.com")
        page.set_playwright_page(mock_playwright_page)

        logger.info("✓ PageBase with mock Playwright setup complete")
        return page, mock_playwright_page

    async def test_click_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful click interaction."""
        logger.info("Testing successful click interaction with event emission")

        page, mock_playwright = page_with_playwright

        # Set up event handler to capture emission
        emitted_events = []

        @page.on("interaction")
        async def capture_event(event):
            logger.info(f"Event captured: {event.action} on {event.selector}")
            emitted_events.append(event)

        logger.info("Event handler registered for interaction events")

        # Perform click
        logger.info("Performing click on #test-button")
        await page.click("#test-button")

        # Verify Playwright was called
        logger.info("Verifying Playwright click method was called with correct parameters")
        mock_playwright.click.assert_called_once_with(
            "#test-button",
            button="left",
            timeout=30000,  # Default config timeout in milliseconds
        )
        logger.info("✓ Playwright click method called correctly")

        # Verify event emission
        logger.info(f"Events emitted: {len(emitted_events)}")
        assert len(emitted_events) == 1

        event = emitted_events[0]
        logger.info(f"Event details - type: {type(event)}, action: {event.action}")
        logger.info(f"Event selector: {event.selector}, URL: {event.page_url}")

        assert isinstance(event, InteractionEvent)
        assert event.action == "click"
        assert event.selector == "#test-button"
        assert event.page_url == "https://example.com"
        assert event.session_id == "test-session"

        logger.info("✓ Click interaction test passed")

    async def test_click_with_options(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test click with additional options."""
        logger.info("Testing click with custom options (right button, custom timeout)")

        page, mock_playwright = page_with_playwright

        await page.click("#button", button="right", timeout=10.0, force=True)

        logger.info("Verifying click called with custom parameters")
        mock_playwright.click.assert_called_once_with(
            "#button",
            button="right",
            timeout=10000,  # 10 seconds in milliseconds
            force=True,
        )

        logger.info("✓ Click with options test passed")

    async def test_click_without_playwright(self) -> None:
        """Test click fails without Playwright page."""
        logger.info("Testing click failure when Playwright page not initialized")

        page = PageBase(session_id="test", url="https://example.com")
        logger.info(f"Page is_active status: {page.is_active}")

        with pytest.raises(ActionExecutionError) as exc_info:
            await page.click("#button")

        logger.info(f"Exception raised: {exc_info.value}")
        logger.info(f"Error code: {exc_info.value.error_code}")

        assert exc_info.value.error_code == ErrorCodes.SESSION_NOT_ACTIVE
        assert "not initialized" in str(exc_info.value)

        logger.info("✓ Click without Playwright test passed")

    async def test_click_playwright_error(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test click handles Playwright errors."""
        logger.info("Testing click error handling when Playwright throws exception")

        page, mock_playwright = page_with_playwright
        mock_playwright.click.side_effect = Exception("Element not found")
        logger.info("Mock configured to raise 'Element not found' exception")

        with pytest.raises(ActionExecutionError) as exc_info:
            await page.click("#missing")

        logger.info(f"Exception caught: {exc_info.value}")
        logger.info(f"Error code: {exc_info.value.error_code}")

        assert exc_info.value.error_code == ErrorCodes.INTERACTION_FAILED
        assert "Element not found" in str(exc_info.value)

        logger.info("✓ Click error handling test passed")

    async def test_fill_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful fill interaction."""
        logger.info("Testing successful fill interaction with event emission")

        page, mock_playwright = page_with_playwright

        emitted_events = []

        @page.on("interaction")
        async def capture_event(event):
            logger.info(f"Fill event captured: {event.action} on {event.selector} with value '{event.value}'")
            emitted_events.append(event)

        logger.info("Performing fill on #username with value 'testuser'")
        await page.fill("#username", "testuser")

        logger.info("Verifying Playwright fill method was called")
        mock_playwright.fill.assert_called_once_with("#username", "testuser", timeout=30000)

        logger.info(f"Events emitted: {len(emitted_events)}")
        assert len(emitted_events) == 1

        event = emitted_events[0]
        logger.info(f"Event action: {event.action}, value: {event.value}")
        assert event.action == "fill"
        assert event.value == "testuser"

        logger.info("✓ Fill interaction test passed")

    async def test_navigate_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful navigation."""
        logger.info("Testing successful navigation with event emission")

        page, mock_playwright = page_with_playwright

        emitted_events = []

        @page.on("navigation")
        async def capture_event(event):
            logger.info(f"Navigation event: {event.method} from {event.from_url} to {event.to_url}")
            emitted_events.append(event)

        new_url = "https://example.com/login"
        logger.info(f"Navigating to: {new_url}")

        await page.navigate(new_url)

        # Verify Playwright navigation
        logger.info("Verifying Playwright goto method was called")
        mock_playwright.goto.assert_called_once_with(new_url, wait_until="load", timeout=30000)

        # Verify URL updated
        logger.info(f"Page URL updated to: {page.url}")
        assert page.url == new_url

        # Verify event emission
        logger.info(f"Navigation events emitted: {len(emitted_events)}")
        assert len(emitted_events) == 1

        event = emitted_events[0]
        logger.info(f"Event details - method: {event.method}, status: {event.status_code}")

        assert isinstance(event, NavigationEvent)
        assert event.from_url == "https://example.com"
        assert event.to_url == new_url
        assert event.method == "navigate"
        assert event.status_code == 200

        logger.info("✓ Navigation success test passed")

    async def test_navigate_invalid_url(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test navigation with invalid URL."""
        logger.info("Testing navigation with invalid URL")

        page, _ = page_with_playwright

        invalid_url = "invalid-url"
        logger.info(f"Attempting navigation to invalid URL: {invalid_url}")

        with pytest.raises(ValidationError) as exc_info:
            await page.navigate(invalid_url)

        logger.info(f"ValidationError raised: {exc_info.value}")
        logger.info("✓ Invalid URL navigation test passed")

    async def test_hover_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful hover interaction."""
        logger.info("Testing successful hover interaction")

        page, mock_playwright = page_with_playwright

        emitted_events = []

        @page.on("interaction")
        async def capture_event(event):
            logger.info(f"Hover event captured on: {event.selector}")
            emitted_events.append(event)

        logger.info("Performing hover on #menu-item")
        await page.hover("#menu-item")

        logger.info("Verifying Playwright hover method was called")
        mock_playwright.hover.assert_called_once_with("#menu-item", timeout=30000)

        logger.info(f"Hover events emitted: {len(emitted_events)}")
        assert len(emitted_events) == 1
        assert emitted_events[0].action == "hover"

        logger.info("✓ Hover interaction test passed")


class TestPageBaseElementMethods:
    """Test PageBase element query and validation methods."""

    @pytest.fixture
    def page_with_playwright(self) -> tuple[PageBase, AsyncMock]:
        """Create PageBase with mock Playwright for element testing."""
        logger.info("Setting up PageBase with mock Playwright for element method testing")

        mock_playwright_page = AsyncMock()
        mock_playwright_page.url = "https://example.com"
        mock_playwright_page.wait_for_selector = AsyncMock()

        mock_locator = AsyncMock()
        mock_locator.is_visible = AsyncMock(return_value=True)
        mock_locator.is_enabled = AsyncMock(return_value=True)
        mock_locator.text_content = AsyncMock(return_value="Element Text")
        mock_locator.get_attribute = AsyncMock(return_value="test-value")
        mock_playwright_page.locator = AsyncMock(return_value=mock_locator)

        page = PageBase(session_id="test", url="https://example.com")
        page.set_playwright_page(mock_playwright_page)

        logger.info("✓ Element testing setup complete")
        return page, mock_playwright_page

    async def test_wait_for_element_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful element wait."""
        logger.info("Testing successful element wait operation")

        page, mock_playwright = page_with_playwright

        selector = "#element"
        state = "visible"
        timeout = 10.0

        logger.info(f"Waiting for element: {selector}, state: {state}, timeout: {timeout}s")
        await page.wait_for_element(selector, state=state, timeout=timeout)

        logger.info("Verifying Playwright wait_for_selector was called with correct parameters")
        mock_playwright.wait_for_selector.assert_called_once_with(
            selector,
            state=state,
            timeout=10000,  # Convert to milliseconds
        )

        logger.info("✓ Element wait success test passed")

    async def test_wait_for_element_failure(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test element wait timeout."""
        logger.info("Testing element wait timeout handling")

        page, mock_playwright = page_with_playwright
        mock_playwright.wait_for_selector.side_effect = Exception("Timeout")
        logger.info("Mock configured to raise timeout exception")

        with pytest.raises(ElementError) as exc_info:
            await page.wait_for_element("#missing")

        logger.info(f"ElementError raised: {exc_info.value}")
        logger.info(f"Error code: {exc_info.value.error_code}")

        assert exc_info.value.error_code == ErrorCodes.ELEMENT_NOT_FOUND
        logger.info("✓ Element wait failure test passed")

    async def test_is_element_visible_true(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test element visibility check returns True."""
        logger.info("Testing element visibility check for visible element")

        page, mock_playwright = page_with_playwright

        selector = "#visible-element"
        logger.info(f"Checking visibility of: {selector}")

        result = await page.is_element_visible(selector)

        logger.info(f"Visibility result: {result}")
        logger.info("Verifying locator was called correctly")

        assert result is True
        mock_playwright.locator.assert_called_once_with(selector)

        logger.info("✓ Element visible test passed")

    async def test_is_element_visible_false(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test element visibility returns False for hidden element."""
        logger.info("Testing element visibility check for hidden element")

        page, mock_playwright = page_with_playwright
        mock_locator = mock_playwright.locator.return_value
        mock_locator.is_visible.return_value = False
        logger.info("Mock configured to return False for visibility")

        result = await page.is_element_visible("#hidden-element")

        logger.info(f"Visibility result for hidden element: {result}")
        assert result is False

        logger.info("✓ Element hidden test passed")

    async def test_is_element_visible_no_playwright(self) -> None:
        """Test element visibility returns False without Playwright."""
        logger.info("Testing element visibility without Playwright page")

        page = PageBase(session_id="test", url="https://example.com")
        logger.info(f"Page is_active status: {page.is_active}")

        result = await page.is_element_visible("#element")

        logger.info(f"Visibility result without Playwright: {result}")
        assert result is False

        logger.info("✓ No Playwright visibility test passed")

    async def test_get_element_text_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test getting element text content."""
        logger.info("Testing successful element text extraction")

        page, mock_playwright = page_with_playwright

        selector = "#element"
        expected_text = "Element Text"

        logger.info(f"Getting text content from: {selector}")
        text = await page.get_element_text(selector)

        logger.info(f"Retrieved text: '{text}'")
        logger.info("Verifying locator was called correctly")

        assert text == expected_text
        mock_playwright.locator.assert_called_once_with(selector)

        logger.info("✓ Element text extraction test passed")

    async def test_get_element_text_failure(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test getting text from non-existent element."""
        logger.info("Testing element text extraction failure handling")

        page, mock_playwright = page_with_playwright
        mock_locator = mock_playwright.locator.return_value
        mock_locator.text_content.side_effect = Exception("Not found")
        logger.info("Mock configured to raise exception for text extraction")

        text = await page.get_element_text("#missing")

        logger.info(f"Text result for missing element: {text}")
        assert text is None

        logger.info("✓ Element text failure test passed")

    async def test_get_element_attribute_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test getting element attribute."""
        logger.info("Testing successful element attribute extraction")

        page, mock_playwright = page_with_playwright

        selector = "#element"
        attribute = "data-test"
        expected_value = "test-value"

        logger.info(f"Getting attribute '{attribute}' from: {selector}")
        value = await page.get_element_attribute(selector, attribute)

        logger.info(f"Retrieved attribute value: '{value}'")
        assert value == expected_value

        logger.info("✓ Element attribute extraction test passed")


class TestPageBaseEventSystem:
    """Test PageBase event emission and handling."""

    @pytest.fixture
    def page_with_playwright(self) -> tuple[PageBase, AsyncMock]:
        """Create PageBase with mock for event testing."""
        logger.info("Setting up PageBase with mock Playwright for event system testing")

        mock_playwright_page = AsyncMock()
        mock_playwright_page.url = "https://example.com"
        mock_playwright_page.click = AsyncMock()

        # Mock locator for element info
        mock_locator = AsyncMock()
        mock_locator.text_content = AsyncMock(return_value="Button")
        mock_locator.evaluate = AsyncMock(return_value="button")
        mock_playwright_page.locator = AsyncMock(return_value=mock_locator)

        page = PageBase(session_id="test", url="https://example.com")
        page.set_playwright_page(mock_playwright_page)

        logger.info("✓ Event system testing setup complete")
        return page, mock_playwright_page

    async def test_multiple_event_handlers(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test multiple handlers receive same event."""
        logger.info("Testing multiple event handlers for same event type")

        page, _ = page_with_playwright

        handler1_called = False
        handler2_called = False

        @page.on("interaction")
        async def handler1(event):
            nonlocal handler1_called
            handler1_called = True
            logger.info(f"Handler1 received event: {event.action}")
            assert event.action == "click"

        @page.on("interaction")
        async def handler2(event):
            nonlocal handler2_called
            handler2_called = True
            logger.info(f"Handler2 received event on selector: {event.selector}")
            assert event.selector == "#test"

        logger.info("Registered 2 event handlers for 'interaction' events")
        logger.info("Performing click to trigger event emission")

        await page.click("#test")

        logger.info(f"Handler1 called: {handler1_called}")
        logger.info(f"Handler2 called: {handler2_called}")

        assert handler1_called
        assert handler2_called

        logger.info("✓ Multiple event handlers test passed")

    async def test_event_handler_error_isolation(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test that handler errors don't break page operation."""
        logger.info("Testing event handler error isolation")

        page, _ = page_with_playwright

        good_handler_called = False

        @page.on("interaction")
        async def failing_handler(event):
            logger.info("Failing handler called - about to raise exception")
            raise ValueError("Handler error")

        @page.on("interaction")
        async def good_handler(event):
            nonlocal good_handler_called
            good_handler_called = True
            logger.info("Good handler called successfully")

        logger.info("Registered failing handler and good handler")
        logger.info("Performing click - should not raise exception despite failing handler")

        # Should not raise exception despite failing handler
        await page.click("#test")

        logger.info(f"Good handler was called: {good_handler_called}")

        # Good handler should still be called
        assert good_handler_called

        logger.info("✓ Event handler error isolation test passed")

    async def test_different_event_types(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test different event types are emitted correctly."""
        logger.info("Testing different event types are emitted correctly")

        page, mock_playwright = page_with_playwright

        # Mock navigation response
        mock_response = Mock()
        mock_response.status = 200
        mock_playwright.goto.return_value = mock_response

        interaction_events = []
        navigation_events = []

        @page.on("interaction")
        async def capture_interaction(event):
            logger.info(f"Interaction event captured: {event.action}")
            interaction_events.append(event)

        @page.on("navigation")
        async def capture_navigation(event):
            logger.info(f"Navigation event captured: {event.method}")
            navigation_events.append(event)

        logger.info("Registered handlers for interaction and navigation events")

        # Perform interactions
        logger.info("Performing click interaction")
        await page.click("#button")

        logger.info("Performing navigation")
        await page.navigate("https://example.com/page")

        # Verify event types
        logger.info(f"Interaction events captured: {len(interaction_events)}")
        logger.info(f"Navigation events captured: {len(navigation_events)}")

        assert len(interaction_events) == 1
        assert len(navigation_events) == 1

        logger.info(f"Interaction event type: {type(interaction_events[0])}")
        logger.info(f"Navigation event type: {type(navigation_events[0])}")

        assert isinstance(interaction_events[0], InteractionEvent)
        assert isinstance(navigation_events[0], NavigationEvent)

        logger.info("✓ Different event types test passed")


class TestPageBaseNavigationMethods:
    """Test PageBase navigation methods (reload, back, forward)."""

    @pytest.fixture
    def page_with_playwright(self) -> tuple[PageBase, AsyncMock]:
        """Create PageBase with navigation mock setup."""
        logger.info("Setting up PageBase for navigation method testing")

        mock_playwright_page = AsyncMock()
        mock_playwright_page.url = "https://example.com/page1"

        mock_response = Mock()
        mock_response.status = 200

        mock_playwright_page.reload = AsyncMock(return_value=mock_response)
        mock_playwright_page.go_back = AsyncMock(return_value=mock_response)
        mock_playwright_page.go_forward = AsyncMock(return_value=mock_response)

        page = PageBase(session_id="test", url="https://example.com/page1")
        page.set_playwright_page(mock_playwright_page)

        logger.info("✓ Navigation testing setup complete")
        return page, mock_playwright_page

    async def test_reload_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful page reload."""
        logger.info("Testing successful page reload with event emission")

        page, mock_playwright = page_with_playwright

        navigation_events = []

        @page.on("navigation")
        async def capture_event(event):
            logger.info(f"Navigation event captured: {event.method} with status {event.status_code}")
            navigation_events.append(event)

        logger.info("Performing page reload")
        await page.reload()

        logger.info("Verifying Playwright reload was called")
        mock_playwright.reload.assert_called_once()

        logger.info(f"Navigation events emitted: {len(navigation_events)}")
        assert len(navigation_events) == 1

        event = navigation_events[0]
        logger.info(f"Event method: {event.method}, status: {event.status_code}")
        assert event.method == "reload"
        assert event.status_code == 200

        logger.info("✓ Page reload test passed")

    async def test_go_back_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful back navigation."""
        logger.info("Testing successful back navigation with URL change")

        page, mock_playwright = page_with_playwright

        # Mock URL change after going back
        mock_playwright.url = "https://example.com/previous"
        logger.info("Mock configured to change URL after go_back")

        navigation_events = []

        @page.on("navigation")
        async def capture_event(event):
            logger.info(f"Back navigation event: {event.from_url} -> {event.to_url}")
            navigation_events.append(event)

        initial_url = page.url
        logger.info(f"Initial URL: {initial_url}")

        await page.go_back()

        logger.info("Verifying Playwright go_back was called")
        mock_playwright.go_back.assert_called_once()

        logger.info(f"Navigation events emitted: {len(navigation_events)}")
        assert len(navigation_events) == 1

        event = navigation_events[0]
        logger.info(f"Event details - method: {event.method}")
        logger.info(f"URL change: {event.from_url} -> {event.to_url}")

        assert event.method == "back"
        assert event.from_url == "https://example.com/page1"
        assert event.to_url == "https://example.com/previous"

        logger.info("✓ Go back navigation test passed")

    async def test_go_forward_success(self, page_with_playwright: tuple[PageBase, AsyncMock]) -> None:
        """Test successful forward navigation."""
        logger.info("Testing successful forward navigation")

        page, mock_playwright = page_with_playwright

        mock_playwright.url = "https://example.com/forward"
        logger.info("Mock configured to change URL after go_forward")

        navigation_events = []

        @page.on("navigation")
        async def capture_event(event):
            logger.info(f"Forward navigation event: {event.method}")
            navigation_events.append(event)

        await page.go_forward()

        logger.info("Verifying Playwright go_forward was called")
        mock_playwright.go_forward.assert_called_once()

        logger.info(f"Navigation events emitted: {len(navigation_events)}")
        assert len(navigation_events) == 1

        event = navigation_events[0]
        logger.info(f"Event method: {event.method}")
        assert event.method == "forward"

        logger.info("✓ Go forward navigation test passed")
