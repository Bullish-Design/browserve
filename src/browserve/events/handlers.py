"""
Event handling protocols and emission framework.

Provides type-safe event handler interfaces and async event emission
for the Browserve event system.
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable, Callable, Dict, List, Any
import asyncio
import logging
from .base import EventBase


# Configure logger for event handling
logger = logging.getLogger(__name__)


@runtime_checkable
class EventHandler(Protocol):
    """
    Protocol for async event handling functions.
    
    Event handlers must be async functions that accept an EventBase
    instance and return None. Handlers should not raise exceptions
    as they will be isolated and logged.
    """
    
    async def __call__(self, event: EventBase) -> None:
        """
        Process an event.
        
        Args:
            event: EventBase instance to process
            
        Note:
            Handlers should not raise exceptions. Any exceptions
            will be logged and isolated to prevent breaking the
            event emission flow.
        """
        ...


class EventEmitter:
    """
    Core event emission functionality with async handler support.
    
    Manages event handler registration and async event emission.
    Provides both direct subscription and decorator-based registration.
    Isolates handler errors to prevent breaking event flow.
    """
    
    def __init__(self) -> None:
        """Initialize event emitter with empty handler registry."""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._handler_count = 0
        
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe handler to specific event type.
        
        Args:
            event_type: Type of event to handle (e.g., 'interaction')
            handler: Async function to call when event occurs
            
        Example:
            >>> emitter = EventEmitter()
            >>> async def my_handler(event):
            ...     print(f"Received: {event.event_type}")
            >>> emitter.subscribe('interaction', my_handler)
        """
        if not callable(handler):
            raise TypeError("Handler must be callable")
            
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        self._handlers[event_type].append(handler)
        self._handler_count += 1
        
        logger.debug(
            f"Subscribed handler to '{event_type}' "
            f"(total handlers: {self._handler_count})"
        )
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """
        Unsubscribe handler from event type.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove
            
        Returns:
            True if handler was found and removed, False otherwise
        """
        if event_type not in self._handlers:
            return False
            
        handlers = self._handlers[event_type]
        if handler in handlers:
            handlers.remove(handler)
            self._handler_count -= 1
            
            # Clean up empty handler lists
            if not handlers:
                del self._handlers[event_type]
                
            logger.debug(
                f"Unsubscribed handler from '{event_type}' "
                f"(total handlers: {self._handler_count})"
            )
            return True
            
        return False
    
    def on(self, event_type: str) -> Callable[[EventHandler], EventHandler]:
        """
        Decorator for event handler registration.
        
        Args:
            event_type: Type of event to handle
            
        Returns:
            Decorator function that registers handlers
            
        Example:
            >>> emitter = EventEmitter()
            >>> @emitter.on('interaction')
            ... async def handle_interaction(event):
            ...     print(f"User {event.action} on {event.selector}")
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(event_type, handler)
            return handler
        return decorator
    
    async def emit(self, event: EventBase) -> Dict[str, Any]:
        """
        Emit event to all registered handlers.
        
        Handlers are executed concurrently using asyncio.gather.
        Individual handler failures are isolated and logged without
        affecting other handlers or breaking the emission process.
        
        Args:
            event: EventBase instance to emit
            
        Returns:
            Dict with emission statistics and any errors
            
        Example:
            >>> emitter = EventEmitter()
            >>> event = InteractionEvent(
            ...     action='click',
            ...     selector='#button', 
            ...     page_url='https://example.com',
            ...     session_id='session-123'
            ... )
            >>> result = await emitter.emit(event)
        """
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for event type: {event.event_type}")
            return {
                'event_type': event.event_type,
                'handlers_called': 0,
                'handlers_succeeded': 0,
                'handlers_failed': 0,
                'errors': []
            }
        
        # Create tasks for all handlers
        tasks = []
        for handler in handlers:
            task = self._safe_handler_call(handler, event)
            tasks.append(task)
        
        # Execute all handlers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        succeeded = 0
        failed = 0
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                errors.append({
                    'handler_index': i,
                    'error_type': type(result).__name__,
                    'error_message': str(result)
                })
            else:
                succeeded += 1
        
        logger.debug(
            f"Emitted {event.event_type}: "
            f"{succeeded} succeeded, {failed} failed"
        )
        
        return {
            'event_type': event.event_type,
            'handlers_called': len(handlers),
            'handlers_succeeded': succeeded,
            'handlers_failed': failed,
            'errors': errors
        }
    
    async def _safe_handler_call(
        self, 
        handler: EventHandler, 
        event: EventBase
    ) -> None:
        """
        Safely call event handler with error isolation.
        
        Args:
            handler: Handler function to call
            event: Event to pass to handler
            
        Raises:
            Exception: Any exception from handler (for gather())
        """
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Event handler error for {event.event_type}: "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )
            raise  # Re-raise for gather() to handle
    
    def get_handler_count(self, event_type: str = None) -> int:
        """
        Get number of registered handlers.
        
        Args:
            event_type: Specific event type, or None for total
            
        Returns:
            Number of handlers registered
        """
        if event_type is None:
            return self._handler_count
            
        return len(self._handlers.get(event_type, []))
    
    def get_event_types(self) -> List[str]:
        """
        Get list of event types with registered handlers.
        
        Returns:
            Sorted list of event type names
        """
        return sorted(self._handlers.keys())
    
    def clear_handlers(self, event_type: str = None) -> int:
        """
        Clear handlers for specific type or all types.
        
        Args:
            event_type: Event type to clear, or None for all
            
        Returns:
            Number of handlers cleared
        """
        if event_type is None:
            # Clear all handlers
            cleared = self._handler_count
            self._handlers.clear()
            self._handler_count = 0
            logger.info(f"Cleared all handlers ({cleared} total)")
            return cleared
        
        # Clear specific event type
        if event_type in self._handlers:
            cleared = len(self._handlers[event_type])
            del self._handlers[event_type]
            self._handler_count -= cleared
            logger.info(f"Cleared {cleared} handlers for '{event_type}'")
            return cleared
            
        return 0


class EventHandlerRegistry:
    """
    Global registry for managing event handlers across components.
    
    Provides a centralized location for registering and managing
    event handlers that should persist across page instances.
    """
    
    def __init__(self) -> None:
        """Initialize handler registry."""
        self._global_handlers: Dict[str, List[EventHandler]] = {}
        
    def register_global_handler(
        self, 
        event_type: str, 
        handler: EventHandler
    ) -> None:
        """
        Register handler to be applied to all event emitters.
        
        Args:
            event_type: Type of event to handle globally
            handler: Handler function to register
        """
        if event_type not in self._global_handlers:
            self._global_handlers[event_type] = []
            
        self._global_handlers[event_type].append(handler)
        logger.info(f"Registered global handler for '{event_type}'")
    
    def apply_to_emitter(self, emitter: EventEmitter) -> None:
        """
        Apply all global handlers to an event emitter.
        
        Args:
            emitter: EventEmitter to enhance with global handlers
        """
        for event_type, handlers in self._global_handlers.items():
            for handler in handlers:
                emitter.subscribe(event_type, handler)
        
        logger.debug(
            f"Applied {sum(len(h) for h in self._global_handlers.values())} "
            f"global handlers to emitter"
        )
    
    def get_global_handlers(self) -> Dict[str, List[EventHandler]]:
        """
        Get copy of global handlers registry.
        
        Returns:
            Dict mapping event types to handler lists
        """
        return {
            event_type: handlers.copy()
            for event_type, handlers in self._global_handlers.items()
        }


# Global registry instance
global_handler_registry = EventHandlerRegistry()
