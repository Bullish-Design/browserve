"""
Test suite for Browserve exception hierarchy.
"""
from __future__ import annotations
import pytest
from browserve.exceptions import (
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


class TestBrowserveException:
    """Test base exception functionality."""
    
    def test_basic_instantiation(self) -> None:
        """Test basic exception creation."""
        exc = BrowserveException("Test message")
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.error_code is None
        assert exc.details == {}
    
    def test_with_error_code(self) -> None:
        """Test exception with error code."""
        exc = BrowserveException(
            "Test message", 
            error_code="TEST_ERROR"
        )
        assert str(exc) == "[TEST_ERROR] Test message"
        assert exc.error_code == "TEST_ERROR"
    
    def test_with_details(self) -> None:
        """Test exception with additional details."""
        details = {"context": "testing", "value": 42}
        exc = BrowserveException(
            "Test message", 
            details=details
        )
        assert exc.details == details
    
    def test_repr(self) -> None:
        """Test exception string representation."""
        exc = BrowserveException(
            "Test message",
            error_code="TEST",
            details={"key": "value"}
        )
        repr_str = repr(exc)
        assert "BrowserveException" in repr_str
        assert "Test message" in repr_str
        assert "TEST" in repr_str


class TestValidationError:
    """Test validation error specifics."""
    
    def test_validation_error_inheritance(self) -> None:
        """Test ValidationError inherits from BrowserveException."""
        exc = ValidationError("Invalid field")
        assert isinstance(exc, BrowserveException)
        assert isinstance(exc, ValidationError)
    
    def test_with_field_information(self) -> None:
        """Test validation error with field context."""
        exc = ValidationError(
            "Invalid selector format",
            field_name="selector",
            invalid_value=">>invalid<<"
        )
        assert exc.field_name == "selector"
        assert exc.invalid_value == ">>invalid<<"
    
    def test_can_be_raised_and_caught(self) -> None:
        """Test exception can be raised and caught correctly."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test validation error")
        
        assert "Test validation error" in str(exc_info.value)


class TestProfileError:
    """Test profile error specifics."""
    
    def test_profile_error_inheritance(self) -> None:
        """Test ProfileError inherits properly."""
        exc = ProfileError("Profile failed")
        assert isinstance(exc, BrowserveException)
        assert isinstance(exc, ProfileError)
    
    def test_with_profile_context(self) -> None:
        """Test profile error with context."""
        exc = ProfileError(
            "Profile creation failed",
            profile_id="test_profile",
            operation="create"
        )
        assert exc.profile_id == "test_profile"
        assert exc.operation == "create"
    
    def test_error_catching_hierarchy(self) -> None:
        """Test that ProfileError can be caught as base exception."""
        with pytest.raises(BrowserveException):
            raise ProfileError("Profile error")


class TestActionExecutionError:
    """Test action execution error specifics."""
    
    def test_action_error_context(self) -> None:
        """Test action error with full context."""
        exc = ActionExecutionError(
            "Click action failed",
            action_type="click",
            selector="#button",
            timeout=30.0
        )
        assert exc.action_type == "click"
        assert exc.selector == "#button"
        assert exc.timeout == 30.0
    
    def test_inheritance_chain(self) -> None:
        """Test proper inheritance."""
        exc = ActionExecutionError("Action failed")
        assert isinstance(exc, BrowserveException)
        assert isinstance(exc, ActionExecutionError)


class TestLoggingError:
    """Test logging error specifics."""
    
    def test_logging_error_context(self) -> None:
        """Test logging error with context."""
        exc = LoggingError(
            "Failed to write log",
            log_level="DEBUG",
            log_format="jsonl"
        )
        assert exc.log_level == "DEBUG"
        assert exc.log_format == "jsonl"


class TestElementError:
    """Test element error specifics."""
    
    def test_element_error_context(self) -> None:
        """Test element error with full context."""
        exc = ElementError(
            "Element not found",
            selector="#missing",
            element_state="not_found",
            page_url="https://example.com"
        )
        assert exc.selector == "#missing"
        assert exc.element_state == "not_found"
        assert exc.page_url == "https://example.com"


class TestSessionError:
    """Test session error specifics."""
    
    def test_session_error_context(self) -> None:
        """Test session error with context."""
        exc = SessionError(
            "Session creation failed",
            session_id="session-123",
            operation="create"
        )
        assert exc.session_id == "session-123"
        assert exc.operation == "create"


class TestConfigurationError:
    """Test configuration error specifics."""
    
    def test_configuration_error_context(self) -> None:
        """Test configuration error with context."""
        exc = ConfigurationError(
            "Invalid config key",
            config_key="invalid_key",
            config_file="/path/to/config.json"
        )
        assert exc.config_key == "invalid_key"
        assert exc.config_file == "/path/to/config.json"


class TestErrorCodes:
    """Test error code constants."""
    
    def test_error_codes_exist(self) -> None:
        """Test that error code constants are defined."""
        assert ErrorCodes.INVALID_SELECTOR == "INVALID_SELECTOR"
        assert ErrorCodes.INVALID_URL == "INVALID_URL"
        assert ErrorCodes.PROFILE_NOT_FOUND == "PROFILE_NOT_FOUND"
        assert ErrorCodes.ELEMENT_NOT_FOUND == "ELEMENT_NOT_FOUND"
        assert ErrorCodes.ACTION_TIMEOUT == "ACTION_TIMEOUT"
    
    def test_error_codes_are_strings(self) -> None:
        """Test error codes are string constants."""
        assert isinstance(ErrorCodes.INVALID_SELECTOR, str)
        assert isinstance(ErrorCodes.BROWSER_LAUNCH_FAILED, str)
        assert isinstance(ErrorCodes.LOG_WRITE_FAILED, str)


class TestExceptionIntegration:
    """Test exception usage patterns."""
    
    def test_exception_with_error_code_from_constants(self) -> None:
        """Test using error codes from constants."""
        exc = ElementError(
            "Element not found on page",
            error_code=ErrorCodes.ELEMENT_NOT_FOUND,
            selector="#missing-element"
        )
        assert exc.error_code == ErrorCodes.ELEMENT_NOT_FOUND
        assert "[ELEMENT_NOT_FOUND]" in str(exc)
    
    def test_catch_specific_vs_base_exception(self) -> None:
        """Test exception catching hierarchy works correctly."""
        # Should catch specific exception type
        with pytest.raises(ValidationError):
            raise ValidationError("Specific validation error")
        
        # Should also catch base exception type
        with pytest.raises(BrowserveException):
            raise ValidationError("Validation error caught as base")
    
    def test_multiple_exception_handling(self) -> None:
        """Test handling multiple exception types."""
        def raise_various_errors(error_type: str) -> None:
            if error_type == "validation":
                raise ValidationError("Validation failed")
            elif error_type == "profile":
                raise ProfileError("Profile failed")
            elif error_type == "action":
                raise ActionExecutionError("Action failed")
        
        # Test specific catching
        with pytest.raises(ValidationError):
            raise_various_errors("validation")
        
        with pytest.raises(ProfileError):
            raise_various_errors("profile")
        
        with pytest.raises(ActionExecutionError):
            raise_various_errors("action")
