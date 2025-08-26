"""
Test suite for Browserve validation utilities.
"""

from __future__ import annotations
import pytest
import logging
from browserve.utils.validation import (
    validate_css_selector,
    validate_xpath_selector,
    validate_selector,
    sanitize_url,
    validate_url,
    validate_session_id,
    validate_timeout,
    sanitize_element_text,
    validate_action_type,
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCSSValidation:
    """Test CSS selector validation."""

    def test_valid_css_selectors(self) -> None:
        """Test valid CSS selector formats."""
        logger.info("Testing CSS selector validation with valid selectors")

        valid_selectors = [
            "#id",
            ".class",
            "div",
            "div.class",
            "#id.class",
            "div#id.class",
            "[attribute='value']",
            "div > p",
            "div + p",
            "div ~ p",
            "input[type='text']",
            "a:hover",
            "p:first-child",
            "div:nth-child(2n+1)",
            ".class1.class2",
            "div, p, span",
            "*",
        ]

        for selector in valid_selectors:
            logger.info(f"Validating CSS selector: '{selector}'")
            result = validate_css_selector(selector)
            logger.info(f"Validation result: {result}")
            assert result, f"Should be valid: {selector}"

        logger.info(f"✓ All {len(valid_selectors)} valid CSS selectors passed validation")

    def test_invalid_css_selectors(self) -> None:
        """Test invalid CSS selector formats."""
        logger.info("Testing CSS selector validation with invalid selectors")

        invalid_selectors = [
            ("", "empty string"),
            ("   ", "whitespace only"),
            (None, "None value"),
            (123, "numeric value"),
            ("<script>", "HTML tag"),
            ("div>script<", "unclosed tag"),
            ("javascript:alert(1)", "javascript protocol"),
            ("div[onclick='alert()']", "event handler"),
            ("expression(alert(1))", "CSS expression"),
            ("eval(code)", "eval function"),
            ("[unclosed", "unclosed bracket"),
            ("unclosed)", "unmatched parenthesis"),
            ("div[attr=unquoted<value]", "dangerous unquoted value"),
        ]

        for selector, description in invalid_selectors:
            logger.info(f"Testing {description}: {repr(selector)}")
            result = validate_css_selector(selector)
            logger.info(f"Validation result: {result}")
            assert not result, f"Should be invalid: {selector}"

        logger.info(f"✓ All {len(invalid_selectors)} invalid CSS selectors correctly rejected")

    def test_css_balanced_brackets(self) -> None:
        """Test CSS selector bracket balancing."""
        logger.info("Testing CSS selector bracket balancing")

        # Valid balanced brackets
        balanced_selectors = [
            ("div[attr='value']", "attribute selector with quotes"),
            ("div:nth-child(2n+1)", "pseudo-class with parentheses"),
            ("input[type='text'][name='username']", "multiple attribute selectors"),
        ]

        for selector, description in balanced_selectors:
            logger.info(f"Testing balanced {description}: '{selector}'")
            result = validate_css_selector(selector)
            assert result, f"Balanced selector should be valid: {selector}"

        # Invalid unbalanced brackets
        unbalanced_selectors = [
            ("div[attr='value'", "unclosed square bracket"),
            ("div:nth-child(2n+1", "unclosed parenthesis"),
            ("div]attr='value']", "mismatched bracket order"),
        ]

        for selector, description in unbalanced_selectors:
            logger.info(f"Testing unbalanced {description}: '{selector}'")
            result = validate_css_selector(selector)
            assert not result, f"Unbalanced selector should be invalid: {selector}"

        logger.info("✓ CSS bracket balancing validation test passed")


class TestXPathValidation:
    """Test XPath selector validation."""

    def test_valid_xpath_selectors(self) -> None:
        """Test valid XPath expressions."""
        logger.info("Testing XPath selector validation with valid expressions")

        valid_xpaths = [
            ("//div", "descendant div elements"),
            ("/html/body/div", "absolute path"),
            ("//div[@id='content']", "attribute filter"),
            ("//span[text()='Click me']", "text content filter"),
            ("//a[contains(@href, 'example.com')]", "contains function"),
            (".//relative/path", "relative path"),
            ("../parent/element", "parent navigation"),
            ("//div[position()=1]", "position function"),
            ("//input[@type='text' and @name='username']", "multiple conditions"),
            ("id('my-element')", "id function"),
            ("//following::div", "following axis"),
            ("//ancestor::body", "ancestor axis"),
        ]

        for xpath, description in valid_xpaths:
            logger.info(f"Validating XPath {description}: '{xpath}'")
            result = validate_xpath_selector(xpath)
            logger.info(f"Validation result: {result}")
            assert result, f"Should be valid: {xpath}"

        logger.info(f"✓ All {len(valid_xpaths)} valid XPath expressions passed validation")

    def test_invalid_xpath_selectors(self) -> None:
        """Test invalid XPath expressions."""
        logger.info("Testing XPath validation with invalid expressions")

        invalid_xpaths = [
            ("", "empty string"),
            ("   ", "whitespace only"),
            (None, "None value"),
            (123, "numeric value"),
            ("not-xpath", "plain text"),
            ("<script>", "HTML tag"),
            ("javascript:alert(1)", "javascript protocol"),
            ("eval(code)", "eval function"),
            ("//div[unclosed", "unclosed bracket"),
            ("//div)extra-paren]", "mismatched parenthesis"),
        ]

        for xpath, description in invalid_xpaths:
            logger.info(f"Testing invalid {description}: {repr(xpath)}")
            result = validate_xpath_selector(xpath)
            logger.info(f"Validation result: {result}")
            assert not result, f"Should be invalid: {xpath}"

        logger.info(f"✓ All {len(invalid_xpaths)} invalid XPath expressions correctly rejected")

    def test_xpath_balanced_brackets(self) -> None:
        """Test XPath bracket and parenthesis balancing."""
        logger.info("Testing XPath bracket and parenthesis balancing")

        # Valid balanced
        balanced_expressions = [
            ("//div[@class='test']", "attribute with brackets"),
            ("//span[contains(text(), 'hello')]", "function with nested parentheses"),
        ]

        for xpath, description in balanced_expressions:
            logger.info(f"Testing balanced {description}: '{xpath}'")
            result = validate_xpath_selector(xpath)
            assert result, f"Balanced XPath should be valid: {xpath}"

        # Invalid unbalanced
        unbalanced_expressions = [
            ("//div[@class='test'", "unclosed bracket"),
            ("//span[contains(text(), 'hello'", "unclosed nested parentheses"),
        ]

        for xpath, description in unbalanced_expressions:
            logger.info(f"Testing unbalanced {description}: '{xpath}'")
            result = validate_xpath_selector(xpath)
            assert not result, f"Unbalanced XPath should be invalid: {xpath}"

        logger.info("✓ XPath bracket balancing validation test passed")


class TestGenericSelectorValidation:
    """Test generic selector validation."""

    def test_css_or_xpath_validation(self) -> None:
        """Test validation accepts both CSS and XPath."""
        logger.info("Testing generic selector validation for both CSS and XPath")

        # CSS selectors
        css_selectors = [
            ("#button", "CSS ID selector"),
            (".class-name", "CSS class selector"),
            ("div > p", "CSS combinator"),
        ]

        for selector, description in css_selectors:
            logger.info(f"Testing {description}: '{selector}'")
            result = validate_selector(selector)
            assert result, f"CSS selector should be valid: {selector}"

        # XPath selectors
        xpath_selectors = [
            ("//div[@id='test']", "XPath attribute selector"),
            ("/html/body/div[1]", "XPath absolute path"),
            (".//relative", "XPath relative path"),
        ]

        for selector, description in xpath_selectors:
            logger.info(f"Testing {description}: '{selector}'")
            result = validate_selector(selector)
            assert result, f"XPath selector should be valid: {selector}"

        # Invalid selectors
        invalid_selectors = [
            ("", "empty string"),
            ("<script>", "HTML tag"),
            ("javascript:alert(1)", "javascript protocol"),
        ]

        for selector, description in invalid_selectors:
            logger.info(f"Testing invalid {description}: '{selector}'")
            result = validate_selector(selector)
            assert not result, f"Should be invalid: {selector}"

        logger.info("✓ Generic selector validation test passed")


class TestURLValidation:
    """Test URL validation and sanitization."""

    def test_sanitize_url(self) -> None:
        """Test URL sanitization."""
        logger.info("Testing URL sanitization functionality")

        sanitization_cases = [
            ("example.com", "https://example.com", "bare domain"),
            ("www.test.org", "https://www.test.org", "www subdomain"),
            ("http://example.com", "http://example.com", "existing http scheme"),
            ("https://secure.com", "https://secure.com", "existing https scheme"),
            ("  https://example.com  ", "https://example.com", "whitespace trimming"),
            ("", "", "empty string"),
            ("   ", "", "whitespace only"),
        ]

        for input_url, expected, description in sanitization_cases:
            logger.info(f"Sanitizing {description}: '{input_url}' -> '{expected}'")
            result = sanitize_url(input_url)
            logger.info(f"Sanitization result: '{result}'")
            assert result == expected

        # Test None input
        logger.info("Testing None input handling")
        result = sanitize_url(None)
        logger.info(f"None input result: '{result}'")
        assert result == ""

        logger.info("✓ URL sanitization test passed")

    def test_validate_url(self) -> None:
        """Test URL validation."""
        logger.info("Testing URL validation with valid URLs")

        # Valid URLs
        valid_urls = [
            ("https://example.com", "basic HTTPS URL"),
            ("http://localhost", "localhost HTTP"),
            ("https://subdomain.example.com/path?query=value", "complex URL with path and query"),
            ("http://192.168.1.1:8080", "IP address with port"),
            ("ftp://files.example.com", "FTP protocol"),
            ("file:///local/path", "file protocol"),
        ]

        for url, description in valid_urls:
            logger.info(f"Validating {description}: '{url}'")
            result = validate_url(url)
            logger.info(f"Validation result: {result}")
            assert result, f"Should be valid: {url}"

        logger.info("Testing URL validation with invalid URLs")

        # Invalid URLs
        invalid_urls = [
            ("", "empty string"),
            ("not-a-url", "plain text"),
            ("javascript:alert(1)", "javascript protocol"),
            ("data:text/html,<script>alert(1)</script>", "data protocol"),
            ("https://", "missing netloc"),
            ("://example.com", "missing scheme"),
            ("example.com", "missing scheme"),
        ]

        for url, description in invalid_urls:
            logger.info(f"Testing invalid {description}: '{url}'")
            result = validate_url(url)
            logger.info(f"Validation result: {result}")
            assert not result, f"Should be invalid: {url}"

        logger.info("✓ URL validation test passed")

    def test_validate_url_special_hosts(self) -> None:
        """Test URL validation for special hosts."""
        logger.info("Testing URL validation for special host cases")

        # Special hosts that don't need dots
        special_hosts = [
            ("http://localhost", "localhost"),
            ("http://127.0.0.1", "loopback IP"),
            ("https://0.0.0.0:8000", "wildcard IP with port"),
        ]

        for url, description in special_hosts:
            logger.info(f"Testing special host {description}: '{url}'")
            result = validate_url(url)
            assert result, f"Special host should be valid: {url}"

        # Regular domains need dots
        logger.info("Testing single domain validation (should fail)")
        result = validate_url("http://singledomain")
        logger.info(f"Single domain result: {result}")
        assert not result, "Single domain without dot should be invalid"

        logger.info("✓ Special host validation test passed")


class TestSessionIdValidation:
    """Test session ID validation."""

    def test_valid_session_ids(self) -> None:
        """Test valid session ID formats."""
        logger.info("Testing session ID validation with valid formats")

        valid_ids = [
            ("session-123", "hyphenated format"),
            ("abc_def_456", "underscored format"),
            ("test.session.id", "dotted format"),
            ("SESSION-ID-123", "uppercase format"),
            ("s123", "short format"),
            ("very-long-session-id-with-many-characters-but-still-valid", "long format"),
        ]

        for session_id, description in valid_ids:
            logger.info(f"Validating {description}: '{session_id}'")
            result = validate_session_id(session_id)
            logger.info(f"Validation result: {result}")
            assert result, f"Should be valid: {session_id}"

        logger.info(f"✓ All {len(valid_ids)} valid session IDs passed validation")

    def test_invalid_session_ids(self) -> None:
        """Test invalid session ID formats."""
        logger.info("Testing session ID validation with invalid formats")

        invalid_ids = [
            ("", "empty string"),
            ("   ", "whitespace only"),
            (None, "None value"),
            (123, "numeric value"),
            ("ab", "too short"),
            ("a" * 101, "too long"),
            ("session id", "space not allowed"),
            ("session@id", "@ not allowed"),
            ("session#id", "# not allowed"),
            ("session/id", "/ not allowed"),
        ]

        for session_id, description in invalid_ids:
            logger.info(f"Testing invalid {description}: {repr(session_id)}")
            result = validate_session_id(session_id)
            logger.info(f"Validation result: {result}")
            assert not result, f"Should be invalid: {session_id}"

        logger.info(f"✓ All {len(invalid_ids)} invalid session IDs correctly rejected")


class TestTimeoutValidation:
    """Test timeout value validation."""

    def test_valid_timeouts(self) -> None:
        """Test valid timeout values."""
        logger.info("Testing timeout validation with valid values")

        valid_timeouts = [
            (1, "minimum value"),
            (1.0, "float minimum"),
            (30, "typical value"),
            (30.5, "float typical"),
            (60, "one minute"),
            (120.75, "float minutes"),
            (300, "5 minutes - upper bound"),
        ]

        for timeout, description in valid_timeouts:
            logger.info(f"Validating {description}: {timeout}")
            result = validate_timeout(timeout)
            logger.info(f"Validation result: {result}")
            assert result, f"Should be valid: {timeout}"

        logger.info(f"✓ All {len(valid_timeouts)} valid timeouts passed validation")

    def test_invalid_timeouts(self) -> None:
        """Test invalid timeout values."""
        logger.info("Testing timeout validation with invalid values")

        invalid_timeouts = [
            (0, "zero value"),
            (-1, "negative integer"),
            (-30.5, "negative float"),
            (301, "over 5 minutes"),
            (500, "way too large"),
            ("30", "string not allowed"),
            (None, "None value"),
        ]

        for timeout, description in invalid_timeouts:
            logger.info(f"Testing invalid {description}: {repr(timeout)}")
            result = validate_timeout(timeout)
            logger.info(f"Validation result: {result}")
            assert not result, f"Should be invalid: {timeout}"

        logger.info(f"✓ All {len(invalid_timeouts)} invalid timeouts correctly rejected")


class TestElementTextSanitization:
    """Test element text sanitization."""

    def test_sanitize_element_text(self) -> None:
        """Test element text sanitization."""
        logger.info("Testing element text sanitization functionality")

        # Remove HTML tags
        html_cases = [
            ("<div>Hello</div>", "Hello", "simple div"),
            ("<script>alert(1)</script>Test", "alert(1)Test", "script tag removal"),
        ]

        for input_text, expected, description in html_cases:
            logger.info(f"Sanitizing {description}: '{input_text}' -> '{expected}'")
            result = sanitize_element_text(input_text)
            logger.info(f"Sanitization result: '{result}'")
            assert result == expected

        # Normalize whitespace
        whitespace_cases = [
            ("  Hello\n\tWorld  ", "Hello World", "mixed whitespace"),
            ("Line1\n\nLine2", "Line1 Line2", "multiple newlines"),
        ]

        for input_text, expected, description in whitespace_cases:
            logger.info(f"Normalizing {description}: '{input_text}' -> '{expected}'")
            result = sanitize_element_text(input_text)
            logger.info(f"Normalization result: '{result}'")
            assert result == expected

        # Handle empty/invalid input
        empty_cases = [("", "", "empty string"), ("   ", "", "whitespace only"), (None, "", "None value")]

        for input_text, expected, description in empty_cases:
            logger.info(f"Handling {description}: {repr(input_text)}")
            result = sanitize_element_text(input_text)
            logger.info(f"Result: '{result}'")
            assert result == expected

        # Test length limit
        logger.info("Testing text length limiting")
        long_text = "a" * 1500
        result = sanitize_element_text(long_text)
        logger.info(f"Long text (1500 chars) -> {len(result)} chars")
        assert len(result) <= 1000
        assert result.endswith("...")

        logger.info("✓ Element text sanitization test passed")

    def test_sanitize_preserves_content(self) -> None:
        """Test sanitization preserves meaningful content."""
        logger.info("Testing that sanitization preserves meaningful content")

        # Should preserve normal text
        normal_cases = [("Button Text", "simple text"), ("Click here to continue", "call to action text")]

        for text, description in normal_cases:
            logger.info(f"Preserving {description}: '{text}'")
            result = sanitize_element_text(text)
            logger.info(f"Preserved result: '{result}'")
            assert result == text

        # Should handle mixed content
        mixed_case = "<div>Welcome <strong>user</strong>!</div>"
        expected = "Welcome user!"
        logger.info(f"Handling mixed HTML: '{mixed_case}'")
        result = sanitize_element_text(mixed_case)
        logger.info(f"Mixed content result: '{result}'")
        assert result == expected

        logger.info("✓ Content preservation test passed")


class TestActionTypeValidation:
    """Test action type validation."""

    def test_valid_action_types(self) -> None:
        """Test valid browser action types."""
        logger.info("Testing action type validation with valid browser actions")

        valid_actions = [
            "click",
            "double_click",
            "right_click",
            "hover",
            "fill",
            "clear",
            "select",
            "check",
            "uncheck",
            "focus",
            "blur",
            "scroll",
            "drag",
            "drop",
            "navigate",
            "reload",
            "back",
            "forward",
            "wait",
            "screenshot",
        ]

        for action in valid_actions:
            logger.info(f"Validating action: '{action}'")
            result = validate_action_type(action)
            logger.info(f"Validation result: {result}")
            assert result, f"Should be valid: {action}"

        logger.info(f"✓ All {len(valid_actions)} valid actions passed validation")

    def test_case_insensitive_actions(self) -> None:
        """Test action validation is case insensitive."""
        logger.info("Testing case insensitive action validation")

        case_variants = [
            ("CLICK", "uppercase"),
            ("Click", "title case"),
            ("cLiCk", "mixed case"),
            ("  hover  ", "with whitespace"),
        ]

        for action, description in case_variants:
            logger.info(f"Testing {description}: '{action}'")
            result = validate_action_type(action)
            logger.info(f"Case insensitive result: {result}")
            assert result

        logger.info("✓ Case insensitive validation test passed")

    def test_invalid_action_types(self) -> None:
        """Test invalid action types."""
        logger.info("Testing action type validation with invalid actions")

        invalid_actions = [
            ("", "empty string"),
            ("   ", "whitespace only"),
            (None, "None value"),
            (123, "numeric value"),
            ("invalid_action", "unknown action"),
            ("execute_script", "not a basic browser action"),
            ("javascript", "script execution"),
            ("custom_action", "custom action"),
        ]

        for action, description in invalid_actions:
            logger.info(f"Testing invalid {description}: {repr(action)}")
            result = validate_action_type(action)
            logger.info(f"Validation result: {result}")
            assert not result, f"Should be invalid: {action}"

        logger.info(f"✓ All {len(invalid_actions)} invalid actions correctly rejected")


class TestValidationIntegration:
    """Test validation utilities integration scenarios."""

    def test_selector_validation_comprehensive(self) -> None:
        """Test comprehensive selector validation scenarios."""
        logger.info("Testing comprehensive real-world selector validation")

        # Real-world selectors that should work
        real_selectors = [
            ('input[name="username"]', "form input selector"),
            ("#main-content .article-title", "ID and class combination"),
            ("div.container > ul.nav-menu li:nth-child(2) a", "complex CSS chain"),
            ('//div[@class="content"]//a[contains(text(), "Next")]', "XPath with text"),
            ('button[data-testid="submit-button"]', "test attribute selector"),
            (".sidebar .widget:last-of-type h3", "pseudo-selector"),
        ]

        for selector, description in real_selectors:
            logger.info(f"Testing {description}: '{selector}'")
            result = validate_selector(selector)
            logger.info(f"Real-world validation result: {result}")
            assert result, f"Real-world selector failed: {selector}"

        logger.info("✓ Real-world selector validation test passed")

    def test_url_validation_comprehensive(self) -> None:
        """Test comprehensive URL validation scenarios."""
        logger.info("Testing comprehensive real-world URL validation")

        # Real-world URLs
        real_urls = [
            ("https://www.example.com/path/to/page?param=value&other=123", "complex URL"),
            ("http://localhost:3000/api/v1/users", "localhost API"),
            ("https://subdomain.example.co.uk/complex-path_with-underscores", "UK domain"),
            ("http://192.168.0.1:8080/admin/dashboard", "IP with path"),
            ("https://example.com:443/secure/page#section", "with fragment"),
        ]

        for url, description in real_urls:
            logger.info(f"Testing {description}: '{url}'")
            result = validate_url(url)
            logger.info(f"Real-world URL result: {result}")
            assert result, f"Real-world URL failed: {url}"

        logger.info("✓ Real-world URL validation test passed")

    def test_combined_validation_workflow(self) -> None:
        """Test typical validation workflow for PageBase."""
        logger.info("Testing combined validation workflow simulation")

        # Simulate PageBase validation needs
        validation_data = {
            "session_id": "browser-session-12345",
            "url": "https://example.com/login",
            "selector": "#username-input",
            "timeout": 30.0,
            "action": "fill",
        }

        logger.info(f"Validating workflow data: {validation_data}")

        # All should validate successfully
        validations = [
            (validate_session_id(validation_data["session_id"]), "session_id"),
            (validate_url(validation_data["url"]), "url"),
            (validate_selector(validation_data["selector"]), "selector"),
            (validate_timeout(validation_data["timeout"]), "timeout"),
            (validate_action_type(validation_data["action"]), "action"),
        ]

        for result, field in validations:
            logger.info(f"Validation {field}: {result}")
            assert result, f"Workflow validation failed for {field}"

        # Test sanitization
        logger.info("Testing URL sanitization in workflow")
        raw_url = "example.com/login"
        sanitized_url = sanitize_url(raw_url)
        logger.info(f"Sanitized URL: '{raw_url}' -> '{sanitized_url}'")
        assert validate_url(sanitized_url)

        # Test text sanitization
        logger.info("Testing text sanitization in workflow")
        element_text = "<span>Username field</span>"
        clean_text = sanitize_element_text(element_text)
        logger.info(f"Sanitized text: '{element_text}' -> '{clean_text}'")
        assert clean_text == "Username field"

        logger.info("✓ Combined validation workflow test passed")
