"""
Test suite for Browserve exception hierarchy.
"""

from __future__ import annotations
import pytest
import logging
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

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestBrowserveException:
    """Test base exception functionality."""

    def test_basic_instantiation(self) -> None:
        """Test basic exception creation."""
        logger.info("Testing basic BrowserveException instantiation")
        exc = BrowserveException("Test message")
        logger.info(f"Created exception: {exc}")
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.error_code is None
        assert exc.details == {}
        logger.info("✓ Basic instantiation test passed")

    def test_with_error_code(self) -> None:
        """Test exception with error code."""
        logger.info("Testing BrowserveException with error code")
        exc = BrowserveException("Test message", error_code="TEST_ERROR")
        logger.info(f"Created exception with error code: {exc}")
        assert str(exc) == "[TEST_ERROR] Test message"
        assert exc.error_code == "TEST_ERROR"
        logger.info("✓ Error code test passed")

    def test_with_details(self) -> None:
        """Test exception with additional details."""
        logger.info("Testing BrowserveException with details")
        details = {"context": "testing", "value": 42}
        exc = BrowserveException("Test message", details=details)
        logger.info(f"Created exception with details: {exc}")
        assert exc.details == details
        logger.info("✓ Details test passed")

    def test_repr(self) -> None:
        """Test exception string representation."""
        logger.info("Testing BrowserveException string representation")
        exc = BrowserveException("Test message", error_code="TEST", details={"key": "value"})
        repr_str = repr(exc)
        logger.info(f"Exception representation: {repr_str}")
        assert "BrowserveException" in repr_str
        assert "Test message" in repr_str
        assert "TEST" in repr_str
        logger.info("✓ String representation test passed")


class TestValidationError:
    """Test validation error specifics."""

    def test_validation_error_inheritance(self) -> None:
        """Test ValidationError inherits from BrowserveException."""
        logger.info("Testing ValidationError inheritance")
        exc = ValidationError("Invalid field")
        logger.info(f"Created ValidationError: {exc}")
        assert isinstance(exc, BrowserveException)
        assert isinstance(exc, ValidationError)
        logger.info("✓ Inheritance test passed")

    def test_with_field_information(self) -> None:
        """Test validation error with field context."""
        logger.info("Testing ValidationError with field context")
        exc = ValidationError("Invalid selector format", field_name="selector", invalid_value=">>invalid<<")
        logger.info(f"Created ValidationError with field info: {exc}")
        assert exc.field_name == "selector"
        assert exc.invalid_value == ">>invalid<<"
        logger.info("✓ Field information test passed")

    def test_can_be_raised_and_caught(self) -> None:
        """Test exception can be raised and caught correctly."""
        logger.info("Testing ValidationError raising and catching")
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test validation error")

        logger.info(f"Caught exception: {exc_info.value}")
        assert "Test validation error" in str(exc_info.value)
        logger.info("✓ Raise and catch test passed")


class TestProfileError:
    """Test profile error specifics."""

    def test_profile_error_inheritance(self) -> None:
        """Test ProfileError inherits properly."""
        logger.info("Testing ProfileError inheritance")
        exc = ProfileError("Profile failed")
        logger.info(f"Created ProfileError: {exc}")
        assert isinstance(exc, BrowserveException)
        assert isinstance(exc, ProfileError)
        logger.info("✓ Inheritance test passed")

    def test_with_profile_context(self) -> None:
        """Test profile error with context."""
        logger.info("Testing ProfileError with context")
        exc = ProfileError("Profile creation failed", profile_id="test_profile", operation="create")
        logger.info(f"Created ProfileError with context: {exc}")
        assert exc.profile_id == "test_profile"
        assert exc.operation == "create"
        logger.info("✓ Context test passed")

    def test_error_catching_hierarchy(self) -> None:
        """Test that ProfileError can be caught as base exception."""
        logger.info("Testing ProfileError catching hierarchy")
        with pytest.raises(BrowserveException):
            raise ProfileError("Profile error")
        logger.info("✓ Catching hierarchy test passed")


class TestActionExecutionError:
    """Test action execution error specifics."""

    def test_action_error_context(self) -> None:
        """Test action error with full context."""
        logger.info("Testing ActionExecutionError with context")
        exc = ActionExecutionError("Click action failed", action_type="click", selector="#button", timeout=30.0)
        logger.info(f"Created ActionExecutionError: {exc}")
        assert exc.action_type == "click"
        assert exc.selector == "#button"
        assert exc.timeout == 30.0
        logger.info("✓ Context test passed")

    def test_inheritance_chain(self) -> None:
        """Test proper inheritance."""
        logger.info("Testing ActionExecutionError inheritance")
        exc = ActionExecutionError("Action failed")
        logger.info(f"Created ActionExecutionError: {exc}")
        assert isinstance(exc, BrowserveException)
        assert isinstance(exc, ActionExecutionError)
        logger.info("✓ Inheritance test passed")


class TestLoggingError:
    """Test logging error specifics."""

    def test_logging_error_context(self) -> None:
        """Test logging error with context."""
        logger.info("Testing LoggingError with context")
        exc = LoggingError("Failed to write log", log_level="DEBUG", log_format="jsonl")
        logger.info(f"Created LoggingError: {exc}")
        assert exc.log_level == "DEBUG"
        assert exc.log_format == "jsonl"
        logger.info("✓ Context test passed")


class TestElementError:
    """Test element error specifics."""

    def test_element_error_context(self) -> None:
        """Test element error with full context."""
        logger.info("Testing ElementError with context")
        exc = ElementError(
            "Element not found", selector="#missing", element_state="not_found", page_url="https://example.com"
        )
        logger.info(f"Created ElementError: {exc}")
        assert exc.selector == "#missing"
        assert exc.element_state == "not_found"
        assert exc.page_url == "https://example.com"
        logger.info("✓ Context test passed")


class TestSessionError:
    """Test session error specifics."""

    def test_session_error_context(self) -> None:
        """Test session error with context."""
        logger.info("Testing SessionError with context")
        exc = SessionError("Session creation failed", session_id="session-123", operation="create")
        logger.info(f"Created SessionError: {exc}")
        assert exc.session_id == "session-123"
        assert exc.operation == "create"
        logger.info("✓ Context test passed")


class TestConfigurationError:
    """Test configuration error specifics."""

    def test_configuration_error_context(self) -> None:
        """Test configuration error with context."""
        logger.info("Testing ConfigurationError with context")
        exc = ConfigurationError("Invalid config key", config_key="invalid_key", config_file="/path/to/config.json")
        logger.info(f"Created ConfigurationError: {exc}")
        assert exc.config_key == "invalid_key"
        assert exc.config_file == "/path/to/config.json"
        logger.info("✓ Context test passed")


class TestErrorCodes:
    """Test error code constants."""

    def test_error_codes_exist(self) -> None:
        """Test that error code constants are defined."""
        logger.info("Testing error code constants existence")
        assert ErrorCodes.INVALID_SELECTOR == "INVALID_SELECTOR"
        assert ErrorCodes.INVALID_URL == "INVALID_URL"
        assert ErrorCodes.PROFILE_NOT_FOUND == "PROFILE_NOT_FOUND"
        assert ErrorCodes.ELEMENT_NOT_FOUND == "ELEMENT_NOT_FOUND"
        assert ErrorCodes.ACTION_TIMEOUT == "ACTION_TIMEOUT"
        logger.info("✓ Error codes existence test passed")

    def test_error_codes_are_strings(self) -> None:
        """Test error codes are string constants."""
        logger.info("Testing error code types")
        assert isinstance(ErrorCodes.INVALID_SELECTOR, str)
        assert isinstance(ErrorCodes.BROWSER_LAUNCH_FAILED, str)
        assert isinstance(ErrorCodes.LOG_WRITE_FAILED, str)
        logger.info("✓ Error code types test passed")


class TestExceptionIntegration:
    """Test exception usage patterns."""

    def test_exception_with_error_code_from_constants(self) -> None:
        """Test using error codes from constants."""
        logger.info("Testing exception with error code from constants")
        exc = ElementError(
            "Element not found on page", error_code=ErrorCodes.ELEMENT_NOT_FOUND, selector="#missing-element"
        )
        logger.info(f"Created exception with error code: {exc}")
        assert exc.error_code == ErrorCodes.ELEMENT_NOT_FOUND
        assert "[ELEMENT_NOT_FOUND]" in str(exc)
        logger.info("✓ Error code from constants test passed")

    def test_catch_specific_vs_base_exception(self) -> None:
        """Test exception catching hierarchy works correctly."""
        logger.info("Testing exception catching hierarchy")
        # Should catch specific exception type
        with pytest.raises(ValidationError):
            raise ValidationError("Specific validation error")

        # Should also catch base exception type
        with pytest.raises(BrowserveException):
            raise ValidationError("Validation error caught as base")
        logger.info("✓ Catching hierarchy test passed")

    def test_multiple_exception_handling(self) -> None:
        """Test handling multiple exception types."""
        logger.info("Testing multiple exception type handling")

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
        logger.info("✓ Multiple exception handling test passed")
