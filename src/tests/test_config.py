"""
Test suite for Browserve configuration models.
"""
from __future__ import annotations
import os
import pytest
from pathlib import Path
from pydantic import ValidationError as PydanticValidationError
from browserve.models.config import (
    BrowserConfig,
    LoggingConfig,
    ProfileConfig,
    ConfigBase,
)


class TestBrowserConfig:
    """Test BrowserConfig validation and functionality."""
    
    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BrowserConfig()
        assert config.headless is True
        assert config.viewport == (1920, 1080)
        assert config.user_agent is None
        assert config.timeout == 30.0
        assert config.slow_mo == 0.0
        assert config.dev_tools is False
    
    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BrowserConfig(
            headless=False,
            viewport=(1280, 720),
            user_agent="Custom Agent",
            timeout=60.0,
            slow_mo=1.0,
            dev_tools=True
        )
        assert config.headless is False
        assert config.viewport == (1280, 720)
        assert config.user_agent == "Custom Agent"
        assert config.timeout == 60.0
        assert config.slow_mo == 1.0
        assert config.dev_tools is True
    
    def test_viewport_validation(self) -> None:
        """Test viewport dimension validation."""
        # Valid dimensions
        config = BrowserConfig(viewport=(1024, 768))
        assert config.viewport == (1024, 768)
        
        # Dimensions too small
        with pytest.raises(PydanticValidationError):
            BrowserConfig(viewport=(50, 50))
        
        # Dimensions too large
        with pytest.raises(PydanticValidationError):
            BrowserConfig(viewport=(8000, 5000))
    
    def test_timeout_validation(self) -> None:
        """Test timeout value constraints."""
        # Valid timeout
        config = BrowserConfig(timeout=45.0)
        assert config.timeout == 45.0
        
        # Timeout too low
        with pytest.raises(PydanticValidationError):
            BrowserConfig(timeout=0.5)
        
        # Timeout too high
        with pytest.raises(PydanticValidationError):
            BrowserConfig(timeout=500.0)
    
    def test_slow_mo_validation(self) -> None:
        """Test slow_mo value constraints."""
        # Valid slow_mo
        config = BrowserConfig(slow_mo=2.5)
        assert config.slow_mo == 2.5
        
        # Negative slow_mo
        with pytest.raises(PydanticValidationError):
            BrowserConfig(slow_mo=-1.0)
        
        # Too high slow_mo
        with pytest.raises(PydanticValidationError):
            BrowserConfig(slow_mo=10.0)


class TestLoggingConfig:
    """Test LoggingConfig validation and functionality."""
    
    def test_default_values(self) -> None:
        """Test default logging configuration."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "jsonl"
        assert config.filters == []
        assert config.buffer_size == 1000
        assert config.auto_flush is True
        assert config.output_path is None
        assert config.max_file_size == 100 * 1024 * 1024
        assert config.rotate_logs is True
    
    def test_log_level_validation(self) -> None:
        """Test log level validation and normalization."""
        # Valid levels (should be normalized to uppercase)
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"
        
        config = LoggingConfig(level="INFO")
        assert config.level == "INFO"
        
        # Invalid level
        with pytest.raises(PydanticValidationError):
            LoggingConfig(level="INVALID")
    
    def test_format_validation(self) -> None:
        """Test output format validation."""
        # Valid formats (should be normalized to lowercase)
        config = LoggingConfig(format="JSON")
        assert config.format == "json"
        
        config = LoggingConfig(format="csv")
        assert config.format == "csv"
        
        # Invalid format
        with pytest.raises(PydanticValidationError):
            LoggingConfig(format="xml")
    
    def test_buffer_size_validation(self) -> None:
        """Test buffer size constraints."""
        # Valid buffer size
        config = LoggingConfig(buffer_size=500)
        assert config.buffer_size == 500
        
        # Buffer size too small
        with pytest.raises(PydanticValidationError):
            LoggingConfig(buffer_size=5)
        
        # Buffer size too large
        with pytest.raises(PydanticValidationError):
            LoggingConfig(buffer_size=50000)
    
    def test_output_path_conversion(self) -> None:
        """Test output path string to Path conversion."""
        # String path
        config = LoggingConfig(output_path="/tmp/log.jsonl")
        assert isinstance(config.output_path, Path)
        assert str(config.output_path) == "/tmp/log.jsonl"
        
        # Path object
        path_obj = Path("/tmp/test.log")
        config = LoggingConfig(output_path=path_obj)
        assert config.output_path == path_obj
        
        # None value
        config = LoggingConfig(output_path=None)
        assert config.output_path is None
    
    def test_max_file_size_validation(self) -> None:
        """Test max file size constraints."""
        # Valid size
        config = LoggingConfig(max_file_size=50 * 1024 * 1024)
        assert config.max_file_size == 50 * 1024 * 1024
        
        # Size too small
        with pytest.raises(PydanticValidationError):
            LoggingConfig(max_file_size=500 * 1024)  # 500KB


class TestProfileConfig:
    """Test ProfileConfig validation and functionality."""
    
    def test_valid_profile_config(self) -> None:
        """Test valid profile configuration."""
        config = ProfileConfig(
            profile_id="test_profile",
            profile_path="/tmp/profiles/test",
            persistent_state=True,
            clear_on_startup=False,
            max_sessions=5,
            session_timeout=1800.0
        )
        assert config.profile_id == "test_profile"
        assert isinstance(config.profile_path, Path)
        assert config.persistent_state is True
        assert config.max_sessions == 5
        assert config.session_timeout == 1800.0
    
    def test_profile_id_validation(self) -> None:
        """Test profile ID validation."""
        # Valid profile ID
        config = ProfileConfig(profile_id="valid_profile-123")
        assert config.profile_id == "valid_profile-123"
        
        # Empty profile ID
        with pytest.raises(PydanticValidationError):
            ProfileConfig(profile_id="")
        
        # Profile ID with invalid characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            with pytest.raises(PydanticValidationError):
                ProfileConfig(profile_id=f"invalid{char}profile")
    
    def test_profile_id_whitespace_handling(self) -> None:
        """Test profile ID whitespace trimming."""
        config = ProfileConfig(profile_id="  trimmed_profile  ")
        assert config.profile_id == "trimmed_profile"
    
    def test_max_sessions_validation(self) -> None:
        """Test max sessions constraints."""
        # Valid range
        config = ProfileConfig(profile_id="test", max_sessions=25)
        assert config.max_sessions == 25
        
        # Below minimum
        with pytest.raises(PydanticValidationError):
            ProfileConfig(profile_id="test", max_sessions=0)
        
        # Above maximum
        with pytest.raises(PydanticValidationError):
            ProfileConfig(profile_id="test", max_sessions=100)
    
    def test_session_timeout_validation(self) -> None:
        """Test session timeout constraints."""
        # Valid timeout
        config = ProfileConfig(profile_id="test", session_timeout=7200.0)
        assert config.session_timeout == 7200.0
        
        # Below minimum
        with pytest.raises(PydanticValidationError):
            ProfileConfig(profile_id="test", session_timeout=30.0)
        
        # Above maximum
        with pytest.raises(PydanticValidationError):
            ProfileConfig(profile_id="test", session_timeout=90000.0)


class TestConfigBase:
    """Test ConfigBase functionality and merging."""
    
    def test_default_config_base(self) -> None:
        """Test default ConfigBase initialization."""
        config = ConfigBase()
        assert isinstance(config.browser_config, BrowserConfig)
        assert isinstance(config.logging_config, LoggingConfig)
        assert config.profile_config == {}
    
    def test_custom_config_base(self) -> None:
        """Test ConfigBase with custom components."""
        browser_config = BrowserConfig(headless=False, timeout=45.0)
        logging_config = LoggingConfig(level="DEBUG", buffer_size=500)
        profile_config = {"custom_key": "custom_value"}
        
        config = ConfigBase(
            browser_config=browser_config,
            logging_config=logging_config,
            profile_config=profile_config
        )
        
        assert config.browser_config.headless is False
        assert config.browser_config.timeout == 45.0
        assert config.logging_config.level == "DEBUG"
        assert config.logging_config.buffer_size == 500
        assert config.profile_config["custom_key"] == "custom_value"
    
    def test_config_merging(self) -> None:
        """Test configuration merging functionality."""
        base_config = ConfigBase(
            browser_config=BrowserConfig(headless=True, timeout=30.0),
            logging_config=LoggingConfig(level="INFO", buffer_size=1000),
            profile_config={"base_key": "base_value"}
        )
        
        override_config = ConfigBase(
            browser_config=BrowserConfig(headless=False, viewport=(800, 600)),
            logging_config=LoggingConfig(level="DEBUG"),
            profile_config={"override_key": "override_value"}
        )
        
        merged = base_config.merge_with(override_config)
        
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
    
    def test_merge_preserves_originals(self) -> None:
        """Test that merging doesn't modify original configs."""
        original = ConfigBase(
            browser_config=BrowserConfig(headless=True)
        )
        override = ConfigBase(
            browser_config=BrowserConfig(headless=False)
        )
        
        original_headless = original.browser_config.headless
        override_headless = override.browser_config.headless
        
        merged = original.merge_with(override)
        
        # Originals should be unchanged
        assert original.browser_config.headless == original_headless
        assert override.browser_config.headless == override_headless
        
        # Merged should have override value
        assert merged.browser_config.headless is False
    
    def test_from_env_empty(self) -> None:
        """Test from_env with no environment variables."""
        # Clear environment
        env_vars = [k for k in os.environ.keys() if k.startswith('BROWSERVE_')]
        for var in env_vars:
            del os.environ[var]
        
        config = ConfigBase.from_env()
        # Should use defaults
        assert config.browser_config.headless is True
        assert config.logging_config.level == "INFO"
    
    def test_from_env_with_variables(self) -> None:
        """Test from_env with environment variables set."""
        # Set test environment variables
        os.environ['BROWSERVE_HEADLESS'] = 'false'
        os.environ['BROWSERVE_VIEWPORT'] = '1600x900'
        os.environ['BROWSERVE_LOG_LEVEL'] = 'DEBUG'
        os.environ['BROWSERVE_BUFFER_SIZE'] = '2000'
        
        try:
            config = ConfigBase.from_env()
            
            assert config.browser_config.headless is False
            assert config.browser_config.viewport == (1600, 900)
            assert config.logging_config.level == "DEBUG"
            assert config.logging_config.buffer_size == 2000
        
        finally:
            # Cleanup
            env_vars = ['BROWSERVE_HEADLESS', 'BROWSERVE_VIEWPORT', 
                       'BROWSERVE_LOG_LEVEL', 'BROWSERVE_BUFFER_SIZE']
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]
    
    def test_from_env_invalid_values(self) -> None:
        """Test from_env handles invalid environment values gracefully."""
        os.environ['BROWSERVE_VIEWPORT'] = 'invalid_format'
        os.environ['BROWSERVE_TIMEOUT'] = 'not_a_number'
        os.environ['BROWSERVE_BUFFER_SIZE'] = 'also_not_a_number'
        
        try:
            config = ConfigBase.from_env()
            # Should use defaults for invalid values
            assert config.browser_config.viewport == (1920, 1080)
            assert config.browser_config.timeout == 30.0
            assert config.logging_config.buffer_size == 1000
        
        finally:
            # Cleanup
            env_vars = ['BROWSERVE_VIEWPORT', 'BROWSERVE_TIMEOUT', 
                       'BROWSERVE_BUFFER_SIZE']
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]


class TestConfigIntegration:
    """Test configuration integration scenarios."""
    
    def test_complex_merge_scenario(self) -> None:
        """Test complex configuration merging scenario."""
        # Global config
        global_config = ConfigBase(
            browser_config=BrowserConfig(
                headless=True,
                viewport=(1920, 1080),
                timeout=30.0
            ),
            logging_config=LoggingConfig(
                level="INFO",
                buffer_size=1000,
                auto_flush=True
            )
        )
        
        # Profile-specific config
        profile_config = ConfigBase(
            browser_config=BrowserConfig(
                headless=False,  # Override for debugging
                slow_mo=1.0      # Add debugging delay
            ),
            logging_config=LoggingConfig(
                level="DEBUG",   # More verbose for this profile
                buffer_size=500  # Smaller buffer for real-time
            )
        )
        
        # Session-specific config
        session_config = ConfigBase(
            browser_config=BrowserConfig(
                viewport=(1280, 720)  # Specific viewport for this session
            )
        )
        
        # Merge in hierarchy: global -> profile -> session
        merged = global_config.merge_with(profile_config).merge_with(session_config)
        
        # Verify final merged state
        assert merged.browser_config.headless is False    # From profile
        assert merged.browser_config.viewport == (1280, 720)  # From session
        assert merged.browser_config.timeout == 30.0     # From global
        assert merged.browser_config.slow_mo == 1.0      # From profile
        
        assert merged.logging_config.level == "DEBUG"    # From profile
        assert merged.logging_config.buffer_size == 500  # From profile
        assert merged.logging_config.auto_flush is True  # From global
    
    def test_serialization_and_deserialization(self) -> None:
        """Test config can be serialized and deserialized."""
        original = ConfigBase(
            browser_config=BrowserConfig(
                headless=False,
                viewport=(1280, 720),
                user_agent="Test Agent",
                timeout=45.0
            ),
            logging_config=LoggingConfig(
                level="DEBUG",
                format="json",
                buffer_size=500,
                output_path="/tmp/test.log"
            ),
            profile_config={
                "custom_setting": "value",
                "number_setting": 42
            }
        )
        
        # Serialize to dict
        config_dict = original.model_dump()
        
        # Recreate from dict
        recreated = ConfigBase(**config_dict)
        
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
