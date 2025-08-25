"""
Base event models for browser interaction tracking.

Provides EventBase and specific event types for comprehensive logging
of browser automation activities.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
import time


class EventBase(BaseModel):
    """
    Base model for all browser events.
    
    All browser interactions, navigations, and state changes emit events
    that inherit from this base class. Events are immutable and contain
    comprehensive metadata for tracking and analysis.
    """
    
    event_type: str = Field(
        description="Type of event (interaction, navigation, etc.)"
    )
    timestamp: float = Field(
        default_factory=time.time, 
        description="Unix timestamp when event occurred"
    )
    page_url: str = Field(
        description="URL of page where event occurred"
    )
    session_id: str = Field(
        description="Unique session identifier"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event-specific data"
    )
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Ensure event_type is not empty."""
        if not v or not v.strip():
            raise ValueError("event_type cannot be empty")
        return v.strip()
    
    @field_validator('page_url')
    @classmethod
    def validate_page_url(cls, v: str) -> str:
        """Basic URL validation."""
        if not v or not v.strip():
            raise ValueError("page_url cannot be empty")
        
        # Basic URL format check
        url = v.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValueError("page_url must be a valid HTTP/HTTPS URL")
        
        return url
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Ensure session_id is not empty."""
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        return v.strip()


class InteractionEvent(EventBase):
    """
    Browser interaction event for user actions.
    
    Captures clicks, form fills, hovers, and other user interactions
    with page elements. Includes element context and interaction data.
    """
    
    event_type: str = Field(default="interaction", frozen=True)
    action: str = Field(
        description="Type of interaction (click, fill, hover, etc.)"
    )
    selector: str = Field(
        description="CSS selector or XPath used to target element"
    )
    value: Optional[str] = Field(
        None, 
        description="Input value for fill actions"
    )
    element_text: Optional[str] = Field(
        None,
        description="Text content of the target element"
    )
    element_tag: Optional[str] = Field(
        None,
        description="HTML tag name of the target element"
    )
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action type."""
        if not v or not v.strip():
            raise ValueError("action cannot be empty")
        
        valid_actions = {
            'click', 'double_click', 'right_click', 'hover', 'fill', 
            'clear', 'select', 'check', 'uncheck', 'focus', 'blur',
            'scroll', 'drag', 'drop'
        }
        
        action = v.strip().lower()
        if action not in valid_actions:
            raise ValueError(
                f"Invalid action '{action}'. Must be one of: "
                f"{', '.join(sorted(valid_actions))}"
            )
        
        return action
    
    @field_validator('selector')
    @classmethod
    def validate_selector(cls, v: str) -> str:
        """Basic selector validation."""
        if not v or not v.strip():
            raise ValueError("selector cannot be empty")
        return v.strip()


class NavigationEvent(EventBase):
    """
    Page navigation event for URL changes.
    
    Captures page loads, redirects, and navigation actions.
    Includes timing and navigation method information.
    """
    
    event_type: str = Field(default="navigation", frozen=True)
    from_url: str = Field(
        description="Previous page URL (empty for initial load)"
    )
    to_url: str = Field(
        description="Target page URL after navigation"
    )
    method: str = Field(
        default="navigate",
        description="Navigation method (navigate, reload, back, forward)"
    )
    load_time: Optional[float] = Field(
        None,
        ge=0.0,
        description="Page load time in seconds"
    )
    status_code: Optional[int] = Field(
        None,
        ge=100,
        le=599,
        description="HTTP response status code"
    )
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate navigation method."""
        if not v or not v.strip():
            raise ValueError("method cannot be empty")
        
        valid_methods = {'navigate', 'reload', 'back', 'forward', 'replace'}
        method = v.strip().lower()
        
        if method not in valid_methods:
            raise ValueError(
                f"Invalid method '{method}'. Must be one of: "
                f"{', '.join(sorted(valid_methods))}"
            )
        
        return method


class NetworkEvent(EventBase):
    """
    Network request event for HTTP activity.
    
    Captures outgoing requests and incoming responses during
    page interactions. Includes timing and size metrics.
    """
    
    event_type: str = Field(default="network_request", frozen=True)
    request_url: str = Field(
        description="Full URL of the network request"
    )
    method: str = Field(
        description="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )
    status_code: Optional[int] = Field(
        None,
        ge=100,
        le=599,
        description="HTTP response status code"
    )
    response_size: Optional[int] = Field(
        None,
        ge=0,
        description="Response body size in bytes"
    )
    request_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP request headers"
    )
    response_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP response headers"
    )
    duration: Optional[float] = Field(
        None,
        ge=0.0,
        description="Request duration in seconds"
    )
    
    @field_validator('request_url')
    @classmethod
    def validate_request_url(cls, v: str) -> str:
        """Validate request URL format."""
        if not v or not v.strip():
            raise ValueError("request_url cannot be empty")
        
        url = v.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValueError("request_url must be a valid HTTP/HTTPS URL")
        
        return url
    
    @field_validator('method')
    @classmethod
    def validate_http_method(cls, v: str) -> str:
        """Validate HTTP method."""
        if not v or not v.strip():
            raise ValueError("HTTP method cannot be empty")
        
        valid_methods = {
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 
            'HEAD', 'OPTIONS', 'CONNECT', 'TRACE'
        }
        
        method = v.strip().upper()
        if method not in valid_methods:
            raise ValueError(
                f"Invalid HTTP method '{method}'. Must be one of: "
                f"{', '.join(sorted(valid_methods))}"
            )
        
        return method


class DOMChangeEvent(EventBase):
    """
    DOM modification event for element changes.
    
    Captures when page elements are added, removed, or modified.
    Useful for tracking dynamic content and SPA interactions.
    """
    
    event_type: str = Field(default="dom_change", frozen=True)
    change_type: str = Field(
        description="Type of DOM change (added, removed, modified, attribute)"
    )
    selector: str = Field(
        description="Selector identifying the affected element"
    )
    old_value: Optional[str] = Field(
        None,
        description="Previous value before change"
    )
    new_value: Optional[str] = Field(
        None,
        description="New value after change"
    )
    attribute_name: Optional[str] = Field(
        None,
        description="Name of modified attribute (for attribute changes)"
    )
    element_tag: Optional[str] = Field(
        None,
        description="HTML tag name of affected element"
    )
    
    @field_validator('change_type')
    @classmethod
    def validate_change_type(cls, v: str) -> str:
        """Validate DOM change type."""
        if not v or not v.strip():
            raise ValueError("change_type cannot be empty")
        
        valid_types = {'added', 'removed', 'modified', 'attribute'}
        change_type = v.strip().lower()
        
        if change_type not in valid_types:
            raise ValueError(
                f"Invalid change_type '{change_type}'. Must be one of: "
                f"{', '.join(sorted(valid_types))}"
            )
        
        return change_type
    
    @field_validator('selector')
    @classmethod
    def validate_selector(cls, v: str) -> str:
        """Basic selector validation."""
        if not v or not v.strip():
            raise ValueError("selector cannot be empty")
        return v.strip()


# Event type registry for validation and introspection
EVENT_TYPES = {
    'interaction': InteractionEvent,
    'navigation': NavigationEvent,
    'network_request': NetworkEvent,
    'dom_change': DOMChangeEvent,
}


def create_event(event_type: str, **kwargs: Any) -> EventBase:
    """
    Factory function to create events by type.
    
    Args:
        event_type: Type of event to create
        **kwargs: Event-specific parameters
    
    Returns:
        EventBase instance of appropriate type
        
    Raises:
        ValueError: If event_type is not recognized
        
    Example:
        >>> event = create_event('interaction', 
        ...                     action='click', 
        ...                     selector='#button',
        ...                     page_url='https://example.com',
        ...                     session_id='session-123')
    """
    if event_type not in EVENT_TYPES:
        raise ValueError(
            f"Unknown event type '{event_type}'. "
            f"Valid types: {', '.join(EVENT_TYPES.keys())}"
        )
    
    event_class = EVENT_TYPES[event_type]
    return event_class(**kwargs)
