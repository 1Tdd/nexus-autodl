# src package - vision, input, ui, config

from .vision import ScreenCapture, TemplateMatcher, MatchResult
from .human_input import HumanMouse, Point
from .ui import Dashboard, Stats, make_logger, VERSION
from .config import AppConfig, load_config

__all__ = [
    "VERSION",
    "ScreenCapture", "TemplateMatcher", "MatchResult",
    "HumanMouse", "Point",
    "Dashboard", "Stats", "make_logger",
    "AppConfig", "load_config"
]
