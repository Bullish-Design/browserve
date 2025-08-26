"""
Core page interface for browser interaction with event emission.

PageBase serves as the primary interface that developers inherit from
to build site-specific automation. It combines Pydantic validation
with event emission for comprehensive interaction tracking.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, TYPE_CHECKING
import time
from urllib.parse import urlparse

from ..events.base import InteractionEvent, NavigationEvent
from ..events.handlers import EventEmitter
from ..exceptions import ElementError, ActionExecutionError, ValidationError, ErrorCodes
from ..models.config import ConfigBase

from playwright.async_api import Page, Locator

# if TYPE_CHECKING:
#    from playwright.async_api import Page, Locator


class PageBase(BaseModel, EventEmitter):
    """
    Core page interface with event emission capabilities.

    PageBase serves as the foundation for all browser automation classes.
    It wraps Playwright Page functionality while automatically emitting
    events for all interactions, providing comprehensive logging and
    monitoring capabilities.

    Example:
        >>> page = PageBase(
        ...     session_id="session-123",
        ...     url="https://example.com"
        ... )
        >>> @page.on("interaction")
        ... async def log_clicks(event):
        ...     print(f"Clicked: {event.selector}")
        >>> await page.click("#button")
    """

    session_id: str = Field(description="Associated session identifier")
    url: str = Field(description="Current page URL")
    config: ConfigBase = Field(default_factory=ConfigBase, description="Page configuration settings")
    playwright_page: Optional[Page] = Field(None, exclude=True, description="Internal Playwright page instance")
    active_state: bool = Field(True, exclude=True, description="Whether page is active and usable")

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data: Any) -> None:
        """
        Initialize PageBase with both BaseModel and EventEmitter.

        Args:
            **data: Page initialization data including session_id and url
        """
        BaseModel.__init__(self, **data)
        EventEmitter.__init__(self)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """
        Ensure URL is properly formatted with scheme and domain.

        Args:
            v: URL string to validate

        Returns:
            Validated URL string

        Raises:
            ValueError: If URL is malformed or missing required components
        """
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")

        url = v.strip()
        parsed = urlparse(url)

        if not parsed.scheme:
            raise ValueError("URL must include scheme (http:// or https://)")

        if not parsed.netloc:
            raise ValueError("URL must include domain")

        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL scheme must be http or https")

        return url

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """
        Ensure session ID is not empty and properly formatted.

        Args:
            v: Session ID to validate

        Returns:
            Validated session ID

        Raises:
            ValueError: If session ID is empty or invalid
        """
        if not v or not v.strip():
            raise ValueError("Session ID cannot be empty")

        return v.strip()

    async def click(self, selector: str, button: str = "left", timeout: Optional[float] = None, **kwargs: Any) -> None:
        """
        Click element and emit interaction event.

        Args:
            selector: CSS selector or XPath for target element
            button: Mouse button to click (left, right, middle)
            timeout: Maximum time to wait for element
            **kwargs: Additional Playwright click options

        Raises:
            ActionExecutionError: If click operation fails
            ElementError: If element cannot be found or interacted with
        """
        if not self.playwright_page:
            raise ActionExecutionError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type="click",
                selector=selector,
            )

        # Use config timeout if not provided
        if timeout is None:
            timeout = self.config.browser_config.timeout

        try:
            # Attempt the click operation
            await self.playwright_page.click(
                selector,
                button=button,
                timeout=timeout * 1000,  # Playwright uses milliseconds
                **kwargs,
            )

            # Get element information for event
            element_text = None
            element_tag = None
            try:
                locator = self.playwright_page.locator(selector)
                element_text = await locator.text_content()
                element_tag = await locator.evaluate("el => el.tagName.toLowerCase()")
            except:
                # Element info is nice-to-have, don't fail if unavailable
                pass

            # Emit interaction event after successful operation
            event = InteractionEvent(
                timestamp=time.time(),
                page_url=self.url,
                session_id=self.session_id,
                action="click",
                selector=selector,
                element_text=element_text,
                element_tag=element_tag,
                metadata={"button": button, "timeout": timeout, **kwargs},
            )
            await self.emit(event)

        except Exception as e:
            raise ActionExecutionError(
                f"Click failed on selector '{selector}': {str(e)}",
                error_code=ErrorCodes.INTERACTION_FAILED,
                action_type="click",
                selector=selector,
                timeout=timeout,
            )

    async def fill(self, selector: str, value: str, timeout: Optional[float] = None, **kwargs: Any) -> None:
        """
        Fill form field and emit interaction event.

        Args:
            selector: CSS selector or XPath for input element
            value: Text value to fill
            timeout: Maximum time to wait for element
            **kwargs: Additional Playwright fill options

        Raises:
            ActionExecutionError: If fill operation fails
            ElementError: If element cannot be found or is not fillable
        """
        if not self.playwright_page:
            raise ActionExecutionError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type="fill",
                selector=selector,
            )

        if timeout is None:
            timeout = self.config.browser_config.timeout

        try:
            # Attempt the fill operation
            await self.playwright_page.fill(selector, value, timeout=timeout * 1000, **kwargs)

            # Get element information
            element_tag = None
            try:
                locator = self.playwright_page.locator(selector)
                element_tag = await locator.evaluate("el => el.tagName.toLowerCase()")
            except:
                pass

            # Emit interaction event
            event = InteractionEvent(
                timestamp=time.time(),
                page_url=self.url,
                session_id=self.session_id,
                action="fill",
                selector=selector,
                value=value,
                element_tag=element_tag,
                metadata={"timeout": timeout, **kwargs},
            )
            await self.emit(event)

        except Exception as e:
            raise ActionExecutionError(
                f"Fill failed on selector '{selector}': {str(e)}",
                error_code=ErrorCodes.INTERACTION_FAILED,
                action_type="fill",
                selector=selector,
                timeout=timeout,
            )

    async def navigate(
        self, url: str, wait_until: str = "load", timeout: Optional[float] = None, **kwargs: Any
    ) -> None:
        """
        Navigate to URL and emit navigation event.

        Args:
            url: Target URL to navigate to
            wait_until: When to consider navigation complete
            timeout: Maximum time to wait for navigation
            **kwargs: Additional Playwright goto options

        Raises:
            ActionExecutionError: If navigation fails
            ValidationError: If URL is invalid
        """
        if not self.playwright_page:
            raise ActionExecutionError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type="navigate",
            )

        # Validate URL format
        try:
            self.validate_url(url)
        except ValueError as e:
            raise ValidationError(f"Invalid URL format: {str(e)}", field_name="url", invalid_value=url)

        if timeout is None:
            timeout = self.config.browser_config.timeout

        old_url = self.url
        start_time = time.time()

        try:
            # Attempt navigation
            response = await self.playwright_page.goto(url, wait_until=wait_until, timeout=timeout * 1000, **kwargs)

            # Update internal URL
            self.url = url

            # Calculate load time
            load_time = time.time() - start_time
            status_code = response.status if response else None

            # Emit navigation event
            event = NavigationEvent(
                timestamp=time.time(),
                page_url=url,
                session_id=self.session_id,
                from_url=old_url,
                to_url=url,
                method="navigate",
                load_time=load_time,
                status_code=status_code,
                metadata={"wait_until": wait_until, "timeout": timeout, **kwargs},
            )
            await self.emit(event)

        except Exception as e:
            raise ActionExecutionError(
                f"Navigation failed to '{url}': {str(e)}",
                error_code=ErrorCodes.INTERACTION_FAILED,
                action_type="navigate",
                timeout=timeout,
            )

    async def hover(self, selector: str, timeout: Optional[float] = None, **kwargs: Any) -> None:
        """
        Hover over element and emit interaction event.

        Args:
            selector: CSS selector or XPath for target element
            timeout: Maximum time to wait for element
            **kwargs: Additional Playwright hover options
        """
        if not self.playwright_page:
            raise ActionExecutionError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type="hover",
                selector=selector,
            )

        if timeout is None:
            timeout = self.config.browser_config.timeout

        try:
            await self.playwright_page.hover(selector, timeout=timeout * 1000, **kwargs)

            # Emit interaction event
            event = InteractionEvent(
                timestamp=time.time(),
                page_url=self.url,
                session_id=self.session_id,
                action="hover",
                selector=selector,
                metadata={"timeout": timeout, **kwargs},
            )
            await self.emit(event)

        except Exception as e:
            raise ActionExecutionError(
                f"Hover failed on selector '{selector}': {str(e)}",
                error_code=ErrorCodes.INTERACTION_FAILED,
                action_type="hover",
                selector=selector,
                timeout=timeout,
            )

    async def wait_for_element(
        self, selector: str, state: str = "visible", timeout: Optional[float] = None, **kwargs: Any
    ) -> None:
        """
        Wait for element to reach specified state.

        Args:
            selector: CSS selector or XPath for target element
            state: Element state to wait for (visible, hidden, attached, detached)
            timeout: Maximum time to wait
            **kwargs: Additional Playwright wait options

        Raises:
            ElementError: If element doesn't reach desired state within timeout
        """
        if not self.playwright_page:
            raise ElementError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                selector=selector,
            )

        if timeout is None:
            timeout = self.config.browser_config.timeout

        try:
            await self.playwright_page.wait_for_selector(selector, state=state, timeout=timeout * 1000, **kwargs)
        except Exception as e:
            raise ElementError(
                f"Element wait failed for '{selector}' (state: {state}): {str(e)}",
                error_code=ErrorCodes.ELEMENT_NOT_FOUND,
                selector=selector,
                element_state=state,
                page_url=self.url,
            )

    async def is_element_visible(self, selector: str) -> bool:
        """
        Check if element is visible on page.

        Args:
            selector: CSS selector or XPath for element

        Returns:
            True if element is visible, False otherwise
        """
        if not self.playwright_page:
            return False

        try:
            locator = self.playwright_page.locator(selector)
            return await locator.is_visible()
        except:
            return False

    async def is_element_enabled(self, selector: str) -> bool:
        """
        Check if element is enabled for interaction.

        Args:
            selector: CSS selector or XPath for element

        Returns:
            True if element is enabled, False otherwise
        """
        if not self.playwright_page:
            return False

        try:
            locator = self.playwright_page.locator(selector)
            return await locator.is_enabled()
        except:
            return False

    async def get_element_text(self, selector: str) -> Optional[str]:
        """
        Get text content of element.

        Args:
            selector: CSS selector or XPath for element

        Returns:
            Element text content, or None if element not found
        """
        if not self.playwright_page:
            return None

        try:
            locator = self.playwright_page.locator(selector)
            return await locator.text_content()
        except:
            return None

    async def get_element_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get attribute value from element.

        Args:
            selector: CSS selector or XPath for element
            attribute: Attribute name to retrieve

        Returns:
            Attribute value, or None if element/attribute not found
        """
        if not self.playwright_page:
            return None

        try:
            locator = self.playwright_page.locator(selector)
            return await locator.get_attribute(attribute)
        except:
            return None

    def set_playwright_page(self, page: Page) -> None:
        """
        Set the underlying Playwright page instance.

        Args:
            page: Playwright Page instance to wrap
        """
        self.playwright_page = page
        # Update URL to match actual page URL
        if page.url:
            self.url = page.url

    @property
    def is_active(self) -> bool:
        """
        Check if page is still active and usable.

        Returns:
            True if page has active Playwright instance
        """
        return self.active_state and self.playwright_page is not None

    @property
    def current_url(self) -> str:
        """
        Get the current URL from the browser page.

        Returns:
            Current URL if page is active, otherwise stored URL
        """
        if self.playwright_page:
            return self.playwright_page.url
        return self.url

    async def reload(self, **kwargs: Any) -> None:
        """
        Reload the current page.

        Args:
            **kwargs: Additional Playwright reload options
        """
        if not self.playwright_page:
            raise ActionExecutionError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type="reload",
            )

        old_url = self.url
        start_time = time.time()

        try:
            response = await self.playwright_page.reload(**kwargs)
            load_time = time.time() - start_time
            status_code = response.status if response else None

            # Emit navigation event for reload
            event = NavigationEvent(
                timestamp=time.time(),
                page_url=self.url,
                session_id=self.session_id,
                from_url=old_url,
                to_url=self.url,
                method="reload",
                load_time=load_time,
                status_code=status_code,
                metadata=kwargs,
            )
            await self.emit(event)

        except Exception as e:
            raise ActionExecutionError(
                f"Page reload failed: {str(e)}", error_code=ErrorCodes.INTERACTION_FAILED, action_type="reload"
            )

    async def go_back(self, **kwargs: Any) -> None:
        """
        Navigate back in browser history.

        Args:
            **kwargs: Additional Playwright goBack options
        """
        if not self.playwright_page:
            raise ActionExecutionError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type="back",
            )

        old_url = self.url

        try:
            response = await self.playwright_page.go_back(**kwargs)
            new_url = self.playwright_page.url
            self.url = new_url

            status_code = response.status if response else None

            # Emit navigation event
            event = NavigationEvent(
                timestamp=time.time(),
                page_url=new_url,
                session_id=self.session_id,
                from_url=old_url,
                to_url=new_url,
                method="back",
                status_code=status_code,
                metadata=kwargs,
            )
            await self.emit(event)

        except Exception as e:
            raise ActionExecutionError(
                f"Go back failed: {str(e)}", error_code=ErrorCodes.INTERACTION_FAILED, action_type="back"
            )

    async def go_forward(self, **kwargs: Any) -> None:
        """
        Navigate forward in browser history.

        Args:
            **kwargs: Additional Playwright goForward options
        """
        if not self.playwright_page:
            raise ActionExecutionError(
                "Page not initialized with Playwright instance",
                error_code=ErrorCodes.SESSION_NOT_ACTIVE,
                action_type="forward",
            )

        old_url = self.url

        try:
            response = await self.playwright_page.go_forward(**kwargs)
            new_url = self.playwright_page.url
            self.url = new_url

            status_code = response.status if response else None

            # Emit navigation event
            event = NavigationEvent(
                timestamp=time.time(),
                page_url=new_url,
                session_id=self.session_id,
                from_url=old_url,
                to_url=new_url,
                method="forward",
                status_code=status_code,
                metadata=kwargs,
            )
            await self.emit(event)

        except Exception as e:
            raise ActionExecutionError(
                f"Go forward failed: {str(e)}", error_code=ErrorCodes.INTERACTION_FAILED, action_type="forward"
            )


PageBase.model_rebuild()
