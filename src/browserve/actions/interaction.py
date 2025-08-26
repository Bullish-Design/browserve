"""
Concrete browser interaction actions for common automation tasks.

Provides ClickAction, FillAction, NavigationAction and other concrete
implementations of PlaywrightAction for typical browser interactions.
"""

from __future__ import annotations
from pydantic import Field, field_validator
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Union
import asyncio

from .base import PlaywrightAction
from ..models.results import ActionResult
from ..exceptions import ActionExecutionError, ElementError, ValidationError
from ..utils.validation import validate_selector, validate_url

if TYPE_CHECKING:
    from ..core.page import PageBase


class ClickAction(PlaywrightAction):
    """
    Click an element on the page.

    Performs mouse click interaction on a specified element using
    CSS selector or XPath. Supports different mouse buttons,
    keyboard modifiers, and position offsets.

    Example:
        >>> action = ClickAction(
        ...     selector="#submit-button",
        ...     button="left",
        ...     modifiers=["Shift"]
        ... )
        >>> result = await action.execute_with_hooks(page)
    """

    selector: str = Field(description="CSS selector or XPath for element to click")
    button: str = Field("left", description="Mouse button to click (left, right, middle)")
    modifiers: List[str] = Field(default_factory=list, description="Keyboard modifiers (Shift, Control, Alt, Meta)")
    position: Optional[Dict[str, float]] = Field(None, description="Click position offset {x: float, y: float}")
    click_count: int = Field(1, ge=1, le=10, description="Number of clicks to perform")
    force: bool = Field(False, description="Force click even if element not actionable")
    action_type: str = "click"

    @field_validator("selector")
    @classmethod
    def validate_selector_format(cls, v: str) -> str:
        """Validate selector is properly formatted."""
        if not validate_selector(v):
            raise ValueError(f"Invalid selector format: {v}")
        return v.strip()

    @field_validator("button")
    @classmethod
    def validate_button_type(cls, v: str) -> str:
        """Validate mouse button type."""
        valid_buttons = {"left", "right", "middle"}
        if v.lower() not in valid_buttons:
            raise ValueError(f"Invalid button '{v}'. Must be one of: {valid_buttons}")
        return v.lower()

    @field_validator("modifiers")
    @classmethod
    def validate_modifiers(cls, v: List[str]) -> List[str]:
        """Validate keyboard modifiers."""
        valid_modifiers = {"Shift", "Control", "Alt", "Meta"}
        for modifier in v:
            if modifier not in valid_modifiers:
                raise ValueError(f"Invalid modifier '{modifier}'. Must be one of: {valid_modifiers}")
        return v

    async def pre_execute(self, page: PageBase) -> None:
        """Validate element exists and is clickable before clicking."""
        await super().pre_execute(page)

        # Check if element is visible
        if not await page.is_element_visible(self.selector):
            raise ElementError(
                f"Element not visible: {self.selector}", selector=self.selector, page_url=page.current_url
            )

    async def execute(self, page: PageBase) -> ActionResult:
        """Execute click action on the specified element."""
        try:
            # Prepare click options
            click_options = {
                "button": self.button,
                "timeout": self.timeout * 1000,  # Convert to milliseconds
                "force": self.force,
            }

            if self.modifiers:
                click_options["modifiers"] = self.modifiers

            if self.position:
                click_options["position"] = self.position

            if self.click_count > 1:
                click_options["click_count"] = self.click_count

            # Perform the click
            await page.click(self.selector, **click_options)

            return ActionResult.success_result(
                data={
                    "selector": self.selector,
                    "button": self.button,
                    "click_count": self.click_count,
                    "position": self.position,
                },
                action_type=self.action_type,
            ).add_metadata(modifiers=self.modifiers, forced=self.force)

        except Exception as e:
            return ActionResult.failure_result(
                error=f"Click failed on '{self.selector}': {str(e)}", action_type=self.action_type
            ).add_metadata(selector=self.selector, button=self.button)


class FillAction(PlaywrightAction):
    """
    Fill a form field with text.

    Enters text into input fields, textareas, or other fillable elements.
    Supports clearing existing content before filling and validation.

    Example:
        >>> action = FillAction(
        ...     selector="input[name='username']",
        ...     value="testuser",
        ...     clear_first=True
        ... )
    """

    selector: str = Field(description="CSS selector or XPath for form field")
    value: str = Field(description="Text value to enter into field")
    clear_first: bool = Field(True, description="Clear existing content before filling")
    verify_fill: bool = Field(True, description="Verify text was actually filled")
    action_type: str = "fill"

    @field_validator("selector")
    @classmethod
    def validate_selector_format(cls, v: str) -> str:
        """Validate selector format."""
        if not validate_selector(v):
            raise ValueError(f"Invalid selector format: {v}")
        return v.strip()

    async def pre_execute(self, page: PageBase) -> None:
        """Validate element exists and is fillable."""
        await super().pre_execute(page)

        # Check element is visible and enabled
        if not await page.is_element_visible(self.selector):
            raise ElementError(f"Element not visible: {self.selector}", selector=self.selector)

        if not await page.is_element_enabled(self.selector):
            raise ElementError(f"Element not enabled: {self.selector}", selector=self.selector)

    async def execute(self, page: PageBase) -> ActionResult:
        """Execute fill action on the form field."""
        try:
            original_value = None

            # Get original value if verification requested
            if self.verify_fill:
                original_value = await page.get_element_attribute(self.selector, "value")

            # Clear field if requested
            if self.clear_first and page.playwright_page:
                await page.playwright_page.fill(self.selector, "")

            # Fill with new value
            await page.fill(self.selector, self.value, timeout=self.timeout)

            # Verify fill if requested
            filled_value = None
            if self.verify_fill:
                filled_value = await page.get_element_attribute(self.selector, "value")
                if filled_value != self.value:
                    return ActionResult.failure_result(
                        error=f"Fill verification failed. Expected '{self.value}', got '{filled_value}'",
                        action_type=self.action_type,
                    ).add_metadata(selector=self.selector, expected_value=self.value, actual_value=filled_value)

            return ActionResult.success_result(
                data={
                    "selector": self.selector,
                    "value": self.value,
                    "original_value": original_value,
                    "verified": self.verify_fill,
                },
                action_type=self.action_type,
            ).add_metadata(cleared_first=self.clear_first, final_value=filled_value)

        except Exception as e:
            return ActionResult.failure_result(
                error=f"Fill failed on '{self.selector}': {str(e)}", action_type=self.action_type
            ).add_metadata(selector=self.selector, value=self.value)


class NavigationAction(PlaywrightAction):
    """
    Navigate to a specific URL.

    Performs page navigation with configurable wait conditions
    and validation of successful navigation.

    Example:
        >>> action = NavigationAction(
        ...     url="https://example.com/login",
        ...     wait_until="networkidle"
        ... )
    """

    url: str = Field(description="Target URL to navigate to")
    wait_until: str = Field("load", description="When to consider navigation complete")
    expected_url_pattern: Optional[str] = Field(None, description="Regex pattern the final URL should match")
    verify_navigation: bool = Field(True, description="Verify navigation was successful")
    action_type: str = "navigate"

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        """Validate URL format."""
        if not validate_url(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v.strip()

    @field_validator("wait_until")
    @classmethod
    def validate_wait_condition(cls, v: str) -> str:
        """Validate wait condition."""
        valid_conditions = {"load", "domcontentloaded", "networkidle", "commit"}
        if v not in valid_conditions:
            raise ValueError(f"Invalid wait_until '{v}'. Must be one of: {valid_conditions}")
        return v

    async def execute(self, page: PageBase) -> ActionResult:
        """Execute navigation to the specified URL."""
        try:
            original_url = page.current_url

            # Perform navigation
            await page.navigate(self.url, wait_until=self.wait_until, timeout=self.timeout)

            final_url = page.current_url

            # Verify navigation if requested
            if self.verify_navigation:
                if self.expected_url_pattern:
                    import re

                    if not re.search(self.expected_url_pattern, final_url):
                        return ActionResult.failure_result(
                            error=f"Navigation verification failed. "
                            f"URL '{final_url}' doesn't match pattern '{self.expected_url_pattern}'",
                            action_type=self.action_type,
                        ).add_metadata(target_url=self.url, final_url=final_url, pattern=self.expected_url_pattern)
                elif not final_url.startswith(self.url.split("?")[0]):
                    # Basic check that we're at least on the right domain/path
                    return ActionResult.failure_result(
                        error=f"Navigation verification failed. Expected to be at '{self.url}', but at '{final_url}'",
                        action_type=self.action_type,
                    ).add_metadata(target_url=self.url, final_url=final_url)

            return ActionResult.success_result(
                data={
                    "target_url": self.url,
                    "original_url": original_url,
                    "final_url": final_url,
                    "wait_until": self.wait_until,
                },
                action_type=self.action_type,
            ).add_metadata(verified=self.verify_navigation, url_changed=original_url != final_url)

        except Exception as e:
            return ActionResult.failure_result(
                error=f"Navigation failed to '{self.url}': {str(e)}", action_type=self.action_type
            ).add_metadata(target_url=self.url)


class WaitAction(PlaywrightAction):
    """
    Wait for an element or condition.

    Waits for elements to appear, disappear, or reach certain states.
    Useful for handling dynamic content and timing-dependent interactions.

    Example:
        >>> action = WaitAction(
        ...     selector="#loading",
        ...     state="hidden",
        ...     timeout=10.0
        ... )
    """

    selector: Optional[str] = Field(None, description="Element selector to wait for")
    state: str = Field("visible", description="Element state to wait for")
    wait_time: Optional[float] = Field(None, description="Fixed time to wait in seconds")
    condition_text: Optional[str] = Field(None, description="Text content to wait for in element")
    action_type: str = "wait"

    @field_validator("state")
    @classmethod
    def validate_wait_state(cls, v: str) -> str:
        """Validate wait state."""
        valid_states = {"visible", "hidden", "attached", "detached"}
        if v not in valid_states:
            raise ValueError(f"Invalid state '{v}'. Must be one of: {valid_states}")
        return v

    async def execute(self, page: PageBase) -> ActionResult:
        """Execute wait action."""
        try:
            if self.wait_time is not None:
                # Simple time-based wait
                await asyncio.sleep(self.wait_time)
                return ActionResult.success_result(data={"wait_time": self.wait_time}, action_type=self.action_type)

            elif self.selector:
                # Element-based wait
                await page.wait_for_element(self.selector, state=self.state, timeout=self.timeout)

                # Check for specific text if requested
                if self.condition_text and self.state in ("visible", "attached"):
                    element_text = await page.get_element_text(self.selector)
                    if self.condition_text not in (element_text or ""):
                        return ActionResult.failure_result(
                            error=f"Element text condition not met. "
                            f"Expected '{self.condition_text}' in '{element_text}'",
                            action_type=self.action_type,
                        )

                return ActionResult.success_result(
                    data={"selector": self.selector, "state": self.state, "condition_text": self.condition_text},
                    action_type=self.action_type,
                )
            else:
                return ActionResult.failure_result(
                    error="Must specify either wait_time or selector", action_type=self.action_type
                )

        except Exception as e:
            return ActionResult.failure_result(
                error=f"Wait failed: {str(e)}", action_type=self.action_type
            ).add_metadata(selector=self.selector, state=self.state, wait_time=self.wait_time)


class HoverAction(PlaywrightAction):
    """
    Hover over an element.

    Moves mouse cursor over an element to trigger hover states,
    dropdown menus, or tooltips.

    Example:
        >>> action = HoverAction(
        ...     selector=".menu-item",
        ...     position={"x": 10, "y": 5}
        ... )
    """

    selector: str = Field(description="CSS selector or XPath for element to hover")
    position: Optional[Dict[str, float]] = Field(None, description="Hover position offset {x: float, y: float}")
    force: bool = Field(False, description="Force hover even if element not actionable")
    action_type: str = "hover"

    @field_validator("selector")
    @classmethod
    def validate_selector_format(cls, v: str) -> str:
        """Validate selector format."""
        if not validate_selector(v):
            raise ValueError(f"Invalid selector format: {v}")
        return v.strip()

    async def pre_execute(self, page: PageBase) -> None:
        """Validate element is visible for hovering."""
        await super().pre_execute(page)

        if not await page.is_element_visible(self.selector):
            raise ElementError(f"Element not visible for hover: {self.selector}", selector=self.selector)

    async def execute(self, page: PageBase) -> ActionResult:
        """Execute hover action."""
        try:
            hover_options = {"timeout": self.timeout * 1000}

            if self.position:
                hover_options["position"] = self.position
            if self.force:
                hover_options["force"] = self.force

            await page.hover(self.selector, **hover_options)

            return ActionResult.success_result(
                data={"selector": self.selector, "position": self.position}, action_type=self.action_type
            ).add_metadata(forced=self.force)

        except Exception as e:
            return ActionResult.failure_result(
                error=f"Hover failed on '{self.selector}': {str(e)}", action_type=self.action_type
            ).add_metadata(selector=self.selector)


class ScrollAction(PlaywrightAction):
    """
    Scroll the page or an element.

    Performs scrolling to bring elements into view or navigate
    through content.
    """

    selector: Optional[str] = Field(None, description="Element to scroll (None for page scroll)")
    direction: str = Field("down", description="Scroll direction (up, down, left, right)")
    pixels: Optional[int] = Field(None, description="Pixels to scroll (None for page/element height)")
    to_element: Optional[str] = Field(None, description="Scroll until this element is visible")
    action_type: str = "scroll"

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate scroll direction."""
        valid_directions = {"up", "down", "left", "right"}
        if v not in valid_directions:
            raise ValueError(f"Invalid direction '{v}'. Must be one of: {valid_directions}")
        return v

    async def execute(self, page: PageBase) -> ActionResult:
        """Execute scroll action."""
        try:
            if self.to_element:
                # Scroll to make element visible
                if not page.playwright_page:
                    return ActionResult.failure_result(
                        error="Playwright page not available", action_type=self.action_type
                    )

                await page.playwright_page.locator(self.to_element).scroll_into_view_if_needed()

                return ActionResult.success_result(data={"to_element": self.to_element}, action_type=self.action_type)

            # Directional scroll
            if not page.playwright_page:
                return ActionResult.failure_result(error="Playwright page not available", action_type=self.action_type)

            # Calculate scroll delta
            delta_x = 0
            delta_y = 0
            pixels = self.pixels or 300  # Default scroll distance

            if self.direction == "down":
                delta_y = pixels
            elif self.direction == "up":
                delta_y = -pixels
            elif self.direction == "right":
                delta_x = pixels
            elif self.direction == "left":
                delta_x = -pixels

            if self.selector:
                # Scroll specific element
                await page.playwright_page.locator(self.selector).scroll_into_view_if_needed()
            else:
                # Scroll page
                await page.playwright_page.mouse.wheel(delta_x, delta_y)

            return ActionResult.success_result(
                data={"direction": self.direction, "pixels": pixels, "selector": self.selector},
                action_type=self.action_type,
            ).add_metadata(delta_x=delta_x, delta_y=delta_y)

        except Exception as e:
            return ActionResult.failure_result(
                error=f"Scroll failed: {str(e)}", action_type=self.action_type
            ).add_metadata(direction=self.direction, selector=self.selector, to_element=self.to_element)
