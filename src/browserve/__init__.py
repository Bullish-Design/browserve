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

__version__ = "0.1.0"
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
]
