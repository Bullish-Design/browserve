"""
Configuration models for Browserve using Pydantic v2.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from pydantic import BaseModel, Field, field_validator, model_validator
import os


class BrowserConfig(BaseModel):
    """
    Browser initialization configuration.

    Controls browser behavior, viewport settings, and performance options.
    """

    headless: bool = Field(True, description="Run browser in headless mode (no GUI)")
    viewport: Tuple[int, int] = Field((1920, 1080), description="Browser viewport size as (width, height)")
    user_agent: Optional[str] = Field(None, description="Custom user agent string for browser identification")
    timeout: float = Field(30.0, ge=1.0, le=300.0, description="Default timeout for operations in seconds")
    slow_mo: float = Field(0.0, ge=0.0, le=5.0, description="Slow down operations by specified seconds for debugging")
    dev_tools: bool = Field(False, description="Open browser developer tools on startup")

    @field_validator("viewport")
    def validate_viewport_dimensions(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """Ensure viewport dimensions are reasonable."""
        width, height = v
        if width < 100 or height < 100:
            raise ValueError("Viewport dimensions must be at least 100x100")
        if width > 7680 or height > 4320:
            raise ValueError("Viewport dimensions exceed maximum 7680x4320")
        return v


class LoggingConfig(BaseModel):
    """
    Event logging configuration.

    Controls how browser interactions are captured and persisted.
    """

    level: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    format: str = Field("jsonl", description="Output format (jsonl, json, csv)")
    filters: List[str] = Field(default_factory=list, description="Event type filters to include/exclude")
    buffer_size: int = Field(1000, ge=10, le=10000, description="Number of events to buffer before flushing")
    auto_flush: bool = Field(True, description="Automatically flush buffer when full")
    output_path: Optional[Path] = Field(None, description="Path to log file (None for stdout)")
    max_file_size: int = Field(
        100 * 1024 * 1024,  # 100MB
        ge=1024 * 1024,  # 1MB minimum
        description="Maximum log file size in bytes before rotation",
    )
    rotate_logs: bool = Field(True, description="Enable automatic log rotation")

    @field_validator("level")
    def validate_log_level(cls, v: str) -> str:
        """Ensure valid logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {', '.join(valid_levels)}")
        return v_upper

    @field_validator("format")
    def validate_format(cls, v: str) -> str:
        """Ensure valid output format."""
        valid_formats = {"jsonl", "json", "csv"}
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid format '{v}'. Must be one of: {', '.join(valid_formats)}")
        return v.lower()

    @field_validator("output_path", mode="before")
    def validate_output_path(cls, v: Any) -> Optional[Path]:
        """Convert string paths to Path objects."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        if isinstance(v, Path):
            return v
        raise ValueError(f"Invalid path type: {type(v)}")


class ProfileConfig(BaseModel):
    """
    Browser profile configuration.

    Controls profile isolation, state persistence, and session behavior.
    """

    profile_id: str = Field(description="Unique identifier for browser profile")
    profile_path: Optional[Path] = Field(None, description="Directory path for profile data storage")
    persistent_state: bool = Field(True, description="Persist cookies, localStorage, and session data")
    clear_on_startup: bool = Field(False, description="Clear profile data on initialization")
    max_sessions: int = Field(10, ge=1, le=50, description="Maximum concurrent sessions per profile")
    session_timeout: float = Field(
        3600.0,  # 1 hour
        ge=60.0,
        le=86400.0,  # 24 hours
        description="Session timeout in seconds",
    )

    @field_validator("profile_id")
    def validate_profile_id(cls, v: str) -> str:
        """Ensure profile ID is filesystem-safe."""
        if not v or not v.strip():
            raise ValueError("Profile ID cannot be empty")

        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Profile ID contains invalid characters: {invalid_chars}")

        return v.strip()

    @field_validator("profile_path", mode="before")
    def validate_profile_path(cls, v: Any) -> Optional[Path]:
        """Convert string paths to Path objects."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        if isinstance(v, Path):
            return v
        raise ValueError(f"Invalid path type: {type(v)}")


class ConfigBase(BaseModel):
    """
    Top-level configuration container with merge capabilities.

    Provides cascading configuration hierarchy:
    global → profile → session → action
    """

    browser_config: BrowserConfig = Field(default_factory=BrowserConfig, description="Browser initialization settings")
    logging_config: LoggingConfig = Field(default_factory=LoggingConfig, description="Event logging configuration")
    profile_config: Dict[str, Any] = Field(default_factory=dict, description="Profile-specific settings")

    def merge_with(self, other: ConfigBase) -> ConfigBase:
        """
        Merge this configuration with another, with other taking precedence.

        Args:
            other: Configuration to merge with (higher precedence)

        Returns:
            New ConfigBase instance with merged settings

        Example:
            >>> base = ConfigBase()
            >>> override = ConfigBase(
            ...     browser_config=BrowserConfig(headless=False)
            ... )
            >>> merged = base.merge_with(override)
            >>> assert merged.browser_config.headless is False
        """
        # Create new instances to avoid modifying originals
        merged_browser = BrowserConfig(
            **{**self.browser_config.model_dump(), **other.browser_config.model_dump(exclude_unset=True)}
        )

        merged_logging = LoggingConfig(
            **{**self.logging_config.model_dump(), **other.logging_config.model_dump(exclude_unset=True)}
        )

        merged_profile = {**self.profile_config, **other.profile_config}

        return ConfigBase(browser_config=merged_browser, logging_config=merged_logging, profile_config=merged_profile)

    @classmethod
    def from_env(cls) -> ConfigBase:
        """
        Create configuration from environment variables.

        Environment variables should be prefixed with 'BROWSERVE_':
        - BROWSERVE_HEADLESS=false
        - BROWSERVE_LOG_LEVEL=DEBUG
        - BROWSERVE_BUFFER_SIZE=500

        Returns:
            ConfigBase instance with environment variable overrides
        """
        env_config = {}

        # Browser config from environment
        browser_env = {}
        if "BROWSERVE_HEADLESS" in os.environ:
            browser_env["headless"] = os.environ["BROWSERVE_HEADLESS"].lower() == "true"
        if "BROWSERVE_VIEWPORT" in os.environ:
            viewport_str = os.environ["BROWSERVE_VIEWPORT"]
            try:
                width, height = map(int, viewport_str.split("x"))
                browser_env["viewport"] = (width, height)
            except ValueError:
                pass  # Use default viewport
        if "BROWSERVE_USER_AGENT" in os.environ:
            browser_env["user_agent"] = os.environ["BROWSERVE_USER_AGENT"]
        if "BROWSERVE_TIMEOUT" in os.environ:
            try:
                browser_env["timeout"] = float(os.environ["BROWSERVE_TIMEOUT"])
            except ValueError:
                pass  # Use default timeout

        if browser_env:
            env_config["browser_config"] = BrowserConfig(**browser_env)

        # Logging config from environment
        logging_env = {}
        if "BROWSERVE_LOG_LEVEL" in os.environ:
            logging_env["level"] = os.environ["BROWSERVE_LOG_LEVEL"]
        if "BROWSERVE_LOG_FORMAT" in os.environ:
            logging_env["format"] = os.environ["BROWSERVE_LOG_FORMAT"]
        if "BROWSERVE_BUFFER_SIZE" in os.environ:
            try:
                logging_env["buffer_size"] = int(os.environ["BROWSERVE_BUFFER_SIZE"])
            except ValueError:
                pass  # Use default buffer size
        if "BROWSERVE_LOG_PATH" in os.environ:
            logging_env["output_path"] = Path(os.environ["BROWSERVE_LOG_PATH"])

        if logging_env:
            env_config["logging_config"] = LoggingConfig(**logging_env)

        return cls(**env_config)

    @model_validator(mode="after")
    def validate_config_consistency(self) -> ConfigBase:
        """Validate configuration consistency across components."""
        # Ensure logging output directory exists if specified
        if self.logging_config.output_path and self.logging_config.output_path.parent:
            try:
                self.logging_config.output_path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError):
                # Will be handled at runtime
                pass

        return self
