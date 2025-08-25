"""
Event filtering system for selective event processing.

Provides flexible filtering capabilities to process only relevant events
based on type, domain, selector, and custom criteria.
"""
from __future__ import annotations
from typing import List, Callable, Optional, Any, Pattern
import re
from urllib.parse import urlparse
from .base import EventBase


class EventFilter:
    """
    Filter events based on multiple criteria.
    
    Supports filtering by event type, domain, selector patterns,
    and custom filter functions. Filters can be combined using
    logical operations.
    """
    
    def __init__(
        self,
        event_types: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        selectors: Optional[List[str]] = None,
        custom_filter: Optional[Callable[[EventBase], bool]] = None,
        exclude_mode: bool = False
    ) -> None:
        """
        Initialize event filter.
        
        Args:
            event_types: List of event types to include/exclude
            domains: List of domains to include/exclude
            selectors: List of selector patterns to include/exclude
            custom_filter: Custom filtering function
            exclude_mode: If True, filter excludes matches instead of including
        """
        self.event_types = set(event_types or [])
        self.domains = domains or []
        self.selectors = selectors or []
        self.custom_filter = custom_filter
        self.exclude_mode = exclude_mode
        
        # Compile selector patterns for performance
        self._selector_patterns: List[Pattern[str]] = []
        for selector in self.selectors:
            try:
                # Support both literal strings and regex patterns
                if selector.startswith('/') and selector.endswith('/'):
                    # Treat as regex pattern
                    pattern = re.compile(selector[1:-1])
                else:
                    # Treat as literal string (escape special chars)
                    pattern = re.compile(re.escape(selector))
                self._selector_patterns.append(pattern)
            except re.error:
                # Fall back to literal string matching
                pattern = re.compile(re.escape(selector))
                self._selector_patterns.append(pattern)
    
    def should_process(self, event: EventBase) -> bool:
        """
        Determine if event should be processed based on filter criteria.
        
        Args:
            event: Event to evaluate
            
        Returns:
            True if event passes filter, False otherwise
        """
        matches = self._matches_criteria(event)
        
        # Apply exclude/include mode
        return not matches if self.exclude_mode else matches
    
    def _matches_criteria(self, event: EventBase) -> bool:
        """
        Check if event matches filter criteria.
        
        Args:
            event: Event to check
            
        Returns:
            True if event matches all active criteria
        """
        # Check event types
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check domains
        if self.domains and not self._matches_domain(event):
            return False
        
        # Check selectors
        if self.selectors and not self._matches_selector(event):
            return False
        
        # Check custom filter
        if self.custom_filter and not self.custom_filter(event):
            return False
        
        return True
    
    def _matches_domain(self, event: EventBase) -> bool:
        """
        Check if event URL matches domain criteria.
        
        Args:
            event: Event to check
            
        Returns:
            True if event URL domain matches filter
        """
        try:
            parsed = urlparse(event.page_url)
            domain = parsed.netloc.lower()
            
            return any(
                domain_filter.lower() in domain
                for domain_filter in self.domains
            )
        except Exception:
            # If URL parsing fails, don't match
            return False
    
    def _matches_selector(self, event: EventBase) -> bool:
        """
        Check if event selector matches selector criteria.
        
        Args:
            event: Event to check
            
        Returns:
            True if event has selector that matches patterns
        """
        # Only events with selectors can match
        if not hasattr(event, 'selector'):
            return False
        
        selector = getattr(event, 'selector', '')
        if not selector:
            return False
        
        return any(
            pattern.search(selector)
            for pattern in self._selector_patterns
        )
    
    def combine_with(
        self, 
        other: EventFilter, 
        operation: str = 'and'
    ) -> EventFilter:
        """
        Combine this filter with another using logical operations.
        
        Args:
            other: Filter to combine with
            operation: 'and' or 'or' operation
            
        Returns:
            New EventFilter with combined criteria
        """
        if operation not in ('and', 'or'):
            raise ValueError("Operation must be 'and' or 'or'")
        
        if operation == 'and':
            # AND operation - event must pass both filters
            def combined_filter(event: EventBase) -> bool:
                return (
                    self.should_process(event) and 
                    other.should_process(event)
                )
        else:
            # OR operation - event must pass either filter
            def combined_filter(event: EventBase) -> bool:
                return (
                    self.should_process(event) or 
                    other.should_process(event)
                )
        
        return EventFilter(custom_filter=combined_filter)
    
    def __and__(self, other: EventFilter) -> EventFilter:
        """Support & operator for combining filters."""
        return self.combine_with(other, 'and')
    
    def __or__(self, other: EventFilter) -> EventFilter:
        """Support | operator for combining filters."""
        return self.combine_with(other, 'or')


# Helper functions for common filter patterns

def create_domain_filter(domains: List[str]) -> EventFilter:
    """
    Create filter that matches specific domains.
    
    Args:
        domains: List of domain strings to match
        
    Returns:
        EventFilter configured for domain matching
        
    Example:
        >>> filter = create_domain_filter(['example.com', 'test.org'])
        >>> # Will match events from example.com and test.org
    """
    return EventFilter(domains=domains)


def create_action_filter(actions: List[str]) -> EventFilter:
    """
    Create filter for specific interaction actions.
    
    Args:
        actions: List of action types to match
        
    Returns:
        EventFilter configured for action matching
        
    Example:
        >>> filter = create_action_filter(['click', 'fill'])
        >>> # Will match only click and fill interactions
    """
    def action_filter(event: EventBase) -> bool:
        if hasattr(event, 'action'):
            return getattr(event, 'action') in actions
        return False
    
    return EventFilter(
        event_types=['interaction'], 
        custom_filter=action_filter
    )


def create_selector_filter(selectors: List[str]) -> EventFilter:
    """
    Create filter for specific element selectors.
    
    Args:
        selectors: List of selector patterns to match
        
    Returns:
        EventFilter configured for selector matching
        
    Example:
        >>> filter = create_selector_filter(['#login', '.button'])
        >>> # Will match events on elements with id='login' or class='button'
    """
    return EventFilter(selectors=selectors)


def create_event_type_filter(event_types: List[str]) -> EventFilter:
    """
    Create filter for specific event types.
    
    Args:
        event_types: List of event types to match
        
    Returns:
        EventFilter configured for event type matching
        
    Example:
        >>> filter = create_event_type_filter(['navigation', 'interaction'])
        >>> # Will match only navigation and interaction events
    """
    return EventFilter(event_types=event_types)


def create_exclusion_filter(
    event_types: Optional[List[str]] = None,
    domains: Optional[List[str]] = None,
    selectors: Optional[List[str]] = None
) -> EventFilter:
    """
    Create filter that excludes matching events.
    
    Args:
        event_types: Event types to exclude
        domains: Domains to exclude
        selectors: Selectors to exclude
        
    Returns:
        EventFilter configured to exclude matches
        
    Example:
        >>> filter = create_exclusion_filter(domains=['ads.example.com'])
        >>> # Will exclude all events from ads.example.com
    """
    return EventFilter(
        event_types=event_types,
        domains=domains,
        selectors=selectors,
        exclude_mode=True
    )


def create_network_filter(
    methods: Optional[List[str]] = None,
    status_codes: Optional[List[int]] = None,
    min_size: Optional[int] = None
) -> EventFilter:
    """
    Create filter for network events with specific criteria.
    
    Args:
        methods: HTTP methods to match
        status_codes: Status codes to match
        min_size: Minimum response size in bytes
        
    Returns:
        EventFilter for network events
        
    Example:
        >>> filter = create_network_filter(
        ...     methods=['POST', 'PUT'],
        ...     status_codes=[200, 201],
        ...     min_size=1024
        ... )
    """
    def network_filter(event: EventBase) -> bool:
        if event.event_type != 'network_request':
            return False
        
        if methods and hasattr(event, 'method'):
            if getattr(event, 'method') not in methods:
                return False
        
        if status_codes and hasattr(event, 'status_code'):
            status = getattr(event, 'status_code')
            if status and status not in status_codes:
                return False
        
        if min_size and hasattr(event, 'response_size'):
            size = getattr(event, 'response_size')
            if size and size < min_size:
                return False
        
        return True
    
    return EventFilter(
        event_types=['network_request'],
        custom_filter=network_filter
    )


def create_time_range_filter(
    start_time: float,
    end_time: float
) -> EventFilter:
    """
    Create filter for events within time range.
    
    Args:
        start_time: Start timestamp (inclusive)
        end_time: End timestamp (exclusive)
        
    Returns:
        EventFilter for time range
        
    Example:
        >>> import time
        >>> now = time.time()
        >>> filter = create_time_range_filter(now - 3600, now)  # Last hour
    """
    def time_filter(event: EventBase) -> bool:
        return start_time <= event.timestamp < end_time
    
    return EventFilter(custom_filter=time_filter)


class FilterChain:
    """
    Chain multiple filters with configurable logic.
    
    Allows building complex filtering logic by combining
    multiple filters with AND/OR operations.
    """
    
    def __init__(self, initial_filter: Optional[EventFilter] = None) -> None:
        """Initialize filter chain."""
        self.filters: List[tuple[EventFilter, str]] = []
        if initial_filter:
            self.filters.append((initial_filter, 'and'))
    
    def add_filter(
        self, 
        filter: EventFilter, 
        operation: str = 'and'
    ) -> FilterChain:
        """
        Add filter to chain with specified operation.
        
        Args:
            filter: Filter to add
            operation: 'and' or 'or' operation
            
        Returns:
            Self for method chaining
        """
        if operation not in ('and', 'or'):
            raise ValueError("Operation must be 'and' or 'or'")
        
        self.filters.append((filter, operation))
        return self
    
    def should_process(self, event: EventBase) -> bool:
        """
        Evaluate all filters in chain.
        
        Args:
            event: Event to evaluate
            
        Returns:
            True if event passes chain logic
        """
        if not self.filters:
            return True  # No filters = accept all
        
        # Start with first filter result
        result = self.filters[0][0].should_process(event)
        
        # Apply remaining filters with their operations
        for filter, operation in self.filters[1:]:
            filter_result = filter.should_process(event)
            
            if operation == 'and':
                result = result and filter_result
            else:  # operation == 'or'
                result = result or filter_result
        
        return result
