"""
Browserve: Modular Pydantic base classes for browser automation.

A library providing foundational components for building site-specific
browser automation tools with comprehensive logging and event tracking.
"""
from __future__ import annotations

from .exceptions import (
    BrowserveException,
    ValidationError,
    ProfileError,
    ActionExecutionError,
    LoggingError,
    ElementError,
    SessionError,
    ConfigurationError,
    ErrorCodes,
)
from .models.config import (
    BrowserConfig,
    LoggingConfig,
    ProfileConfig,
    ConfigBase,
)
from .events import (
    EventBase,
    InteractionEvent,
    NavigationEvent,
    NetworkEvent,
    DOMChangeEvent,
    EventHandler,
    EventEmitter,
    EventFilter,
    FilterChain,
    create_event,
    create_domain_filter,
    create_action_filter,
    create_selector_filter,
    create_event_type_filter,
    create_exclusion_filter,
    create_network_filter,
    create_time_range_filter,
    global_handler_registry,
)

__version__ = "0.1.2"
__all__ = [
    # Exception hierarchy
    "BrowserveException",
    "ValidationError",
    "ProfileError", 
    "ActionExecutionError",
    "LoggingError",
    "ElementError",
    "SessionError",
    "ConfigurationError",
    "ErrorCodes",
    
    # Configuration models
    "BrowserConfig",
    "LoggingConfig",
    "ProfileConfig", 
    "ConfigBase",
    
    # Event system
    "EventBase",
    "InteractionEvent",
    "NavigationEvent",
    "NetworkEvent", 
    "DOMChangeEvent",
    "EventHandler",
    "EventEmitter",
    "EventFilter",
    "FilterChain",
    "create_event",
    "create_domain_filter",
    "create_action_filter",
    "create_selector_filter",
    "create_event_type_filter",
    "create_exclusion_filter",
    "create_network_filter",
    "create_time_range_filter",
    "global_handler_registry",
]
