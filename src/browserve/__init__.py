"""
Browserve: Modular Pydantic base classes for browser automation.

A library providing foundational components for building site-specific
browser automation tools with comprehensive logging and event tracking.
"""

from __future__ import annotations

from .core import PageBase, BrowserLogger
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
from .models.results import (
    ActionStatus,
    ActionResult,
    ActionMetrics,
)
from .actions import (
    PlaywrightAction,
    ComposedAction,
    ConditionalAction,
    ClickAction,
    FillAction,
    NavigationAction,
    WaitAction,
    HoverAction,
    ScrollAction,
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
from .utils import (
    validate_css_selector,
    validate_xpath_selector,
    validate_selector,
    validate_url,
    sanitize_url,
    validate_session_id,
    validate_timeout,
    sanitize_element_text,
    validate_action_type,
)

__version__ = "0.1.4"
__all__ = [
    # Core page interface
    "PageBase",
    "BrowserLogger",
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
    # Action result models
    "ActionStatus",
    "ActionResult",
    "ActionMetrics",
    # Action framework
    "PlaywrightAction",
    "ComposedAction",
    "ConditionalAction",
    "ClickAction",
    "FillAction",
    "NavigationAction",
    "WaitAction",
    "HoverAction",
    "ScrollAction",
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
    # Validation utilities
    "validate_css_selector",
    "validate_xpath_selector",
    "validate_selector",
    "validate_url",
    "sanitize_url",
    "validate_session_id",
    "validate_timeout",
    "sanitize_element_text",
    "validate_action_type",
]
