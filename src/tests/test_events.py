"""
Test suite for Browserve event system.
"""
from __future__ import annotations
import pytest
import asyncio
import time
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


class TestEventBase:
    """Test EventBase model validation and functionality."""
    
    def test_valid_event_creation(self) -> None:
        """Test creating valid EventBase instance."""
        event = EventBase(
            event_type="test_event",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.event_type == "test_event"
        assert event.page_url == "https://example.com"
        assert event.session_id == "session-123"
        assert isinstance(event.timestamp, float)
        assert event.metadata == {}
    
    def test_automatic_timestamp(self) -> None:
        """Test timestamp is automatically generated."""
        before = time.time()
        event = EventBase(
            event_type="test",
            page_url="https://example.com",
            session_id="session-123"
        )
        after = time.time()
        
        assert before <= event.timestamp <= after
    
    def test_custom_timestamp(self) -> None:
        """Test custom timestamp can be provided."""
        custom_time = 1234567890.0
        event = EventBase(
            event_type="test",
            page_url="https://example.com", 
            session_id="session-123",
            timestamp=custom_time
        )
        assert event.timestamp == custom_time
    
    def test_custom_metadata(self) -> None:
        """Test custom metadata can be added."""
        metadata = {"key1": "value1", "key2": 42}
        event = EventBase(
            event_type="test",
            page_url="https://example.com",
            session_id="session-123",
            metadata=metadata
        )
        assert event.metadata == metadata
    
    def test_empty_event_type_validation(self) -> None:
        """Test event_type cannot be empty."""
        with pytest.raises(PydanticValidationError):
            EventBase(
                event_type="",
                page_url="https://example.com",
                session_id="session-123"
            )
        
        with pytest.raises(PydanticValidationError):
            EventBase(
                event_type="   ",
                page_url="https://example.com", 
                session_id="session-123"
            )
    
    def test_invalid_url_validation(self) -> None:
        """Test page_url validation."""
        # Empty URL
        with pytest.raises(PydanticValidationError):
            EventBase(
                event_type="test",
                page_url="",
                session_id="session-123"
            )
        
        # Invalid URL format
        with pytest.raises(PydanticValidationError):
            EventBase(
                event_type="test",
                page_url="not-a-url",
                session_id="session-123"
            )
    
    def test_empty_session_id_validation(self) -> None:
        """Test session_id cannot be empty."""
        with pytest.raises(PydanticValidationError):
            EventBase(
                event_type="test",
                page_url="https://example.com",
                session_id=""
            )


class TestInteractionEvent:
    """Test InteractionEvent specific functionality."""
    
    def test_valid_interaction_creation(self) -> None:
        """Test creating valid InteractionEvent."""
        event = InteractionEvent(
            action="click",
            selector="#button",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.event_type == "interaction"
        assert event.action == "click"
        assert event.selector == "#button"
        assert event.value is None
        assert event.element_text is None
    
    def test_interaction_with_value(self) -> None:
        """Test interaction with input value."""
        event = InteractionEvent(
            action="fill",
            selector="input[name='username']",
            value="testuser",
            element_text="Username",
            element_tag="input",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.action == "fill"
        assert event.value == "testuser"
        assert event.element_text == "Username"
        assert event.element_tag == "input"
    
    def test_action_validation(self) -> None:
        """Test action type validation."""
        # Valid actions
        valid_actions = ['click', 'fill', 'hover', 'scroll']
        for action in valid_actions:
            event = InteractionEvent(
                action=action,
                selector="#test",
                page_url="https://example.com",
                session_id="session-123"
            )
            assert event.action == action
        
        # Invalid action
        with pytest.raises(PydanticValidationError):
            InteractionEvent(
                action="invalid_action",
                selector="#test",
                page_url="https://example.com",
                session_id="session-123"
            )
    
    def test_empty_selector_validation(self) -> None:
        """Test selector cannot be empty."""
        with pytest.raises(PydanticValidationError):
            InteractionEvent(
                action="click",
                selector="",
                page_url="https://example.com",
                session_id="session-123"
            )


class TestNavigationEvent:
    """Test NavigationEvent specific functionality."""
    
    def test_valid_navigation_creation(self) -> None:
        """Test creating valid NavigationEvent."""
        event = NavigationEvent(
            from_url="https://example.com/page1",
            to_url="https://example.com/page2",
            page_url="https://example.com/page2",
            session_id="session-123"
        )
        assert event.event_type == "navigation"
        assert event.from_url == "https://example.com/page1"
        assert event.to_url == "https://example.com/page2"
        assert event.method == "navigate"
        assert event.load_time is None
    
    def test_navigation_with_timing(self) -> None:
        """Test navigation with load time and status."""
        event = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/login",
            method="navigate",
            load_time=1.5,
            status_code=200,
            page_url="https://example.com/login",
            session_id="session-123"
        )
        assert event.load_time == 1.5
        assert event.status_code == 200
    
    def test_method_validation(self) -> None:
        """Test navigation method validation."""
        valid_methods = ['navigate', 'reload', 'back', 'forward']
        for method in valid_methods:
            event = NavigationEvent(
                from_url="https://example.com",
                to_url="https://example.com/page",
                method=method,
                page_url="https://example.com/page",
                session_id="session-123"
            )
            assert event.method == method
        
        # Invalid method
        with pytest.raises(PydanticValidationError):
            NavigationEvent(
                from_url="https://example.com",
                to_url="https://example.com/page", 
                method="invalid_method",
                page_url="https://example.com/page",
                session_id="session-123"
            )


class TestNetworkEvent:
    """Test NetworkEvent specific functionality."""
    
    def test_valid_network_creation(self) -> None:
        """Test creating valid NetworkEvent."""
        event = NetworkEvent(
            request_url="https://api.example.com/data",
            method="GET",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.event_type == "network_request"
        assert event.request_url == "https://api.example.com/data"
        assert event.method == "GET"
        assert event.status_code is None
    
    def test_network_with_response_data(self) -> None:
        """Test network event with response information."""
        event = NetworkEvent(
            request_url="https://api.example.com/data",
            method="POST",
            status_code=201,
            response_size=1024,
            request_headers={"Content-Type": "application/json"},
            response_headers={"Server": "nginx"},
            duration=0.25,
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.status_code == 201
        assert event.response_size == 1024
        assert event.request_headers["Content-Type"] == "application/json"
        assert event.duration == 0.25
    
    def test_http_method_validation(self) -> None:
        """Test HTTP method validation."""
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        for method in valid_methods:
            event = NetworkEvent(
                request_url="https://example.com",
                method=method,
                page_url="https://example.com",
                session_id="session-123"
            )
            assert event.method == method
        
        # Invalid method
        with pytest.raises(PydanticValidationError):
            NetworkEvent(
                request_url="https://example.com",
                method="INVALID",
                page_url="https://example.com",
                session_id="session-123"
            )


class TestDOMChangeEvent:
    """Test DOMChangeEvent specific functionality."""
    
    def test_valid_dom_change_creation(self) -> None:
        """Test creating valid DOMChangeEvent."""
        event = DOMChangeEvent(
            change_type="added",
            selector=".new-element",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.event_type == "dom_change"
        assert event.change_type == "added"
        assert event.selector == ".new-element"
    
    def test_dom_change_with_values(self) -> None:
        """Test DOM change with old/new values."""
        event = DOMChangeEvent(
            change_type="modified",
            selector="#content",
            old_value="Old Text",
            new_value="New Text",
            element_tag="div",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.old_value == "Old Text"
        assert event.new_value == "New Text"
        assert event.element_tag == "div"
    
    def test_attribute_change(self) -> None:
        """Test attribute change event."""
        event = DOMChangeEvent(
            change_type="attribute",
            selector="#element",
            attribute_name="class",
            old_value="old-class",
            new_value="new-class",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert event.change_type == "attribute"
        assert event.attribute_name == "class"
    
    def test_change_type_validation(self) -> None:
        """Test change type validation."""
        valid_types = ['added', 'removed', 'modified', 'attribute']
        for change_type in valid_types:
            event = DOMChangeEvent(
                change_type=change_type,
                selector="#test",
                page_url="https://example.com",
                session_id="session-123"
            )
            assert event.change_type == change_type
        
        # Invalid type
        with pytest.raises(PydanticValidationError):
            DOMChangeEvent(
                change_type="invalid_type",
                selector="#test",
                page_url="https://example.com",
                session_id="session-123"
            )


class TestEventFactory:
    """Test event factory functionality."""
    
    def test_create_event_by_type(self) -> None:
        """Test creating events using factory function."""
        # Create interaction event
        event = create_event(
            'interaction',
            action='click',
            selector='#button',
            page_url='https://example.com',
            session_id='session-123'
        )
        assert isinstance(event, InteractionEvent)
        assert event.action == 'click'
        
        # Create navigation event
        event = create_event(
            'navigation',
            from_url='https://example.com',
            to_url='https://example.com/page',
            page_url='https://example.com/page',
            session_id='session-123'
        )
        assert isinstance(event, NavigationEvent)
    
    def test_create_event_invalid_type(self) -> None:
        """Test factory with invalid event type."""
        with pytest.raises(ValueError, match="Unknown event type"):
            create_event('invalid_type')
    
    def test_event_types_registry(self) -> None:
        """Test EVENT_TYPES registry completeness."""
        expected_types = {
            'interaction', 'navigation', 'network_request', 'dom_change'
        }
        assert set(EVENT_TYPES.keys()) == expected_types


class TestEventEmitter:
    """Test EventEmitter functionality."""
    
    @pytest.fixture
    def emitter(self) -> EventEmitter:
        """Create EventEmitter instance for testing."""
        return EventEmitter()
    
    @pytest.fixture
    def sample_event(self) -> InteractionEvent:
        """Create sample event for testing."""
        return InteractionEvent(
            action="click",
            selector="#button",
            page_url="https://example.com",
            session_id="session-123"
        )
    
    async def test_handler_subscription(self, emitter: EventEmitter) -> None:
        """Test event handler subscription."""
        handler_called = False
        received_event = None
        
        async def test_handler(event: EventBase) -> None:
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event
        
        emitter.subscribe('interaction', test_handler)
        assert emitter.get_handler_count('interaction') == 1
    
    async def test_event_emission(
        self, 
        emitter: EventEmitter, 
        sample_event: InteractionEvent
    ) -> None:
        """Test event emission to handlers."""
        handler_called = False
        received_event = None
        
        async def test_handler(event: EventBase) -> None:
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event
        
        emitter.subscribe('interaction', test_handler)
        result = await emitter.emit(sample_event)
        
        assert handler_called
        assert received_event == sample_event
        assert result['handlers_called'] == 1
        assert result['handlers_succeeded'] == 1
        assert result['handlers_failed'] == 0
    
    async def test_multiple_handlers(
        self, 
        emitter: EventEmitter,
        sample_event: InteractionEvent
    ) -> None:
        """Test multiple handlers for same event type."""
        call_count = 0
        
        async def handler1(event: EventBase) -> None:
            nonlocal call_count
            call_count += 1
        
        async def handler2(event: EventBase) -> None:
            nonlocal call_count
            call_count += 1
        
        emitter.subscribe('interaction', handler1)
        emitter.subscribe('interaction', handler2)
        
        await emitter.emit(sample_event)
        assert call_count == 2
    
    async def test_handler_error_isolation(
        self,
        emitter: EventEmitter,
        sample_event: InteractionEvent
    ) -> None:
        """Test handler errors don't break emission."""
        good_handler_called = False
        
        async def failing_handler(event: EventBase) -> None:
            raise ValueError("Handler error")
        
        async def good_handler(event: EventBase) -> None:
            nonlocal good_handler_called
            good_handler_called = True
        
        emitter.subscribe('interaction', failing_handler)
        emitter.subscribe('interaction', good_handler)
        
        result = await emitter.emit(sample_event)
        
        # Good handler should still be called
        assert good_handler_called
        assert result['handlers_succeeded'] == 1
        assert result['handlers_failed'] == 1
        assert len(result['errors']) == 1
    
    def test_decorator_subscription(
        self, 
        emitter: EventEmitter
    ) -> None:
        """Test decorator-based handler registration."""
        @emitter.on('interaction')
        async def decorated_handler(event: EventBase) -> None:
            pass
        
        assert emitter.get_handler_count('interaction') == 1
        assert 'interaction' in emitter.get_event_types()
    
    def test_handler_unsubscription(
        self, 
        emitter: EventEmitter
    ) -> None:
        """Test handler unsubscription."""
        async def test_handler(event: EventBase) -> None:
            pass
        
        emitter.subscribe('interaction', test_handler)
        assert emitter.get_handler_count('interaction') == 1
        
        removed = emitter.unsubscribe('interaction', test_handler)
        assert removed is True
        assert emitter.get_handler_count('interaction') == 0
        
        # Try to remove again
        removed = emitter.unsubscribe('interaction', test_handler)
        assert removed is False
    
    def test_clear_handlers(
        self, 
        emitter: EventEmitter
    ) -> None:
        """Test clearing handlers."""
        async def handler1(event: EventBase) -> None:
            pass
        
        async def handler2(event: EventBase) -> None:
            pass
        
        emitter.subscribe('interaction', handler1)
        emitter.subscribe('navigation', handler2)
        
        # Clear specific event type
        cleared = emitter.clear_handlers('interaction')
        assert cleared == 1
        assert emitter.get_handler_count('interaction') == 0
        assert emitter.get_handler_count('navigation') == 1
        
        # Clear all handlers
        cleared = emitter.clear_handlers()
        assert cleared == 1
        assert emitter.get_handler_count() == 0


class TestEventFilter:
    """Test EventFilter functionality."""
    
    @pytest.fixture
    def sample_events(self) -> list[EventBase]:
        """Create sample events for testing."""
        return [
            InteractionEvent(
                action="click",
                selector="#login-btn",
                page_url="https://example.com/login",
                session_id="session-123"
            ),
            InteractionEvent(
                action="fill",
                selector="input[name='username']",
                page_url="https://test.com/signup",
                session_id="session-123"
            ),
            NavigationEvent(
                from_url="https://example.com",
                to_url="https://example.com/dashboard",
                page_url="https://example.com/dashboard",
                session_id="session-123"
            ),
            NetworkEvent(
                request_url="https://api.example.com/user",
                method="GET",
                page_url="https://example.com",
                session_id="session-123"
            )
        ]
    
    def test_event_type_filtering(
        self, 
        sample_events: list[EventBase]
    ) -> None:
        """Test filtering by event type."""
        filter = EventFilter(event_types=['interaction'])
        
        results = [e for e in sample_events if filter.should_process(e)]
        assert len(results) == 2
        assert all(e.event_type == 'interaction' for e in results)
    
    def test_domain_filtering(
        self, 
        sample_events: list[EventBase]
    ) -> None:
        """Test filtering by domain."""
        filter = EventFilter(domains=['example.com'])
        
        results = [e for e in sample_events if filter.should_process(e)]
        # Should match events from example.com but not test.com
        assert len(results) == 3
        assert all('example.com' in e.page_url for e in results)
    
    def test_selector_filtering(
        self, 
        sample_events: list[EventBase]
    ) -> None:
        """Test filtering by selector patterns."""
        filter = EventFilter(selectors=['#login-btn'])
        
        results = [e for e in sample_events if filter.should_process(e)]
        assert len(results) == 1
        assert hasattr(results[0], 'selector')
        assert getattr(results[0], 'selector') == '#login-btn'
    
    def test_custom_filter_function(
        self, 
        sample_events: list[EventBase]
    ) -> None:
        """Test custom filter function."""
        def click_only(event: EventBase) -> bool:
            return hasattr(event, 'action') and event.action == 'click'
        
        filter = EventFilter(custom_filter=click_only)
        
        results = [e for e in sample_events if filter.should_process(e)]
        assert len(results) == 1
        assert getattr(results[0], 'action') == 'click'
    
    def test_exclude_mode(
        self, 
        sample_events: list[EventBase]
    ) -> None:
        """Test exclusion filtering."""
        filter = EventFilter(
            event_types=['interaction'], 
            exclude_mode=True
        )
        
        results = [e for e in sample_events if filter.should_process(e)]
        # Should exclude interaction events
        assert len(results) == 2
        assert all(e.event_type != 'interaction' for e in results)
    
    def test_filter_combination(
        self, 
        sample_events: list[EventBase]
    ) -> None:
        """Test combining multiple filter criteria."""
        filter = EventFilter(
            event_types=['interaction'],
            domains=['example.com']
        )
        
        results = [e for e in sample_events if filter.should_process(e)]
        # Should match interaction events from example.com only
        assert len(results) == 1
        assert results[0].event_type == 'interaction'
        assert 'example.com' in results[0].page_url


class TestFilterHelpers:
    """Test filter helper functions."""
    
    def test_create_domain_filter(self) -> None:
        """Test domain filter helper."""
        filter = create_domain_filter(['example.com', 'test.org'])
        
        # Should match
        event1 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com/page",
            session_id="session-123"
        )
        assert filter.should_process(event1)
        
        # Should not match
        event2 = InteractionEvent(
            action="click",
            selector="#btn", 
            page_url="https://other.com/page",
            session_id="session-123"
        )
        assert not filter.should_process(event2)
    
    def test_create_action_filter(self) -> None:
        """Test action filter helper."""
        filter = create_action_filter(['click', 'hover'])
        
        # Should match
        event1 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert filter.should_process(event1)
        
        # Should not match (wrong action)
        event2 = InteractionEvent(
            action="fill",
            selector="#input",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert not filter.should_process(event2)
        
        # Should not match (not interaction event)
        event3 = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/page",
            page_url="https://example.com/page",
            session_id="session-123"
        )
        assert not filter.should_process(event3)
    
    def test_create_network_filter(self) -> None:
        """Test network filter helper."""
        filter = create_network_filter(
            methods=['POST', 'PUT'],
            status_codes=[200, 201],
            min_size=1000
        )
        
        # Should match all criteria
        event1 = NetworkEvent(
            request_url="https://api.example.com",
            method="POST",
            status_code=201,
            response_size=2048,
            page_url="https://example.com",
            session_id="session-123"
        )
        assert filter.should_process(event1)
        
        # Should not match (wrong method)
        event2 = NetworkEvent(
            request_url="https://api.example.com", 
            method="GET",
            status_code=200,
            response_size=2048,
            page_url="https://example.com",
            session_id="session-123"
        )
        assert not filter.should_process(event2)
    
    def test_create_time_range_filter(self) -> None:
        """Test time range filter helper."""
        start_time = time.time()
        end_time = start_time + 3600  # 1 hour later
        
        filter = create_time_range_filter(start_time, end_time)
        
        # Should match (within range)
        event1 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123",
            timestamp=start_time + 1800  # 30 minutes later
        )
        assert filter.should_process(event1)
        
        # Should not match (outside range)
        event2 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123", 
            timestamp=end_time + 1  # 1 second after end
        )
        assert not filter.should_process(event2)


class TestFilterChain:
    """Test FilterChain functionality."""
    
    def test_empty_chain(self) -> None:
        """Test empty filter chain accepts all events."""
        chain = FilterChain()
        
        event = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert chain.should_process(event)
    
    def test_single_filter_chain(self) -> None:
        """Test chain with single filter."""
        filter1 = EventFilter(event_types=['interaction'])
        chain = FilterChain(filter1)
        
        # Should match
        event1 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert chain.should_process(event1)
        
        # Should not match
        event2 = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/page",
            page_url="https://example.com/page",
            session_id="session-123"
        )
        assert not chain.should_process(event2)
    
    def test_and_chain(self) -> None:
        """Test AND filter chain."""
        filter1 = EventFilter(event_types=['interaction'])
        filter2 = EventFilter(domains=['example.com'])
        
        chain = FilterChain(filter1)
        chain.add_filter(filter2, 'and')
        
        # Should match (both filters pass)
        event1 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com/page",
            session_id="session-123"
        )
        assert chain.should_process(event1)
        
        # Should not match (fails domain filter)
        event2 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://test.com/page",
            session_id="session-123"
        )
        assert not chain.should_process(event2)
    
    def test_or_chain(self) -> None:
        """Test OR filter chain."""
        filter1 = EventFilter(event_types=['interaction'])
        filter2 = EventFilter(event_types=['navigation'])
        
        chain = FilterChain(filter1)
        chain.add_filter(filter2, 'or')
        
        # Should match interaction
        event1 = InteractionEvent(
            action="click",
            selector="#btn",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert chain.should_process(event1)
        
        # Should match navigation
        event2 = NavigationEvent(
            from_url="https://example.com",
            to_url="https://example.com/page",
            page_url="https://example.com/page",
            session_id="session-123"
        )
        assert chain.should_process(event2)
        
        # Should not match network
        event3 = NetworkEvent(
            request_url="https://api.example.com",
            method="GET",
            page_url="https://example.com",
            session_id="session-123"
        )
        assert not chain.should_process(event3)
