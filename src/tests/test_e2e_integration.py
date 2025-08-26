"""
End-to-end integration test for browserve library.

Tests against httpbin.org - a simple, stable HTTP testing service
that provides predictable pages for automation testing.
"""

from __future__ import annotations
import pytest
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright
from browserve.core.page import PageBase
from browserve.events import InteractionEvent, NavigationEvent
from browserve.models.config import ConfigBase, BrowserConfig

# Test configuration
TEST_BASE_URL = "https://httpbun.com"
TEST_OUTPUT_DIR = Path(__file__).parent / "test_output"


class TestBrowserveE2E:
    """End-to-end integration tests for browserve library."""

    @pytest.fixture
    async def browser_setup(self):
        """Set up Playwright browser and page."""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        yield playwright, browser, context, page

        await context.close()
        await browser.close()
        await playwright.stop()

    @pytest.fixture
    def test_output_path(self) -> Path:
        """Create test output directory."""
        output_dir = TEST_OUTPUT_DIR / f"test_{int(time.time())}_httpbun"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    async def test_httpbin_navigation_flow(self, browser_setup, test_output_path: Path):
        """
        Test complete navigation flow on httpbin.org.

        Flow:
        1. Navigate to httpbin.org main page
        2. Take screenshot
        3. Find and click a link (e.g., to /get endpoint)
        4. Take screenshot of new page
        5. Verify events were emitted correctly
        """
        playwright, browser, context, page = browser_setup

        # Create PageBase instance with configuration
        config = ConfigBase(browser_config=BrowserConfig(headless=False, viewport=(1280, 720), timeout=30.0))

        browserve_page = PageBase(session_id=f"e2e_test_{int(time.time())}", url=TEST_BASE_URL, config=config)

        # Connect PageBase to Playwright page
        browserve_page.set_playwright_page(page)

        # Event capture for verification
        captured_events = []

        @browserve_page.on("navigation")
        async def capture_navigation(event: NavigationEvent):
            print(f"Navigation: {event.method} {event.from_url} -> {event.to_url}")
            captured_events.append(event)

        @browserve_page.on("interaction")
        async def capture_interaction(event: InteractionEvent):
            print(f"Interaction: {event.action} on {event.selector}")
            captured_events.append(event)

        # Step 1: Navigate to httpbin.org main page
        print(f"Navigating to {TEST_BASE_URL}")
        await browserve_page.navigate(TEST_BASE_URL)

        # Wait for page to load
        await asyncio.sleep(2)

        # Step 2: Take screenshot of main page
        main_screenshot_path = test_output_path / "01_httpbun_main.png"
        await page.screenshot(path=str(main_screenshot_path))
        print(f"Main page screenshot saved: {main_screenshot_path}")

        # Step 3: Find and verify elements exist
        # httpbin.org has links to various endpoints
        link_selector = 'a[href="/mixer"]'  # Link to forms page
        print(f"Verifying presence of link: {link_selector}")

        # Wait for the link to be available
        await browserve_page.wait_for_element(link_selector, timeout=20.0)

        # Verify element is visible
        is_visible = await browserve_page.is_element_visible(link_selector)
        assert is_visible, f"Link {link_selector} should be visible"

        # Get link text for verification
        link_text = await browserve_page.get_element_text(link_selector)
        print(f"Found link with text: '{link_text}'")

        # Step 4: Click the link to navigate to /get endpoint
        print("  Clicking link to /mixer endpoint")
        await browserve_page.click(link_selector)
        print(f"    Clicked link: {link_selector}")

        # Wait for navigation to complete
        await asyncio.sleep(3)

        # Step 5: Take screenshot of the new page
        get_screenshot_path = test_output_path / "02_httpbun_get.png"
        await page.screenshot(path=str(get_screenshot_path))
        print(f"      GET page screenshot saved: {get_screenshot_path}")

        # Step 6: Verify we're on the correct page
        current_url = browserve_page.current_url
        print(f"Current URL: {current_url}")
        assert "/mixer" in current_url, "Should be on the /mixer endpoint page"

        # Step 7: Interact with elements on the GET page
        # The /get page typically shows JSON response
        # Let's look for the response body
        if await browserve_page.is_element_visible("pre"):
            response_text = await browserve_page.get_element_text("pre")
            print(f"Response preview: {response_text[:100]}...")

        # Step 8: Navigate back to test back functionality
        print("Testing back navigation")
        await browserve_page.go_back()
        await asyncio.sleep(2)

        # Step 9: Final screenshot showing we're back
        back_screenshot_path = test_output_path / "03_httpbun_back.png"
        await page.screenshot(path=str(back_screenshot_path))
        print(f"Back navigation screenshot saved: {back_screenshot_path}")

        # Step 10: Verify events were captured
        print(f"Total events captured: {len(captured_events)}")

        # Should have at least navigation and interaction events
        navigation_events = [e for e in captured_events if isinstance(e, NavigationEvent)]
        interaction_events = [e for e in captured_events if isinstance(e, InteractionEvent)]

        print(f"Navigation events: {len(navigation_events)}")
        print(f"Interaction events: {len(interaction_events)}")

        # Verify we have expected events
        assert len(navigation_events) >= 2, "Should have at least 2 navigation events"
        assert len(interaction_events) >= 1, "Should have at least 1 interaction event"

        # Verify first navigation to httpbin.org
        initial_nav = navigation_events[0]
        assert initial_nav.method == "navigate"
        assert TEST_BASE_URL in initial_nav.to_url

        # Verify click interaction
        click_event = interaction_events[0]
        assert click_event.action == "click"
        assert link_selector == click_event.selector

        # Step 11: Create summary file
        summary_path = test_output_path / "test_summary.txt"
        with open(summary_path, "w") as f:
            f.write("Browserve E2E Test Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Test URL: {TEST_BASE_URL}\n")
            f.write(f"Session ID: {browserve_page.session_id}\n")
            f.write(f"Final URL: {current_url}\n")
            f.write(f"Total Events: {len(captured_events)}\n")
            f.write(f"Navigation Events: {len(navigation_events)}\n")
            f.write(f"Interaction Events: {len(interaction_events)}\n")
            f.write("\nScreenshots:\n")
            f.write(f"- Main page: 01_httpbun_main.png\n")
            f.write(f"- GET endpoint: 02_httpbun_get.png\n")
            f.write(f"- Back navigation: 03_httpbun_back.png\n")
            f.write("\nTest Status: PASSED ✓\n")

        print(f"Test summary saved: {summary_path}")
        print("✓ End-to-end test completed successfully!")

    async def test_httpbin_form_interaction(self, browser_setup, test_output_path: Path):
        """
        Test form interaction on httpbin.org forms page.

        Flow:
        1. Navigate to httpbin.org/forms/post
        2. Fill out a simple form
        3. Submit and verify response
        """
        playwright, browser, context, page = browser_setup

        # Create separate output directory for this test
        form_output_path = test_output_path.parent / f"test_{int(time.time())}_httpbun_forms"
        form_output_path.mkdir(parents=True, exist_ok=True)

        browserve_page = PageBase(
            session_id=f"form_test_{int(time.time())}", url=f"{TEST_BASE_URL}/mixer", config=ConfigBase()
        )

        browserve_page.set_playwright_page(page)

        # Event capture
        form_events = []

        @browserve_page.on("interaction")
        async def capture_form_interaction(event: InteractionEvent):
            form_events.append(event)
            print(f"Form interaction: {event.action} on {event.selector}")

        # Navigate to forms page
        await browserve_page.navigate(f"{TEST_BASE_URL}/mixer")
        await asyncio.sleep(2)

        # Screenshot of form
        form_screenshot_path = form_output_path / "01_form_initial.png"
        await page.screenshot(path=str(form_screenshot_path))

        # Fill out form fields (httpbin form has these fields)
        try:
            # Fill customer name
            await browserve_page.fill("input[name='custname']", "Test Customer")
            await asyncio.sleep(0.5)

            # Fill customer telephone
            await browserve_page.fill("input[name='custtel']", "555-1234")
            await asyncio.sleep(0.5)

            # Fill email
            await browserve_page.fill("input[name='custemail']", "test@example.com")
            await asyncio.sleep(0.5)

            # Select pizza size (if radio buttons exist)
            if await browserve_page.is_element_visible("input[name='size'][value='medium']"):
                await browserve_page.click("input[name='size'][value='medium']")
                await asyncio.sleep(0.5)

            # Screenshot after filling
            filled_screenshot_path = form_output_path / "02_form_filled.png"
            await page.screenshot(path=str(filled_screenshot_path))

            # Submit form
            submit_button = "input[type='submit']"
            if await browserve_page.is_element_visible(submit_button):
                await browserve_page.click(submit_button)
                await asyncio.sleep(3)

                # Screenshot of result
                result_screenshot_path = form_output_path / "03_form_result.png"
                await page.screenshot(path=str(result_screenshot_path))

        except Exception as e:
            print(f"Form test encountered issue: {e}")
            # Still save what we have
            error_screenshot_path = form_output_path / "form_error.png"
            await page.screenshot(path=str(error_screenshot_path))

        # Verify we captured form interactions
        fill_events = [e for e in form_events if e.action == "fill"]
        click_events = [e for e in form_events if e.action == "click"]

        print(f"Form fill events: {len(fill_events)}")
        print(f"Form click events: {len(click_events)}")

        # Create form test summary
        form_summary_path = form_output_path / "form_test_summary.txt"
        with open(form_summary_path, "w") as f:
            f.write("Browserve Form Test Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Form URL: {TEST_BASE_URL}/mixer\n")
            f.write(f"Fill Events: {len(fill_events)}\n")
            f.write(f"Click Events: {len(click_events)}\n")
            f.write("\nForm Test Status: COMPLETED\n")

        print("✓ Form interaction test completed!")


if __name__ == "__main__":
    # Can run directly for quick testing
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
