"""
Action framework for validated browser automation.

Provides base PlaywrightAction class and concrete action implementations
for building composable browser automation workflows.
"""

from __future__ import annotations

from .base import (
    PlaywrightAction,
    ComposedAction,
    ConditionalAction,
)
from .interaction import (
    ClickAction,
    FillAction,
    NavigationAction,
    WaitAction,
    HoverAction,
    ScrollAction,
)

__all__ = [
    # Base action framework
    "PlaywrightAction",
    "ComposedAction",
    "ConditionalAction",
    # Concrete action implementations
    "ClickAction",
    "FillAction",
    "NavigationAction",
    "WaitAction",
    "HoverAction",
    "ScrollAction",
]
