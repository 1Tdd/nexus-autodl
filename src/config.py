"""
src/config.py - The Knobs and Dials

Look, if you're reading this you probably want to tweak something.
Fair enough. But don't come crying when you crank everything to 11
and get throttled/banned/flagged. You've been warned.

Defaults are sane. Don't touch unless you know what you're doing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Optional

import yaml


# ═══════════════════════════════════════════════════════════════════════════════
# MOUSE MOVEMENT - aka "Don't Move Like a Robot"
# ═══════════════════════════════════════════════════════════════════════════════
#
# Bots die because they move in straight lines at constant speed.
# Humans are sloppy, shaky, and overshoot targets. Embrace the chaos.
#

@dataclass
class MouseConfig:
    # Mouse movement config - don't mess with these unless you know what you're doing
    
    # How many points on the bezier curve. More = smoother but slower.
    # 50 is smooth enough. Drop to 30 if you're impatient.
    curve_resolution: int = 50
    
    # Speed multiplier. 1.0 = normal. 0.5 = grandma mode. 1.5 = twitchy.
    # Stay under 1.2 unless you want to look like you've had 8 espressos.
    speed_factor: float = 1.0
    
    # Overshoot: sometimes "miss" the target and correct back.
    # Real humans do this constantly. Disabling = instant red flag.
    overshoot_enabled: bool = True
    overshoot_probability: float = 0.25  # 25% chance per click
    overshoot_distance: Tuple[int, int] = (3, 10)  # pixels past target
    overshoot_delay_ms: int = 50  # pause before correction
    
    # Jitter: tiny random wobbles simulating hand tremor.
    # Not coffee jitters - more like "I'm a human holding a mouse" jitters.
    jitter_enabled: bool = True
    jitter_amplitude: float = 1.2  # pixels of shake
    jitter_frequency: float = 0.30  # 30% of movements get the shake
    
    # Click offset: like throwing darts - most land near bullseye,
    # but some drift toward the edges. Perfect bullseyes = bot behavior.
    click_offset_enabled: bool = True
    click_offset_ratio: float = 0.30  # Max offset (0.30 = up to 30% from center)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE MATCHING - Vision System Tuning
# ═══════════════════════════════════════════════════════════════════════════════
#
# How picky the bot is about "finding" buttons. Too high = misses real buttons.
# Too low = clicks random garbage that kinda looks like buttons.
#

@dataclass
class MatchingConfig:
    # How confident the bot needs to be before clicking
    
    # Main threshold. 0.80 = "pretty sure that's the button"
    # Drop to 0.70 if it's not finding obvious buttons.
    # Raise to 0.90 if it's clicking your taskbar icons.
    confidence_threshold: float = 0.80
    
    # Marginal zone. Matches here get a warning but still proceed.
    # Below this = fallback to ORB/AKAZE feature matching (slower but robust).
    marginal_threshold: float = 0.60
    
    # Grayscale matching is faster. Color only matters if your buttons
    # are identical shapes but different colors. (They're not. Leave this on.)
    use_grayscale: bool = True
    
    # Matching strategy: how to find buttons on screen.
    # Options:
    #   "cascade"  - Try template first, then ORB, then AKAZE (default, recommended)
    #   "template" - Template correlation only (fastest, needs exact match)
    #   "orb"      - ORB features only (handles minor variations)
    #   "akaze"    - AKAZE features only (slowest, most robust)
    # Cascade is smart - it starts fast and falls back to slower methods if needed.
    strategy: str = "cascade"


# ═══════════════════════════════════════════════════════════════════════════════
# TIMING - The "Don't Get Rate-Limited" Section
# ═══════════════════════════════════════════════════════════════════════════════
#
# This is where most people get banned. They set delays to 0.1s and wonder
# why Nexus shows them the door. Randomization is your friend.
#

@dataclass 
class TimingConfig:
    # Timing delays - don't set these to zero or you'll get banned
    
    # Main loop sleep. Random between min and max.
    # 1.0-2.5s is brisk but human. Under 0.5 = sus.
    min_sleep_seconds: float = 1.0
    max_sleep_seconds: float = 2.5
    
    # After clicking Vortex button, browser needs time to open.
    # Modern browsers are fast - 3.5s is usually enough.
    vortex_launch_delay: float = 3.5
    
    # After clicking "Slow Download", wait before closing tab.
    # 1.0s is enough for the click to register.
    web_click_delay: float = 1.0
    
    # Jitter percentage. Adds +/- randomness to ALL delays.
    # 0.20 = 20% variance. Makes timing unpredictable (good).
    jitter_pct: float = 0.20
    
    # Hesitation before clicking. Humans don't click instantly.
    # They see the button, brain processes, hand moves. 50-180ms is realistic.
    hesitation_min_ms: int = 50
    hesitation_max_ms: int = 180
    
    # Template fallback: after this many cycles without ANY match on priority templates,
    # the bot will try ALL templates in the folder regardless of naming convention.
    # Set to 0 to disable (always use priority order).
    fallback_cycles: int = 4
    
    # Verification: How long to wait for "Your download has started" text
    # before giving up and closing the tab anyway.
    download_verify_timeout: float = 10.0


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY - Resolution Sanity Check
# ═══════════════════════════════════════════════════════════════════════════════
#
# Templates are resolution-specific. If you captured buttons at 1080p and
# run at 1440p, nothing will match. Bot will sit there doing nothing.
# Not a bug - it's you.
#

@dataclass
class DisplayConfig:
    # Monitor config - must match your template screenshots
    
    # Set these to YOUR resolution. The bot will yell at startup if wrong.
    expected_width: int = 1920
    expected_height: int = 1080
    # Monitor selection: 0=all, 1=primary, 2+=specific
    monitor: int = 1


# ═══════════════════════════════════════════════════════════════════════════════
# UI CONFIG - Dashboard Appearance
# ═══════════════════════════════════════════════════════════════════════════════
#
# Cosmetic stuff. Won't get you banned but might save your eyes at 2am.
#

@dataclass
class UIConfig:
    # UI settings
    
    # Night mode dimming. "always" = dark theme 24/7. "auto" = after night_mode_hour.
    # "disabled" if you hate your retinas.
    night_mode: str = "always"
    night_mode_hour: int = 20  # 8 PM, only used if night_mode == "auto"
    
    # Dashboard refresh rate. 100ms is smooth. Higher = choppier but less CPU.
    refresh_rate_ms: int = 100


# ═══════════════════════════════════════════════════════════════════════════════
# HOTKEYS - Panic Buttons
# ═══════════════════════════════════════════════════════════════════════════════
#
# When things go sideways, you'll want these memorized.
#

@dataclass
class HotkeysConfig:
    # Hotkeys - memorize these
    
    # Closes browser tab after download starts. Standard stuff.
    close_tab: str = "ctrl+w"
    
    # STOP: Nuke the whole operation. Use when things go wrong.
    stop_bot: str = "f10"
    
    # PAUSE: Take a break without killing the session.
    pause_bot: str = "f9"
    
    # RELOAD: Hot-reload config.yaml without restarting. 
    # Edit config, hit this, see changes. Magic.
    reload_bot: str = "f5"

    # STRATEGY: Cycle through matching algorithms at runtime.
    # CASCADE -> TEMPLATE -> ORB -> AKAZE -> CASCADE...
    cycle_strategy: str = "f8"

@dataclass
class ProfilesConfig:
    # Profile paths
    root_directory: str = "profiles"
    active_profile: str = ""

@dataclass
class VisualConfig:
    # Debug settings
    debug_mode: bool = False

# ═══════════════════════════════════════════════════════════════════════════════
# MASTER CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AppConfig:
    """
    Everything bundled together. Don't instantiate this manually -
    use load_config() which handles all the YAML parsing bullshit for you.
    """
    display: DisplayConfig = field(default_factory=DisplayConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    hotkeys: HotkeysConfig = field(default_factory=HotkeysConfig)
    profiles: ProfilesConfig = field(default_factory=ProfilesConfig)
    visual: VisualConfig = field(default_factory=VisualConfig)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG LOADER
# ═══════════════════════════════════════════════════════════════════════════════

def _get(data: dict, *keys, default=None):
    """Drill into nested dicts without KeyError explosions."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
        if data is None:
            return default
    return data


def load_config(path: str = "config.yaml") -> AppConfig:
    """
    Load config from YAML. Missing file = all defaults. Missing keys = defaults.
    Robust handling for partial configs.
    """
    config_path = Path(path)
    
    if not config_path.exists():
        return AppConfig()  # No config found, using defaults.
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return AppConfig()  # Malformed YAML fallback.
    
    # Build config from YAML with fallbacks
    display = DisplayConfig(
        expected_width=_get(data, "display", "expected_width", default=1920),
        expected_height=_get(data, "display", "expected_height", default=1080)
    )
    
    matching = MatchingConfig(
        confidence_threshold=_get(data, "matching", "confidence_threshold", default=0.80),
        marginal_threshold=_get(data, "matching", "marginal_threshold", default=0.60),
        use_grayscale=_get(data, "matching", "use_grayscale", default=True),
        strategy=_get(data, "matching", "strategy", default="cascade")
    )
    
    timing = TimingConfig(
        min_sleep_seconds=_get(data, "timing", "min_sleep_seconds", default=1.5),
        max_sleep_seconds=_get(data, "timing", "max_sleep_seconds", default=4.0),
        vortex_launch_delay=_get(data, "timing", "vortex_launch_delay", default=5.0),
        web_click_delay=_get(data, "timing", "web_click_delay", default=1.5),
        jitter_pct=_get(data, "timing", "jitter_pct", default=0.15),
        hesitation_min_ms=_get(data, "timing", "hesitation_min_ms", default=80),
        hesitation_max_ms=_get(data, "timing", "hesitation_max_ms", default=250),
        fallback_cycles=_get(data, "timing", "fallback_cycles", default=4),
        download_verify_timeout=_get(data, "timing", "download_verify_timeout", default=10.0)
    )
    
    overshoot = _get(data, "mouse", "overshoot", default={})
    jitter = _get(data, "mouse", "jitter", default={})
    click_offset = _get(data, "mouse", "click_offset", default={})
    
    mouse = MouseConfig(
        curve_resolution=_get(data, "mouse", "curve_resolution", default=60),
        speed_factor=_get(data, "mouse", "speed_factor", default=0.9),
        overshoot_enabled=overshoot.get("enabled", True),
        overshoot_probability=overshoot.get("probability", 0.20),
        overshoot_distance=(
            overshoot.get("distance_min_px", 4),
            overshoot.get("distance_max_px", 12)
        ),
        overshoot_delay_ms=overshoot.get("correction_delay_ms", 60),
        jitter_enabled=jitter.get("enabled", True),
        jitter_amplitude=jitter.get("amplitude_px", 1.5),
        jitter_frequency=jitter.get("frequency", 0.25),
        click_offset_enabled=click_offset.get("enabled", True),
        click_offset_ratio=click_offset.get("ratio", 0.35)
    )
    
    ui = UIConfig(
        night_mode=_get(data, "ui", "night_mode", default="always"),
        night_mode_hour=_get(data, "ui", "night_mode_start_hour", default=20),
        refresh_rate_ms=_get(data, "ui", "refresh_rate_ms", default=100)
    )
    
    hotkeys = HotkeysConfig(
        close_tab=_get(data, "hotkeys", "close_tab", default="ctrl+w"),
        stop_bot=_get(data, "hotkeys", "stop_bot", default="f10"),
        pause_bot=_get(data, "hotkeys", "pause_bot", default="f9"),
        reload_bot=_get(data, "hotkeys", "reload_bot", default="f5"),
        cycle_strategy=_get(data, "hotkeys", "cycle_strategy", default="f8")
    )
    
    return AppConfig(
        display=display,
        matching=matching,
        timing=timing,
        mouse=mouse,
        ui=ui,
        hotkeys=hotkeys,
        profiles=ProfilesConfig(
            root_directory=_get(data, "profiles", "profiles_dir", default="profiles"),
            active_profile=_get(data, "profiles", "active_profile", default="")
        ),
        visual=VisualConfig(
            debug_mode=_get(data, "visual", "debug_mode", default=False)
        )
    )
