"""
Test suite for Browserve event system.
"""

from __future__ import annotations
import pytest
import asyncio
import time
import logging
from unittest.mock import AsyncMock
from pydantic import ValidationError as PydanticValidationError
from browserve.events import (
    EventBase,
    InteractionEvent,
    NavigationEvent,
    NetworkEvent,
    DOMChangeEvent,
    EVENT_TYPES,
    create_event,
    EventHandler,
    EventEmitter,
    EventFilter,
    FilterChain,
    create_domain_filter,
    create_action_filter,
    create_selector_filter,
    create_event_type_filter,
    create_exclusion_filter,
    create_network_filter,
    create_time_range_filter,
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEventBase:
    """Test EventBase model validation and functionality."""

    def test_valid_event_creation(self) -> None:
        """Test creating valid EventBase instance."""
        logger.info("Testing valid EventBase creation")
        event = EventBase(event_type="test_event", page_url="https://example.com", session_id="session-123")
        logger.info(f"Created event: {event}")
        assert event.event_type == "test_event"
        assert event.page_url == "https://example.com"
        assert event.session_id == "session-123"
        assert isinstance(event.timestamp, float)
        assert event.metadata == {}
        logger.info("✓ Valid event creation test passed")

    def test_automatic_timestamp(self) -> None:
        """Test timestamp is automatically generated."""
        logger.info("Testing automatic timestamp generation")
        before = time.time()
        event = EventBase(event_type="test", page_url="https://example.com", session_id="session-123")
        after = time.time()
        logger.info(f"Event timestamp: {event.timestamp}")
        logger.info(f"Time range: {before} - {after}")

        assert before <= event.timestamp <= after
        logger.info("✓ Automatic timestamp test passed")

    def test_custom_timestamp(self) -> None:
        """Test custom timestamp can be provided."""
        logger.info("Testing custom timestamp")
        custom_time = 1234567890.0
        event = EventBase(
            event_type="test", page_url="https://example.com", session_id="session-123", timestamp=custom_time
        )
        logger.info(f"Event with custom timestamp: {event}")
        assert event.timestamp == custom_time
        logger.info("✓ Custom timestamp test passed")

    def test_custom_metadata(self) -> None:
        """Test custom metadata can be added."""
        logger.info("Testing custom metadata")
        metadata = {"key1": "value1", "key2": 42}
        event = EventBase(
            event_type="test", page_url="https://example.com", session_id="session-123", metadata=metadata
        )
        logger.info(f"Event with metadata: {event}")
        assert event.metadata == metadata
        logger.info("✓ Custom metadata test passed")

    def test_empty_event_type_validation(self) -> None:
        """Test event_type cannot be empty."""
        logger.info("Testing empty event_type validation")
        with pytest.raises(PydanticValidationError):
            EventBase(event_type="", page_url="https://example.com", session_id="session-123")

        with pytest.raises(PydanticValidationError):
            EventBase(event_type="   ", page_url="https://example.com", session_id="session-123")
        logger.info("✓ Empty event_type validation test passed")

    def test_invalid_url_validation(self) -> None:
        """Test page_url validation."""
        logger.info("Testing invalid URL validation")
        # Empty URL
        with pytest.raises(PydanticValidationError):
            EventBase(event_type="test", page_url="", session_id="session-123")

        # Invalid URL format
        with pytest.raises(PydanticValidationError):
            EventBase(event_type="test", page_url="not-a-url", session_id="session-123")
        logger.info("✓ Invalid URL validation test passed")

    def test_empty_session_id_validation(self) -> None:
        """Test session_id cannot be empty."""
        logger.info("Testing empty session_id validation")
        with pytest.raises(PydanticValidationError):
            EventBase(event_type="test", page_url="https://example.com", session_id="")
        logger.info("✓ Empty session_id validation test passed")


class TestInteractionEvent:
    """Test InteractionEvent specific functionality."""

    def test_valid_interaction_creation(self) -> None:
        """Test creating valid InteractionEvent."""
        logger.info("Testing valid InteractionEvent creation")
        event = InteractionEvent(
            action="click", selector="#button", page_url="https://example.com", session_id="session-123"
        )
        logger.info(f"Created interaction event: {event}")
        assert event.event_type == "interaction"
        assert event.action == "click"
        assert event.selector == "#button"
        assert event.value is None
        assert event.element_text is None
        logger.info("✓ Valid interaction creation test passed")

    def test_interaction_with_value(self) -> None:
        """Test interaction with input value."""
        logger.info("Testing interaction with value")
        event = InteractionEvent(
            action="fill",
            selector="input[name='username']",
            value="testuser",
            element_text="Username",
            element_tag="input",
            page_url="https://example.com",
            session_id="session-123",
        )
        logger.info(f"Created interaction event with value: {event}")
        assert event.action == "fill"
        assert event.value == "testuser"
        assert event.element_text == "Username"
        assert event.element_tag == "input"
        logger.info("✓ Interaction with value test passed")

    def test_action_validation(self) -> None:
        """Test action type validation."""
        logger.info("Testing action type validation")
        # Valid actions
        valid_actions = ["click", "fill", "hover", "scroll"]
        for action in valid_actions:
            logger.info(f"Testing valid action: {action}")
            event = InteractionEvent(
                action=action, selector="#test", page_url="https://example.com", session_id="session-123"
            )
            assert event.action == action

        # Invalid action
        with pytest.raises(PydanticValidationError):
            logger.info("Testing invalid action")
            InteractionEvent(
                action="invalid_action", selector="#test", page_url="https://example.com", session_id="session-123"
            )
        logger.info("✓ Action validation test passed")

    def test_empty_selector_validation(self) -> None:
        """Test selector cannot be empty."""
        logger.info("Testing empty selector validation")
        with pytest.raises(PydanticValidationError):
            InteractionEvent(action="click", selector="", page_url="https://example.com", session_id="session-123")
        logger.info("✓ Empty selector validation test passed")


class TestNavigationEvent:
    """Test NavigationEvent specific functionality."""

    def test_valid_navigation_creation(self) -> None:
        """Test creating valid NavigationEvent."""
        logger.info("Testing valid NavigationEvent creation")
        event = NavigationEvent(
            from_url="https://example.com/page1",
            to_url="https://example.com/page2",
            page_url="https://example.com/page2",
            session_id="session-123",
        )
        logger.info(f"Created navigation event: {event}")
        assert event.event_type == "navigation"
        assert event.from_url == "https://example.com/page1"
        assert event.to_url == "https://example.com/page2"
        assert event.method == "navigate"
        assert event.load_time is None
        logger.info("✓ Valid navigation creation test passed")

    def test_navigation_with_timing(self) -> None:
        """Test navigation with load time and status."""
        logger.info("Testing navigation with timing")
        event = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/login",
            method="navigate",
            load_time=1.5,
            status_code=200,
            page_url="https://example.com/login",
            session_id="session-123",
        )
        logger.info(f"Created navigation event with timing: {event}")
        assert event.load_time == 1.5
        assert event.status_code == 200
        logger.info("✓ Navigation with timing test passed")

    def test_method_validation(self) -> None:
        """Test navigation method validation."""
        logger.info("Testing navigation method validation")
        valid_methods = ["navigate", "reload", "back", "forward"]
        for method in valid_methods:
            logger.info(f"Testing valid method: {method}")
            event = NavigationEvent(
                from_url="https://example.com",
                to_url="https://example.com/page",
                method=method,
                page_url="https://example.com/page",
                session_id="session-123",
            )
            assert event.method == method

        # Invalid method
        with pytest.raises(PydanticValidationError):
            logger.info("Testing invalid method")
            NavigationEvent(
                from_url="https://example.com",
                to_url="https://example.com/page",
                method="invalid_method",
                page_url="https://example.com/page",
                session_id="session-123",
            )
        logger.info("✓ Method validation test passed")


class TestNetworkEvent:
    """Test NetworkEvent specific functionality."""

    def test_valid_network_creation(self) -> None:
        """Test creating valid NetworkEvent."""
        logger.info("Testing valid NetworkEvent creation")
        event = NetworkEvent(
            request_url="https://api.example.com/data",
            method="GET",
            page_url="https://example.com",
            session_id="session-123",
        )
        logger.info(f"Created network event: {event}")
        assert event.event_type == "network_request"
        assert event.request_url == "https://api.example.com/data"
        assert event.method == "GET"
        assert event.status_code is None
        logger.info("✓ Valid network creation test passed")

    def test_network_with_response_data(self) -> None:
        """Test network event with response information."""
        logger.info("Testing network event with response data")
        event = NetworkEvent(
            request_url="https://api.example.com/data",
            method="POST",
            status_code=201,
            response_size=1024,
            request_headers={"Content-Type": "application/json"},
            response_headers={"Server": "nginx"},
            duration=0.25,
            page_url="https://example.com",
            session_id="session-123",
        )
        logger.info(f"Created network event with response data: {event}")
        assert event.status_code == 201
        assert event.response_size == 1024
        assert event.request_headers["Content-Type"] == "application/json"
        assert event.duration == 0.25
        logger.info("✓ Network with response data test passed")

    def test_http_method_validation(self) -> None:
        """Test HTTP method validation."""
        logger.info("Testing HTTP method validation")
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        for method in valid_methods:
            logger.info(f"Testing valid HTTP method: {method}")
            event = NetworkEvent(
                request_url="https://example.com",
                method=method,
                page_url="https://example.com",
                session_id="session-123",
            )
            assert event.method == method

        # Invalid method
        with pytest.raises(PydanticValidationError):
            logger.info("Testing invalid HTTP method")
            NetworkEvent(
                request_url="https://example.com",
                method="INVALID",
                page_url="https://example.com",
                session_id="session-123",
            )
        logger.info("✓ HTTP method validation test passed")


class TestDOMChangeEvent:
    """Test DOMChangeEvent specific functionality."""

    def test_valid_dom_change_creation(self) -> None:
        """Test creating valid DOMChangeEvent."""
        logger.info("Testing valid DOMChangeEvent creation")
        event = DOMChangeEvent(
            change_type="added", selector=".new-element", page_url="https://example.com", session_id="session-123"
        )
        logger.info(f"Created DOM change event: {event}")
        assert event.event_type == "dom_change"
        assert event.change_type == "added"
        assert event.selector == ".new-element"
        logger.info("✓ Valid DOM change creation test passed")

    def test_dom_change_with_values(self) -> None:
        """Test DOM change with old/new values."""
        logger.info("Testing DOM change with values")
        event = DOMChangeEvent(
            change_type="modified",
            selector="#content",
            old_value="Old Text",
            new_value="New Text",
            element_tag="div",
            page_url="https://example.com",
            session_id="session-123",
        )
        logger.info(f"Created DOM change event with values: {event}")
        assert event.old_value == "Old Text"
        assert event.new_value == "New Text"
        assert event.element_tag == "div"
        logger.info("✓ DOM change with values test passed")

    def test_attribute_change(self) -> None:
        """Test attribute change event."""
        logger.info("Testing attribute change event")
        event = DOMChangeEvent(
            change_type="attribute",
            selector="#element",
            attribute_name="class",
            old_value="old-class",
            new_value="new-class",
            page_url="https://example.com",
            session_id="session-123",
        )
        logger.info(f"Created attribute change event: {event}")
        assert event.change_type == "attribute"
        assert event.attribute_name == "class"
        logger.info("✓ Attribute change test passed")

    def test_change_type_validation(self) -> None:
        """Test change type validation."""
        logger.info("Testing change type validation")
        valid_types = ["added", "removed", "modified", "attribute"]
        for change_type in valid_types:
            logger.info(f"Testing valid change type: {change_type}")
            event = DOMChangeEvent(
                change_type=change_type, selector="#test", page_url="https://example.com", session_id="session-123"
            )
            assert event.change_type == change_type

        # Invalid type
        with pytest.raises(PydanticValidationError):
            logger.info("Testing invalid change type")
            DOMChangeEvent(
                change_type="invalid_type", selector="#test", page_url="https://example.com", session_id="session-123"
            )
        logger.info("✓ Change type validation test passed")


class TestEventFactory:
    """Test event factory functionality."""

    def test_create_event_by_type(self) -> None:
        """Test creating events using factory function."""
        logger.info("Testing event creation by type")
        # Create interaction event
        event = create_event(
            "interaction", action="click", selector="#button", page_url="https://example.com", session_id="session-123"
        )
        logger.info(f"Created interaction event: {event}")
        assert isinstance(event, InteractionEvent)
        assert event.action == "click"

        # Create navigation event
        event = create_event(
            "navigation",
            from_url="https://example.com",
            to_url="https://example.com/page",
            page_url="https://example.com/page",
            session_id="session-123",
        )
        logger.info(f"Created navigation event: {event}")
        assert isinstance(event, NavigationEvent)
        logger.info("✓ Event creation by type test passed")

    def test_create_event_invalid_type(self) -> None:
        """Test factory with invalid event type."""
        logger.info("Testing event creation with invalid type")
        with pytest.raises(ValueError, match="Unknown event type"):
            create_event("invalid_type")
        logger.info("✓ Invalid event type test passed")

    def test_event_types_registry(self) -> None:
        """Test EVENT_TYPES registry completeness."""
        logger.info("Testing EVENT_TYPES registry")
        expected_types = {"interaction", "navigation", "network_request", "dom_change"}
        assert set(EVENT_TYPES.keys()) == expected_types
        logger.info("✓ Event types registry test passed")


class TestEventEmitter:
    """Test EventEmitter functionality."""

    @pytest.fixture
    def emitter(self) -> EventEmitter:
        """Create EventEmitter instance for testing."""
        logger.info("Creating EventEmitter fixture")
        return EventEmitter()

    @pytest.fixture
    def sample_event(self) -> InteractionEvent:
        """Create sample event for testing."""
        logger.info("Creating sample event fixture")
        return InteractionEvent(
            action="click", selector="#button", page_url="https://example.com", session_id="session-123"
        )

    async def test_handler_subscription(self, emitter: EventEmitter) -> None:
        """Test event handler subscription."""
        logger.info("Testing handler subscription")
        handler_called = False
        received_event = None

        async def test_handler(event: EventBase) -> None:
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event

        emitter.subscribe("interaction", test_handler)
        logger.info(f"Handler count for 'interaction': {emitter.get_handler_count('interaction')}")
        assert emitter.get_handler_count("interaction") == 1
        logger.info("✓ Handler subscription test passed")

    async def test_event_emission(self, emitter: EventEmitter, sample_event: InteractionEvent) -> None:
        """Test event emission to handlers."""
        logger.info("Testing event emission")
        handler_called = False
        received_event = None

        async def test_handler(event: EventBase) -> None:
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event

        emitter.subscribe("interaction", test_handler)
        result = await emitter.emit(sample_event)
        logger.info(f"Emission result: {result}")

        assert handler_called
        assert received_event == sample_event
        assert result["handlers_called"] == 1
        assert result["handlers_succeeded"] == 1
        assert result["handlers_failed"] == 0
        logger.info("✓ Event emission test passed")

    async def test_multiple_handlers(self, emitter: EventEmitter, sample_event: InteractionEvent) -> None:
        """Test multiple handlers for same event type."""
        logger.info("Testing multiple handlers")
        call_count = 0

        async def handler1(event: EventBase) -> None:
            nonlocal call_count
            call_count += 1

        async def handler2(event: EventBase) -> None:
            nonlocal call_count
            call_count += 1

        emitter.subscribe("interaction", handler1)
        emitter.subscribe("interaction", handler2)

        await emitter.emit(sample_event)
        logger.info(f"Total handler calls: {call_count}")
        assert call_count == 2
        logger.info("✓ Multiple handlers test passed")

    async def test_handler_error_isolation(self, emitter: EventEmitter, sample_event: InteractionEvent) -> None:
        """Test handler errors don't break emission."""
        logger.info("Testing handler error isolation")
        good_handler_called = False

        async def failing_handler(event: EventBase) -> None:
            raise ValueError("Handler error")

        async def good_handler(event: EventBase) -> None:
            nonlocal good_handler_called
            good_handler_called = True

        emitter.subscribe("interaction", failing_handler)
        emitter.subscribe("interaction", good_handler)

        result = await emitter.emit(sample_event)
        logger.info(f"Emission result with errors: {result}")

        # Good handler should still be called
        assert good_handler_called
        assert result["handlers_succeeded"] == 1
        assert result["handlers_failed"] == 1
        assert len(result["errors"]) == 1
        logger.info("✓ Handler error isolation test passed")

    def test_decorator_subscription(self, emitter: EventEmitter) -> None:
        """Test decorator-based handler registration."""
        logger.info("Testing decorator subscription")

        @emitter.on("interaction")
        async def decorated_handler(event: EventBase) -> None:
            pass

        logger.info(f"Handler count after decorator: {emitter.get_handler_count('interaction')}")
        assert emitter.get_handler_count("interaction") == 1
        assert "interaction" in emitter.get_event_types()
        logger.info("✓ Decorator subscription test passed")

    def test_handler_unsubscription(self, emitter: EventEmitter) -> None:
        """Test handler unsubscription."""
        logger.info("Testing handler unsubscription")

        async def test_handler(event: EventBase) -> None:
            pass

        emitter.subscribe("interaction", test_handler)
        logger.info(f"Handler count after subscription: {emitter.get_handler_count('interaction')}")
        assert emitter.get_handler_count("interaction") == 1

        removed = emitter.unsubscribe("interaction", test_handler)
        logger.info(f"Handler removed: {removed}")
        assert removed is True
        assert emitter.get_handler_count("interaction") == 0

        # Try to remove again
        removed = emitter.unsubscribe("interaction", test_handler)
        logger.info(f"Handler removed again: {removed}")
        assert removed is False
        logger.info("✓ Handler unsubscription test passed")

    def test_clear_handlers(self, emitter: EventEmitter) -> None:
        """Test clearing handlers."""
        logger.info("Testing clear handlers")

        async def handler1(event: EventBase) -> None:
            pass

        async def handler2(event: EventBase) -> None:
            pass

        emitter.subscribe("interaction", handler1)
        emitter.subscribe("navigation", handler2)

        # Clear specific event type
        cleared = emitter.clear_handlers("interaction")
        logger.info(f"Handlers cleared for 'interaction': {cleared}")
        assert cleared == 1
        assert emitter.get_handler_count("interaction") == 0
        assert emitter.get_handler_count("navigation") == 1

        # Clear all handlers
        cleared = emitter.clear_handlers()
        logger.info(f"All handlers cleared: {cleared}")
        assert cleared == 1
        assert emitter.get_handler_count() == 0
        logger.info("✓ Clear handlers test passed")


class TestEventFilter:
    """Test EventFilter functionality."""

    @pytest.fixture
    def sample_events(self) -> list[EventBase]:
        """Create sample events for testing."""
        logger.info("Creating sample events fixture")
        return [
            InteractionEvent(
                action="click", selector="#login-btn", page_url="https://example.com/login", session_id="session-123"
            ),
            InteractionEvent(
                action="fill",
                selector="input[name='username']",
                page_url="https://test.com/signup",
                session_id="session-123",
            ),
            NavigationEvent(
                from_url="https://example.com",
                to_url="https://example.com/dashboard",
                page_url="https://example.com/dashboard",
                session_id="session-123",
            ),
            NetworkEvent(
                request_url="https://api.example.com/user",
                method="GET",
                page_url="https://example.com",
                session_id="session-123",
            ),
        ]

    def test_event_type_filtering(self, sample_events: list[EventBase]) -> None:
        """Test filtering by event type."""
        logger.info("Testing event type filtering")
        filter = EventFilter(event_types=["interaction"])

        results = [e for e in sample_events if filter.should_process(e)]
        logger.info(f"Filtered results count: {len(results)}")
        assert len(results) == 2
        assert all(e.event_type == "interaction" for e in results)
        logger.info("✓ Event type filtering test passed")

    def test_domain_filtering(self, sample_events: list[EventBase]) -> None:
        """Test filtering by domain."""
        logger.info("Testing domain filtering")
        filter = EventFilter(domains=["example.com"])

        results = [e for e in sample_events if filter.should_process(e)]
        logger.info(f"Filtered results count: {len(results)}")
        # Should match events from example.com but not test.com
        assert len(results) == 3
        assert all("example.com" in e.page_url for e in results)
        logger.info("✓ Domain filtering test passed")

    def test_selector_filtering(self, sample_events: list[EventBase]) -> None:
        """Test filtering by selector patterns."""
        logger.info("Testing selector filtering")
        filter = EventFilter(selectors=["#login-btn"])

        results = [e for e in sample_events if filter.should_process(e)]
        logger.info(f"Filtered results count: {len(results)}")
        assert len(results) == 1
        assert hasattr(results[0], "selector")
        assert getattr(results[0], "selector") == "#login-btn"
        logger.info("✓ Selector filtering test passed")

    def test_custom_filter_function(self, sample_events: list[EventBase]) -> None:
        """Test custom filter function."""
        logger.info("Testing custom filter function")

        def click_only(event: EventBase) -> bool:
            return hasattr(event, "action") and event.action == "click"

        filter = EventFilter(custom_filter=click_only)

        results = [e for e in sample_events if filter.should_process(e)]
        logger.info(f"Filtered results count: {len(results)}")
        assert len(results) == 1
        assert getattr(results[0], "action") == "click"
        logger.info("✓ Custom filter function test passed")

    def test_exclude_mode(self, sample_events: list[EventBase]) -> None:
        """Test exclusion filtering."""
        logger.info("Testing exclusion filtering")
        filter = EventFilter(event_types=["interaction"], exclude_mode=True)

        results = [e for e in sample_events if filter.should_process(e)]
        logger.info(f"Filtered results count: {len(results)}")
        # Should exclude interaction events
        assert len(results) == 2
        assert all(e.event_type != "interaction" for e in results)
        logger.info("✓ Exclusion filtering test passed")

    def test_filter_combination(self, sample_events: list[EventBase]) -> None:
        """Test combining multiple filter criteria."""
        logger.info("Testing filter combination")
        filter = EventFilter(event_types=["interaction"], domains=["example.com"])

        results = [e for e in sample_events if filter.should_process(e)]
        logger.info(f"Filtered results count: {len(results)}")
        # Should match interaction events from example.com only
        assert len(results) == 1
        assert results[0].event_type == "interaction"
        assert "example.com" in results[0].page_url
        logger.info("✓ Filter combination test passed")


class TestFilterHelpers:
    """Test filter helper functions."""

    def test_create_domain_filter(self) -> None:
        """Test domain filter helper."""
        logger.info("Testing create_domain_filter helper")
        filter = create_domain_filter(["example.com", "test.org"])

        # Should match
        event1 = InteractionEvent(
            action="click", selector="#btn", page_url="https://example.com/page", session_id="session-123"
        )
        assert filter.should_process(event1)

        # Should not match
        event2 = InteractionEvent(
            action="click", selector="#btn", page_url="https://other.com/page", session_id="session-123"
        )
        assert not filter.should_process(event2)
        logger.info("✓ Domain filter helper test passed")

    def test_create_action_filter(self) -> None:
        """Test action filter helper."""
        logger.info("Testing create_action_filter helper")
        filter = create_action_filter(["click", "hover"])

        # Should match
        event1 = InteractionEvent(
            action="click", selector="#btn", page_url="https://example.com", session_id="session-123"
        )
        assert filter.should_process(event1)

        # Should not match (wrong action)
        event2 = InteractionEvent(
            action="fill", selector="#input", page_url="https://example.com", session_id="session-123"
        )
        assert not filter.should_process(event2)

        # Should not match (not interaction event)
        event3 = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/page",
            page_url="https://example.com/page",
            session_id="session-123",
        )
        assert not filter.should_process(event3)
        logger.info("✓ Action filter helper test passed")

    def test_create_network_filter(self) -> None:
        """Test network filter helper."""
        logger.info("Testing create_network_filter helper")
        filter = create_network_filter(methods=["POST", "PUT"], status_codes=[200, 201], min_size=1000)

        # Should match all criteria
        event1 = NetworkEvent(
            request_url="https://api.example.com",
            method="POST",
            status_code=201,
            response_size=2048,
            page_url="https://example.com",
            session_id="session-123",
        )
        assert filter.should_process(event1)

        # Should not match (wrong method)
        event2 = NetworkEvent(
            request_url="https://api.example.com",
            method="GET",
            status_code=200,
            response_size=2048,
            page_url="https://example.com",
            session_id="session-123",
        )
        assert not filter.should_process(event2)
        logger.info("✓ Network filter helper test passed")

    def test_create_time_range_filter(self) -> None:
        """Test time range filter helper."""
        logger.info("Testing create_time_range_filter helper")
        start_time = time.time()
        end_time = start_time + 3600  # 1 hour later

        filter = create_time_range_filter(start_time, end_time)

        # Should match (within range)
        event1 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123",
            timestamp=start_time + 1800,  # 30 minutes later
        )
        assert filter.should_process(event1)

        # Should not match (outside range)
        event2 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123",
            timestamp=end_time + 1,  # 1 second after end
        )
        assert not filter.should_process(event2)
        logger.info("✓ Time range filter helper test passed")


class TestFilterChain:
    """Test FilterChain functionality."""

    def test_empty_chain(self) -> None:
        """Test empty filter chain accepts all events."""
        logger.info("Testing empty filter chain")
        chain = FilterChain()

        event = InteractionEvent(
            action="click", selector="#btn", page_url="https://example.com", session_id="session-123"
        )
        assert chain.should_process(event)
        logger.info("✓ Empty filter chain test passed")

    def test_single_filter_chain(self) -> None:
        """Test chain with single filter."""
        logger.info("Testing single filter chain")
        filter1 = EventFilter(event_types=["interaction"])
        chain = FilterChain(filter1)

        # Should match
        event1 = InteractionEvent(
            action="click", selector="#btn", page_url="https://example.com", session_id="session-123"
        )
        assert chain.should_process(event1)

        # Should not match
        event2 = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/page",
            page_url="https://example.com/page",
            session_id="session-123",
        )
        assert not chain.should_process(event2)
        logger.info("✓ Single filter chain test passed")

    def test_and_chain(self) -> None:
        """Test AND filter chain."""
        logger.info("Testing AND filter chain")
        filter1 = EventFilter(event_types=["interaction"])
        filter2 = EventFilter(domains=["example.com"])

        chain = FilterChain(filter1)
        chain.add_filter(filter2, "and")

        # Should match (both filters pass)
        event1 = InteractionEvent(
            action="click", selector="#btn", page_url="https://example.com/page", session_id="session-123"
        )
        assert chain.should_process(event1)

        # Should not match (fails domain filter)
        event2 = InteractionEvent(
            action="click", selector="#btn", page_url="https://test.com/page", session_id="session-123"
        )
        assert not chain.should_process(event2)
        logger.info("✓ AND filter chain test passed")

    def test_or_chain(self) -> None:
        """Test OR filter chain."""
        logger.info("Testing OR filter chain")
        filter1 = EventFilter(event_types=["interaction"])
        filter2 = EventFilter(event_types=["navigation"])

        chain = FilterChain(filter1)
        chain.add_filter(filter2, "or")

        # Should match interaction
        event1 = InteractionEvent(
            action="click", selector="#btn", page_url="https://example.com", session_id="session-123"
        )
        assert chain.should_process(event1)

        # Should match navigation
        event2 = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/page",
            page_url="https://example.com/page",
            session_id="session-123",
        )
        assert chain.should_process(event2)

        # Should not match network
        event3 = NetworkEvent(
            request_url="https://api.example.com",
            method="GET",
            page_url="https://example.com",
            session_id="session-123",
        )
        assert not chain.should_process(event3)
        logger.info("✓ OR filter chain test passed")
