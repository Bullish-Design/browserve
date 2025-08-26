"""
Test suite for Browserve configuration models.
"""

from __future__ import annotations
import os
import pytest
import logging
from pathlib import Path
from pydantic import ValidationError as PydanticValidationError
from browserve.models.config import (
    BrowserConfig,
    LoggingConfig,
    ProfileConfig,
    ConfigBase,
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestBrowserConfig:
    """Test BrowserConfig validation and functionality."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        logger.info("Testing BrowserConfig default values")
        config = BrowserConfig()
        logger.info(f"Created config: {config}")
        assert config.headless is True
        assert config.viewport == (1920, 1080)
        assert config.user_agent is None
        assert config.timeout == 30.0
        assert config.slow_mo == 0.0
        assert config.dev_tools is False
        logger.info("✓ Default values test passed")

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        logger.info("Testing BrowserConfig custom values")
        config = BrowserConfig(
            headless=False, viewport=(1280, 720), user_agent="Custom Agent", timeout=60.0, slow_mo=1.0, dev_tools=True
        )
        logger.info(f"Created config with custom values: {config}")
        assert config.headless is False
        assert config.viewport == (1280, 720)
        assert config.user_agent == "Custom Agent"
        assert config.timeout == 60.0
        assert config.slow_mo == 1.0
        assert config.dev_tools is True
        logger.info("✓ Custom values test passed")

    def test_viewport_validation(self) -> None:
        """Test viewport dimension validation."""
        logger.info("Testing viewport validation")
        # Valid dimensions
        config = BrowserConfig(viewport=(1024, 768))
        logger.info(f"Created config with valid viewport: {config.viewport}")
        assert config.viewport == (1024, 768)

        # Dimensions too small
        with pytest.raises(PydanticValidationError):
            logger.info("Testing viewport too small")
            BrowserConfig(viewport=(50, 50))

        # Dimensions too large
        with pytest.raises(PydanticValidationError):
            logger.info("Testing viewport too large")
            BrowserConfig(viewport=(8000, 5000))
        logger.info("✓ Viewport validation test passed")

    def test_timeout_validation(self) -> None:
        """Test timeout value constraints."""
        logger.info("Testing timeout validation")
        # Valid timeout
        config = BrowserConfig(timeout=45.0)
        logger.info(f"Created config with valid timeout: {config.timeout}")
        assert config.timeout == 45.0

        # Timeout too low
        with pytest.raises(PydanticValidationError):
            logger.info("Testing timeout too low")
            BrowserConfig(timeout=0.5)

        # Timeout too high
        with pytest.raises(PydanticValidationError):
            logger.info("Testing timeout too high")
            BrowserConfig(timeout=500.0)
        logger.info("✓ Timeout validation test passed")

    def test_slow_mo_validation(self) -> None:
        """Test slow_mo value constraints."""
        logger.info("Testing slow_mo validation")
        # Valid slow_mo
        config = BrowserConfig(slow_mo=2.5)
        logger.info(f"Created config with valid slow_mo: {config.slow_mo}")
        assert config.slow_mo == 2.5

        # Negative slow_mo
        with pytest.raises(PydanticValidationError):
            logger.info("Testing negative slow_mo")
            BrowserConfig(slow_mo=-1.0)

        # Too high slow_mo
        with pytest.raises(PydanticValidationError):
            logger.info("Testing slow_mo too high")
            BrowserConfig(slow_mo=10.0)
        logger.info("✓ Slow_mo validation test passed")


class TestLoggingConfig:
    """Test LoggingConfig validation and functionality."""

    def test_default_values(self) -> None:
        """Test default logging configuration."""
        logger.info("Testing LoggingConfig default values")
        config = LoggingConfig()
        logger.info(f"Created config: {config}")
        assert config.level == "INFO"
        assert config.format == "jsonl"
        assert config.filters == []
        assert config.buffer_size == 1000
        assert config.auto_flush is True
        assert config.output_path is None
        assert config.max_file_size == 100 * 1024 * 1024
        assert config.rotate_logs is True
        logger.info("✓ Default values test passed")

    def test_log_level_validation(self) -> None:
        """Test log level validation and normalization."""
        logger.info("Testing log level validation")
        # Valid levels (should be normalized to uppercase)
        config = LoggingConfig(level="debug")
        logger.info(f"Created config with debug level: {config.level}")
        assert config.level == "DEBUG"

        config = LoggingConfig(level="INFO")
        logger.info(f"Created config with INFO level: {config.level}")
        assert config.level == "INFO"

        # Invalid level
        with pytest.raises(PydanticValidationError):
            logger.info("Testing invalid log level")
            LoggingConfig(level="INVALID")
        logger.info("✓ Log level validation test passed")

    def test_format_validation(self) -> None:
        """Test output format validation."""
        logger.info("Testing format validation")
        # Valid formats (should be normalized to lowercase)
        config = LoggingConfig(format="JSON")
        logger.info(f"Created config with JSON format: {config.format}")
        assert config.format == "json"

        config = LoggingConfig(format="csv")
        logger.info(f"Created config with CSV format: {config.format}")
        assert config.format == "csv"

        # Invalid format
        with pytest.raises(PydanticValidationError):
            logger.info("Testing invalid format")
            LoggingConfig(format="xml")
        logger.info("✓ Format validation test passed")

    def test_buffer_size_validation(self) -> None:
        """Test buffer size constraints."""
        logger.info("Testing buffer size validation")
        # Valid buffer size
        config = LoggingConfig(buffer_size=500)
        logger.info(f"Created config with buffer size: {config.buffer_size}")
        assert config.buffer_size == 500

        # Buffer size too small
        with pytest.raises(PydanticValidationError):
            logger.info("Testing buffer size too small")
            LoggingConfig(buffer_size=5)

        # Buffer size too large
        with pytest.raises(PydanticValidationError):
            logger.info("Testing buffer size too large")
            LoggingConfig(buffer_size=50000)
        logger.info("✓ Buffer size validation test passed")

    def test_output_path_conversion(self) -> None:
        """Test output path string to Path conversion."""
        logger.info("Testing output path conversion")
        # String path
        config = LoggingConfig(output_path="/tmp/log.jsonl")
        logger.info(f"Created config with string path: {config.output_path}")
        assert isinstance(config.output_path, Path)
        assert str(config.output_path) == "/tmp/log.jsonl"

        # Path object
        path_obj = Path("/tmp/test.log")
        config = LoggingConfig(output_path=path_obj)
        logger.info(f"Created config with Path object: {config.output_path}")
        assert config.output_path == path_obj

        # None value
        config = LoggingConfig(output_path=None)
        logger.info("Created config with None output path")
        assert config.output_path is None
        logger.info("✓ Output path conversion test passed")

    def test_max_file_size_validation(self) -> None:
        """Test max file size constraints."""
        logger.info("Testing max file size validation")
        # Valid size
        config = LoggingConfig(max_file_size=50 * 1024 * 1024)
        logger.info(f"Created config with max file size: {config.max_file_size}")
        assert config.max_file_size == 50 * 1024 * 1024

        # Size too small
        with pytest.raises(PydanticValidationError):
            logger.info("Testing max file size too small")
            LoggingConfig(max_file_size=500 * 1024)  # 500KB
        logger.info("✓ Max file size validation test passed")


class TestProfileConfig:
    """Test ProfileConfig validation and functionality."""

    def test_valid_profile_config(self) -> None:
        """Test valid profile configuration."""
        logger.info("Testing valid ProfileConfig")
        config = ProfileConfig(
            profile_id="test_profile",
            profile_path="/tmp/profiles/test",
            persistent_state=True,
            clear_on_startup=False,
            max_sessions=5,
            session_timeout=1800.0,
        )
        logger.info(f"Created profile config: {config}")
        assert config.profile_id == "test_profile"
        assert isinstance(config.profile_path, Path)
        assert config.persistent_state is True
        assert config.max_sessions == 5
        assert config.session_timeout == 1800.0
        logger.info("✓ Valid profile config test passed")

    def test_profile_id_validation(self) -> None:
        """Test profile ID validation."""
        logger.info("Testing profile ID validation")
        # Valid profile ID
        config = ProfileConfig(profile_id="valid_profile-123")
        logger.info(f"Created config with valid profile ID: {config.profile_id}")
        assert config.profile_id == "valid_profile-123"

        # Empty profile ID
        with pytest.raises(PydanticValidationError):
            logger.info("Testing empty profile ID")
            ProfileConfig(profile_id="")

        # Profile ID with invalid characters
        invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        for char in invalid_chars:
            with pytest.raises(PydanticValidationError):
                logger.info(f"Testing profile ID with invalid character: {char}")
                ProfileConfig(profile_id=f"invalid{char}profile")
        logger.info("✓ Profile ID validation test passed")

    def test_profile_id_whitespace_handling(self) -> None:
        """Test profile ID whitespace trimming."""
        logger.info("Testing profile ID whitespace handling")
        config = ProfileConfig(profile_id="  trimmed_profile  ")
        logger.info(f"Created config with whitespace: '{config.profile_id}'")
        assert config.profile_id == "trimmed_profile"
        logger.info("✓ Profile ID whitespace test passed")

    def test_max_sessions_validation(self) -> None:
        """Test max sessions constraints."""
        logger.info("Testing max sessions validation")
        # Valid range
        config = ProfileConfig(profile_id="test", max_sessions=25)
        logger.info(f"Created config with max sessions: {config.max_sessions}")
        assert config.max_sessions == 25

        # Below minimum
        with pytest.raises(PydanticValidationError):
            logger.info("Testing max sessions below minimum")
            ProfileConfig(profile_id="test", max_sessions=0)

        # Above maximum
        with pytest.raises(PydanticValidationError):
            logger.info("Testing max sessions above maximum")
            ProfileConfig(profile_id="test", max_sessions=100)
        logger.info("✓ Max sessions validation test passed")

    def test_session_timeout_validation(self) -> None:
        """Test session timeout constraints."""
        logger.info("Testing session timeout validation")
        # Valid timeout
        config = ProfileConfig(profile_id="test", session_timeout=7200.0)
        logger.info(f"Created config with session timeout: {config.session_timeout}")
        assert config.session_timeout == 7200.0

        # Below minimum
        with pytest.raises(PydanticValidationError):
            logger.info("Testing session timeout below minimum")
            ProfileConfig(profile_id="test", session_timeout=30.0)

        # Above maximum
        with pytest.raises(PydanticValidationError):
            logger.info("Testing session timeout above maximum")
            ProfileConfig(profile_id="test", session_timeout=90000.0)
        logger.info("✓ Session timeout validation test passed")


class TestConfigBase:
    """Test ConfigBase functionality and merging."""

    def test_default_config_base(self) -> None:
        """Test default ConfigBase initialization."""
        logger.info("Testing default ConfigBase")
        config = ConfigBase()
        logger.info(f"Created default config: {config}")
        assert isinstance(config.browser_config, BrowserConfig)
        assert isinstance(config.logging_config, LoggingConfig)
        assert config.profile_config == {}
        logger.info("✓ Default ConfigBase test passed")

    def test_custom_config_base(self) -> None:
        """Test ConfigBase with custom components."""
        logger.info("Testing ConfigBase with custom components")
        browser_config = BrowserConfig(headless=False, timeout=45.0)
        logging_config = LoggingConfig(level="DEBUG", buffer_size=500)
        profile_config = {"custom_key": "custom_value"}

        config = ConfigBase(browser_config=browser_config, logging_config=logging_config, profile_config=profile_config)
        logger.info(f"Created custom config: {config}")

        assert config.browser_config.headless is False
        assert config.browser_config.timeout == 45.0
        assert config.logging_config.level == "DEBUG"
        assert config.logging_config.buffer_size == 500
        assert config.profile_config["custom_key"] == "custom_value"
        logger.info("✓ Custom ConfigBase test passed")

    def test_config_merging(self) -> None:
        """Test configuration merging functionality."""
        logger.info("Testing config merging")
        base_config = ConfigBase(
            browser_config=BrowserConfig(headless=True, timeout=30.0),
            logging_config=LoggingConfig(level="INFO", buffer_size=1000),
            profile_config={"base_key": "base_value"},
        )

        override_config = ConfigBase(
            browser_config=BrowserConfig(headless=False, viewport=(800, 600)),
            logging_config=LoggingConfig(level="DEBUG"),
            profile_config={"override_key": "override_value"},
        )

        merged = base_config.merge_with(override_config)
        logger.info(f"Merged config: {merged}")

        # Browser config should merge with override precedence
        assert merged.browser_config.headless is False  # Overridden
        assert merged.browser_config.viewport == (800, 600)  # Overridden
        assert merged.browser_config.timeout == 30.0  # From base

        # Logging config should merge
        assert merged.logging_config.level == "DEBUG"  # Overridden
        assert merged.logging_config.buffer_size == 1000  # From base

        # Profile config should merge dictionaries
        assert merged.profile_config["base_key"] == "base_value"
        assert merged.profile_config["override_key"] == "override_value"
        logger.info("✓ Config merging test passed")

    def test_merge_preserves_originals(self) -> None:
        """Test that merging doesn't modify original configs."""
        logger.info("Testing merge preserves originals")
        original = ConfigBase(browser_config=BrowserConfig(headless=True))
        override = ConfigBase(browser_config=BrowserConfig(headless=False))

        original_headless = original.browser_config.headless
        override_headless = override.browser_config.headless

        merged = original.merge_with(override)
        logger.info(f"Merged config headless: {merged.browser_config.headless}")

        # Originals should be unchanged
        assert original.browser_config.headless == original_headless
        assert override.browser_config.headless == override_headless

        # Merged should have override value
        assert merged.browser_config.headless is False
        logger.info("✓ Merge preserves originals test passed")

    def test_from_env_empty(self) -> None:
        """Test from_env with no environment variables."""
        logger.info("Testing from_env with empty environment")
        # Clear environment
        env_vars = [k for k in os.environ.keys() if k.startswith("BROWSERVE_")]
        for var in env_vars:
            del os.environ[var]

        config = ConfigBase.from_env()
        logger.info(f"Config from empty env: {config}")
        # Should use defaults
        assert config.browser_config.headless is True
        assert config.logging_config.level == "INFO"
        logger.info("✓ From_env empty test passed")

    def test_from_env_with_variables(self) -> None:
        """Test from_env with environment variables set."""
        logger.info("Testing from_env with environment variables")
        # Set test environment variables
        os.environ["BROWSERVE_HEADLESS"] = "false"
        os.environ["BROWSERVE_VIEWPORT"] = "1600x900"
        os.environ["BROWSERVE_LOG_LEVEL"] = "DEBUG"
        os.environ["BROWSERVE_BUFFER_SIZE"] = "2000"

        try:
            config = ConfigBase.from_env()
            logger.info(f"Config from env: {config}")

            assert config.browser_config.headless is False
            assert config.browser_config.viewport == (1600, 900)
            assert config.logging_config.level == "DEBUG"
            assert config.logging_config.buffer_size == 2000

        finally:
            # Cleanup
            env_vars = ["BROWSERVE_HEADLESS", "BROWSERVE_VIEWPORT", "BROWSERVE_LOG_LEVEL", "BROWSERVE_BUFFER_SIZE"]
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]
        logger.info("✓ From_env with variables test passed")

    def test_from_env_invalid_values(self) -> None:
        """Test from_env handles invalid environment values gracefully."""
        logger.info("Testing from_env with invalid values")
        os.environ["BROWSERVE_VIEWPORT"] = "invalid_format"
        os.environ["BROWSERVE_TIMEOUT"] = "not_a_number"
        os.environ["BROWSERVE_BUFFER_SIZE"] = "also_not_a_number"

        try:
            config = ConfigBase.from_env()
            logger.info(f"Config from env with invalid values: {config}")
            # Should use defaults for invalid values
            assert config.browser_config.viewport == (1920, 1080)
            assert config.browser_config.timeout == 30.0
            assert config.logging_config.buffer_size == 1000

        finally:
            # Cleanup
            env_vars = ["BROWSERVE_VIEWPORT", "BROWSERVE_TIMEOUT", "BROWSERVE_BUFFER_SIZE"]
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]
        logger.info("✓ From_env invalid values test passed")


class TestConfigIntegration:
    """Test configuration integration scenarios."""

    def test_complex_merge_scenario(self) -> None:
        """Test complex configuration merging scenario."""
        logger.info("Testing complex merge scenario")
        # Global config
        global_config = ConfigBase(
            browser_config=BrowserConfig(headless=True, viewport=(1920, 1080), timeout=30.0),
            logging_config=LoggingConfig(level="INFO", buffer_size=1000, auto_flush=True),
        )

        # Profile-specific config
        profile_config = ConfigBase(
            browser_config=BrowserConfig(
                headless=False,  # Override for debugging
                slow_mo=1.0,  # Add debugging delay
            ),
            logging_config=LoggingConfig(
                level="DEBUG",  # More verbose for this profile
                buffer_size=500,  # Smaller buffer for real-time
            ),
        )

        # Session-specific config
        session_config = ConfigBase(
            browser_config=BrowserConfig(
                viewport=(1280, 720)  # Specific viewport for this session
            )
        )

        # Merge in hierarchy: global -> profile -> session
        merged = global_config.merge_with(profile_config).merge_with(session_config)
        logger.info(f"Complex merged config: {merged}")

        # Verify final merged state
        assert merged.browser_config.headless is False  # From profile
        assert merged.browser_config.viewport == (1280, 720)  # From session
        assert merged.browser_config.timeout == 30.0  # From global
        assert merged.browser_config.slow_mo == 1.0  # From profile

        assert merged.logging_config.level == "DEBUG"  # From profile
        assert merged.logging_config.buffer_size == 500  # From profile
        assert merged.logging_config.auto_flush is True  # From global
        logger.info("✓ Complex merge scenario test passed")

    def test_serialization_and_deserialization(self) -> None:
        """Test config can be serialized and deserialized."""
        logger.info("Testing config serialization and deserialization")
        original = ConfigBase(
            browser_config=BrowserConfig(headless=False, viewport=(1280, 720), user_agent="Test Agent", timeout=45.0),
            logging_config=LoggingConfig(level="DEBUG", format="json", buffer_size=500, output_path="/tmp/test.log"),
            profile_config={"custom_setting": "value", "number_setting": 42},
        )

        # Serialize to dict
        config_dict = original.model_dump()
        logger.info(f"Serialized config: {config_dict}")

        # Recreate from dict
        recreated = ConfigBase(**config_dict)
        logger.info(f"Recreated config: {recreated}")

        # Verify all values match
        assert recreated.browser_config.headless == original.browser_config.headless
        assert recreated.browser_config.viewport == original.browser_config.viewport
        assert recreated.browser_config.user_agent == original.browser_config.user_agent
        assert recreated.browser_config.timeout == original.browser_config.timeout

        assert recreated.logging_config.level == original.logging_config.level
        assert recreated.logging_config.format == original.logging_config.format
        assert recreated.logging_config.buffer_size == original.logging_config.buffer_size
        assert recreated.logging_config.output_path == original.logging_config.output_path

        assert recreated.profile_config == original.profile_config
        logger.info("✓ Serialization and deserialization test passed")
