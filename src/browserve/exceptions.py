"""
Browserve exception hierarchy for comprehensive error handling.
"""
from __future__ import annotations
from typing import Optional, Dict, Any


class BrowserveException(Exception):
    """
    Base exception for all Browserve errors.
    
    Args:
        message: Error description
        error_code: Optional error code for programmatic handling
        details: Additional error context
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r})"
        )


class ValidationError(BrowserveException):
    """
    Raised when Pydantic validation fails or invalid data is provided.
    
    Examples:
        Invalid selector format, malformed configuration,
        invalid action parameters
    """
    
    def __init__(
        self, 
        message: str, 
        field_name: Optional[str] = None,
        invalid_value: Any = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.invalid_value = invalid_value


class ProfileError(BrowserveException):
    """
    Raised when profile operations fail.
    
    Examples:
        Profile creation failure, browser launch error,
        state persistence issues, profile corruption
    """
    
    def __init__(
        self, 
        message: str, 
        profile_id: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.profile_id = profile_id
        self.operation = operation


class ActionExecutionError(BrowserveException):
    """
    Raised when action execution fails.
    
    Examples:
        Element not found, interaction timeout,
        browser navigation failure, action validation error
    """
    
    def __init__(
        self, 
        message: str, 
        action_type: Optional[str] = None,
        selector: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.action_type = action_type
        self.selector = selector
        self.timeout = timeout


class LoggingError(BrowserveException):
    """
    Raised when logging operations fail.
    
    Examples:
        File write permission error, buffer overflow,
        log format conversion failure, event serialization error
    """
    
    def __init__(
        self, 
        message: str, 
        log_level: Optional[str] = None,
        log_format: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.log_level = log_level
        self.log_format = log_format


class ElementError(BrowserveException):
    """
    Raised when element operations fail.
    
    Examples:
        Element not found, invalid selector,
        element not visible/enabled, element interaction failure
    """
    
    def __init__(
        self, 
        message: str, 
        selector: Optional[str] = None,
        element_state: Optional[str] = None,
        page_url: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.selector = selector
        self.element_state = element_state
        self.page_url = page_url


class SessionError(BrowserveException):
    """
    Raised when session management operations fail.
    
    Examples:
        Session creation failure, context switching error,
        session cleanup issues, concurrent session conflicts
    """
    
    def __init__(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.session_id = session_id
        self.operation = operation


class ConfigurationError(BrowserveException):
    """
    Raised when configuration operations fail.
    
    Examples:
        Invalid configuration file, missing required settings,
        configuration merge conflict, environment variable errors
    """
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_file = config_file


# Common error code constants
class ErrorCodes:
    """Standard error codes for programmatic error handling."""
    
    # Validation errors
    INVALID_SELECTOR = "INVALID_SELECTOR"
    INVALID_URL = "INVALID_URL"
    INVALID_CONFIG = "INVALID_CONFIG"
    
    # Profile errors
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROFILE_CREATION_FAILED = "PROFILE_CREATION_FAILED"
    BROWSER_LAUNCH_FAILED = "BROWSER_LAUNCH_FAILED"
    
    # Action errors
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ACTION_TIMEOUT = "ACTION_TIMEOUT"
    INTERACTION_FAILED = "INTERACTION_FAILED"
    
    # Logging errors
    LOG_WRITE_FAILED = "LOG_WRITE_FAILED"
    BUFFER_OVERFLOW = "BUFFER_OVERFLOW"
    
    # Session errors
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    CONTEXT_CREATION_FAILED = "CONTEXT_CREATION_FAILED"
