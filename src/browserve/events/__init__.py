"""
Event system for browser interaction tracking and logging.

Provides comprehensive event models, async handler management, and flexible
filtering for browser automation workflows.
"""
from __future__ import annotations

from .base import (
    EventBase,
    InteractionEvent,
    NavigationEvent,
    NetworkEvent,
    DOMChangeEvent,
    EVENT_TYPES,
    create_event,
)
from .handlers import (
    EventHandler,
    EventEmitter,
    EventHandlerRegistry,
    global_handler_registry,
)
from .filters import (
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

__all__ = [
    # Base event models
    "EventBase",
    "InteractionEvent",
    "NavigationEvent", 
    "NetworkEvent",
    "DOMChangeEvent",
    "EVENT_TYPES",
    "create_event",
    
    # Event handling
    "EventHandler",
    "EventEmitter",
    "EventHandlerRegistry", 
    "global_handler_registry",
    
    # Event filtering
    "EventFilter",
    "FilterChain",
    "create_domain_filter",
    "create_action_filter",
    "create_selector_filter",
    "create_event_type_filter",
    "create_exclusion_filter",
    "create_network_filter",
    "create_time_range_filter",
]
