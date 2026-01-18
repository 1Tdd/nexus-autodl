"""
src package - Clean modular architecture

vision.py      - Screen capture (mss) and template matching (ORB/AKAZE)
human_input.py - Bézier curve mouse movement with overshoot
ui.py          - Rich terminal dashboard
config.py      - Typed configuration dataclasses
"""

from .vision import ScreenCapture, TemplateMatcher, MatchResult, check_resolution
from .human_input import HumanMouse, Point
from .ui import Dashboard, Stats, make_logger
from .config import AppConfig, load_config

__all__ = [
    "ScreenCapture", "TemplateMatcher", "MatchResult", "check_resolution",
    "HumanMouse", "Point",
    "Dashboard", "Stats", "make_logger",
    "AppConfig", "load_config"
]
