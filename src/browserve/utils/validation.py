"""
Validation utilities for selectors and URLs.

Provides validation functions for CSS selectors, XPath expressions,
and URLs to ensure safe browser automation operations.
"""
from __future__ import annotations
import re
from typing import Union
from urllib.parse import urlparse


def validate_css_selector(selector: str) -> bool:
    """
    Validate CSS selector syntax for basic safety.
    
    Performs basic validation to catch obviously malformed selectors
    and potential security issues. This is not a full CSS grammar
    validator but catches common problems.
    
    Args:
        selector: CSS selector string to validate
        
    Returns:
        True if selector appears valid, False otherwise
        
    Example:
        >>> validate_css_selector("#my-button")
        True
        >>> validate_css_selector("div.class[attr='value']")
        True
        >>> validate_css_selector("<script>")
        False
    """
    if not selector or not isinstance(selector, str):
        return False
    
    # Remove whitespace for validation
    selector = selector.strip()
    if not selector:
        return False
    
    # Check for obviously dangerous content
    forbidden_chars = ['<', '>', '"', "'", '`']
    if any(char in selector for char in forbidden_chars):
        return False
    
    # Check for script-like content
    dangerous_patterns = [
        'javascript:', 'data:', 'vbscript:', 'expression(',
        'eval(', 'setTimeout', 'setInterval'
    ]
    selector_lower = selector.lower()
    if any(pattern in selector_lower for pattern in dangerous_patterns):
        return False
    
    # Basic CSS selector pattern validation
    # Matches basic CSS selector patterns: #id, .class, tag, [attr], etc.
    css_pattern = r'^[a-zA-Z0-9\-_#.\[\]=:(),"\'*+~^$|>\s]+$'
    if not re.match(css_pattern, selector):
        return False
    
    # Check for balanced brackets
    brackets = {'[': ']', '(': ')'}
    stack = []
    
    for char in selector:
        if char in brackets:
            stack.append(brackets[char])
        elif char in brackets.values():
            if not stack or stack.pop() != char:
                return False
    
    # All brackets should be closed
    return len(stack) == 0


def validate_xpath_selector(selector: str) -> bool:
    """
    Validate XPath selector syntax for basic safety.
    
    Performs basic validation to identify XPath expressions and check
    for obvious syntax errors and security issues.
    
    Args:
        selector: XPath selector string to validate
        
    Returns:
        True if selector appears to be valid XPath, False otherwise
        
    Example:
        >>> validate_xpath_selector("//div[@id='content']")
        True
        >>> validate_xpath_selector("/html/body/div[1]")
        True
        >>> validate_xpath_selector("invalid xpath")
        False
    """
    if not selector or not isinstance(selector, str):
        return False
    
    selector = selector.strip()
    if not selector:
        return False
    
    # Check for dangerous content
    forbidden_chars = ['<', '>']
    if any(char in selector for char in forbidden_chars):
        return False
    
    # Check for script-like content
    dangerous_patterns = [
        'javascript:', 'data:', 'vbscript:', 'expression(',
        'eval(', 'setTimeout', 'setInterval'
    ]
    selector_lower = selector.lower()
    if any(pattern in selector_lower for pattern in dangerous_patterns):
        return False
    
    # Basic XPath patterns
    xpath_starts = [
        '/', '//', './', '../', '.', '(',
        'id(', 'name(', 'class(', 'text()', 'contains(',
        'starts-with(', 'normalize-space(', 'following:',
        'preceding:', 'ancestor:', 'descendant:', 'child:',
        'parent:', 'self:'
    ]
    
    # Check if it looks like XPath
    if not any(selector.startswith(start) for start in xpath_starts):
        # Also check for xpath-like content anywhere in string
        xpath_indicators = ['//', '[@', '[contains(', '[text()', 'following::', 'preceding::']
        if not any(indicator in selector for indicator in xpath_indicators):
            return False
    
    # Basic XPath character validation
    # Allow common XPath characters and functions
    xpath_pattern = r'^[a-zA-Z0-9\-_\[\]@=():,."\'*/+\s\\|]+$'
    if not re.match(xpath_pattern, selector):
        return False
    
    # Check for balanced brackets and parentheses
    brackets = {'[': ']', '(': ')'}
    stack = []
    
    for char in selector:
        if char in brackets:
            stack.append(brackets[char])
        elif char in brackets.values():
            if not stack or stack.pop() != char:
                return False
    
    return len(stack) == 0


def validate_selector(selector: str) -> bool:
    """
    Validate either CSS or XPath selector.
    
    Attempts to validate the selector as either CSS or XPath,
    returning True if it appears valid as either format.
    
    Args:
        selector: Selector string to validate
        
    Returns:
        True if selector is valid CSS or XPath, False otherwise
        
    Example:
        >>> validate_selector("#button")  # CSS
        True
        >>> validate_selector("//div[@class='content']")  # XPath
        True
        >>> validate_selector("<invalid>")
        False
    """
    if not selector or not isinstance(selector, str):
        return False
    
    # Try CSS first (more common)
    if validate_css_selector(selector):
        return True
    
    # Try XPath
    return validate_xpath_selector(selector)


def sanitize_url(url: str) -> str:
    """
    Sanitize URL for safe usage.
    
    Normalizes URL format by adding https:// scheme if missing
    and removing extra whitespace. Does not perform full validation.
    
    Args:
        url: URL string to sanitize
        
    Returns:
        Sanitized URL string
        
    Example:
        >>> sanitize_url("example.com")
        'https://example.com'
        >>> sanitize_url("  http://test.com  ")
        'http://test.com'
    """
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip()
    
    if not url:
        return ""
    
    # Add https if no scheme present
    if not url.startswith(('http://', 'https://', 'ftp://', 'file://')):
        url = 'https://' + url
    
    return url


def validate_url(url: str) -> bool:
    """
    Validate URL format and components.
    
    Checks if URL has proper scheme, netloc, and basic structure.
    More comprehensive than basic URL parsing.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
        
    Example:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("http://localhost:8080/path?param=value")
        True
        >>> validate_url("invalid-url")
        False
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        
        # Must have scheme
        if not parsed.scheme:
            return False
        
        # Must have network location (domain/host)
        if not parsed.netloc:
            return False
        
        # Only allow safe schemes
        allowed_schemes = {'http', 'https', 'ftp', 'file'}
        if parsed.scheme.lower() not in allowed_schemes:
            return False
        
        # Check for basic domain format (at least one dot for non-localhost)
        netloc = parsed.netloc.lower()
        if netloc not in ('localhost', '127.0.0.1', '0.0.0.0'):
            if '.' not in netloc and ':' not in netloc:
                return False
        
        return True
        
    except Exception:
        return False


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format.
    
    Checks if session ID contains only safe characters and
    has reasonable length for session identification.
    
    Args:
        session_id: Session identifier to validate
        
    Returns:
        True if session ID is valid, False otherwise
        
    Example:
        >>> validate_session_id("session-123")
        True
        >>> validate_session_id("abc_def_456")
        True
        >>> validate_session_id("")
        False
    """
    if not session_id or not isinstance(session_id, str):
        return False
    
    session_id = session_id.strip()
    
    if not session_id:
        return False
    
    # Check length (reasonable bounds)
    if len(session_id) < 3 or len(session_id) > 100:
        return False
    
    # Only allow alphanumeric, hyphens, underscores, and dots
    allowed_pattern = r'^[a-zA-Z0-9\-_.]+$'
    return bool(re.match(allowed_pattern, session_id))


def validate_timeout(timeout: Union[int, float]) -> bool:
    """
    Validate timeout value.
    
    Checks if timeout is a reasonable positive number
    within acceptable bounds for browser operations.
    
    Args:
        timeout: Timeout value in seconds
        
    Returns:
        True if timeout is valid, False otherwise
        
    Example:
        >>> validate_timeout(30.0)
        True
        >>> validate_timeout(-5)
        False
        >>> validate_timeout(500)
        False
    """
    if not isinstance(timeout, (int, float)):
        return False
    
    # Must be positive
    if timeout <= 0:
        return False
    
    # Reasonable upper bound (5 minutes)
    if timeout > 300:
        return False
    
    return True


def sanitize_element_text(text: str) -> str:
    """
    Sanitize element text content for safe logging.
    
    Removes potentially dangerous content and normalizes
    whitespace while preserving readability.
    
    Args:
        text: Raw text content from element
        
    Returns:
        Sanitized text string
        
    Example:
        >>> sanitize_element_text("  Hello\\nWorld  ")
        'Hello World'
        >>> sanitize_element_text("<script>alert('xss')</script>")
        'alert('xss')'
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Trim
    text = text.strip()
    
    # Limit length for logging (prevent huge text dumps)
    if len(text) > 1000:
        text = text[:997] + "..."
    
    return text


def validate_action_type(action_type: str) -> bool:
    """
    Validate action type string.
    
    Checks if action type is a known, safe browser action.
    
    Args:
        action_type: Action type identifier
        
    Returns:
        True if action type is valid, False otherwise
        
    Example:
        >>> validate_action_type("click")
        True
        >>> validate_action_type("navigate")
        True
        >>> validate_action_type("invalid_action")
        False
    """
    if not action_type or not isinstance(action_type, str):
        return False
    
    valid_actions = {
        'click', 'double_click', 'right_click', 'hover', 'fill', 
        'clear', 'select', 'check', 'uncheck', 'focus', 'blur',
        'scroll', 'drag', 'drop', 'navigate', 'reload', 'back', 
        'forward', 'wait', 'screenshot'
    }
    
    return action_type.lower().strip() in valid_actions
