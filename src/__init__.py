# src package - vision, input, ui, config

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
