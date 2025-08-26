# File: /src/browserve/core/__init__.py
"""
Core Browserve components for page interaction, session management, and logging.
"""

from __future__ import annotations

from .page import PageBase
from .logger import BrowserLogger

__all__ = ["PageBase", "BrowserLogger"]
