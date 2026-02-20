# Nexus-AutoDL - Bot for clicking download buttons
# Because manually downloading 300 mods is for masochists

import re
import time
import random
import sys
import keyboard
import pyautogui
import cv2  # OpenCV
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Any

# Local imports
from src import AppConfig, load_config
from src.vision import ScreenCapture, TemplateMatcher
from src.human_input import HumanMouse
from src.ui import Dashboard, make_logger

# Configuration

DEFAULT_CONFIG = """
# Nexus-AutoDL Configuration

profiles:
  active_profile: "" # Set on first run
  profiles_dir: "profiles"

display:
  expected_width: 1920
  expected_height: 1080
  monitor: 1  # 0=all, 1=primary, 2+=specific

hotkeys:
  pause_bot: "f9"
  stop_bot: "f10"
  reload_bot: "f5"
  cycle_strategy: "f8"
  close_tab: "ctrl+w"

timing:
  min_sleep_seconds: 1.0
  max_sleep_seconds: 2.5
  vortex_launch_delay: 3.5
  web_click_delay: 1.0
  jitter_pct: 0.20
  hesitation_min_ms: 50
  hesitation_max_ms: 180
  fallback_cycles: 4
  download_verify_timeout: 10.0

mouse:
  speed_factor: 1.0
  curve_resolution: 60
  overshoot:
    enabled: true
    probability: 0.20
    distance_min_px: 4
    distance_max_px: 12
    correction_delay_ms: 60
  jitter:
    enabled: true
    amplitude_px: 1.5
    frequency: 0.25
  click_offset:
    enabled: true
    ratio: 0.35

matching:
  confidence_threshold: 0.75
  marginal_threshold: 0.55
  use_grayscale: true
  strategy: "cascade"  # cascade, template, orb, akaze

visual:
  debug_mode: false

ui:
  refresh_rate_ms: 100
  night_mode_hour: 19
"""


# Small visual delay between template scans so the dashboard shows progress
SCAN_VISUAL_DELAY = 0.02

class NexusBot:
    # Main bot class - handles all the clicking and scanning
    
    def __init__(self):
        # State Flags
        self.running: bool = True
        self.paused: bool = True # Start paused as requested
        self.reload_requested: bool = False
        self.cycle_requested: bool = False
        
        # Runtime State
        self.profile: str = ""
        self.templates: Dict[str, np.ndarray] = {}
        self.last_pause_state: bool = True  # Matches paused=True initial state
        self.expecting_web: bool = False
        self.no_match_streak: int = 0
        
        # Components (Lazy loaded)
        self.cfg: Optional[AppConfig] = None
        self.dash: Optional[Dashboard] = None
        self.log = lambda m, l: None  # Dummy logger until init
        self.screen: Optional[ScreenCapture] = None
        self.matcher: Optional[TemplateMatcher] = None
        self.mouse: Optional[HumanMouse] = None

    def bootstrap(self):
        # Set up config, UI, and all the core systems
        # 1. Config First
        if not Path("config.yaml").exists():
            with open("config.yaml", "w") as f:
                f.write(DEFAULT_CONFIG.strip())
        
        try:
            self.cfg = load_config()
        except Exception as e:
            print(f"CRITICAL: Config failed to load: {e}")
            sys.exit(1)

        # 2. Profile Auto-Correction (includes monitor setup in wizard)
        self._ensure_profile()
        
        # 3. UI
        self._init_ui()
        
        # 4. Core Systems
        self.screen = ScreenCapture(monitor_index=self.cfg.display.monitor)
        self._reload_systems(initial=True)
        
        # 5. Hotkeys
        self._bind_hotkeys()
        
        self.log(f"Bot initialized. Profile: {self.profile}", "SUCCESS")
        self.log(f"READY. Press {self.cfg.hotkeys.pause_bot.upper()} to START.", "WARN")

    def _bind_hotkeys(self):
        # Register keyboard shortcuts for controlling the bot
        keyboard.add_hotkey(self.cfg.hotkeys.pause_bot, self._toggle_pause)
        keyboard.add_hotkey(self.cfg.hotkeys.stop_bot, self._stop)
        keyboard.add_hotkey(self.cfg.hotkeys.reload_bot, self._request_reload)
        keyboard.add_hotkey(self.cfg.hotkeys.cycle_strategy, self._request_cycle)

    def _toggle_pause(self):
        self.paused = not self.paused

    def _stop(self):
        self.running = False

    def _request_reload(self):
        self.reload_requested = True

    def _request_cycle(self):
        self.cycle_requested = True

    def _ensure_profile(self):
        # Make sure we have a valid profile selected
        # If not, run the interactive setup wizard
        profiles_dir = Path("profiles")
        profiles_dir.mkdir(exist_ok=True)
        
        # 1. Validate current setting
        if self.cfg.profiles.active_profile:
            current = profiles_dir / self.cfg.profiles.active_profile
            if current.exists() and current.is_dir():
                self.profile = self.cfg.profiles.active_profile
                return

        # 2. Setup Wizard
        print("\n" + "═"*60)
        print(" WELCOME TO NEXUS-AUTODL SETUP")
        print("═"*60)
        print("Let's detect your monitors and get you configured...\n")
        
        # Step 1: Monitor Detection & Selection
        print("─"*60)
        print(" STEP 1: MONITOR SETUP")
        print("─"*60)
        
        temp_screen = ScreenCapture()
        monitors = temp_screen.list_monitors()
        
        if len(monitors) > 2:  # Multi-monitor setup
            print("Detected multiple monitors:")
            print(f"  0. All monitors (virtual screen {monitors[0]['width']}x{monitors[0]['height']})")
            for i in range(1, len(monitors)):
                m = monitors[i]
                print(f"  {i}. Monitor {i} ({m['width']}x{m['height']}) [may be DPI-scaled]")
            
            while True:
                try:
                    s = input(f"\nSelect Monitor (0-{len(monitors)-1}, default=1): ").strip()
                    if not s:
                        monitor_choice = 1
                        break
                    monitor_choice = int(s)
                    if 0 <= monitor_choice < len(monitors):
                        break
                    print(f"Please enter a number between 0 and {len(monitors)-1}")
                except ValueError:
                    print("Please enter a valid number")
            
            self.cfg.display.monitor = monitor_choice
            print(f">> Selected Monitor: {monitor_choice}")
        else:
            # Single monitor - auto-select
            monitor_choice = 1
            self.cfg.display.monitor = 1
            m = monitors[1]
            print(f"Single monitor detected: {m['width']}x{m['height']}")
            print(">> Using Monitor 1 [OK]")
        
        # Step 2: Resolution Validation (for the selected monitor)
        if monitor_choice > 0:  # Specific monitor (not "all monitors")
            selected_mon = monitors[monitor_choice]
            mon_w, mon_h = selected_mon['width'], selected_mon['height']
            cfg_w, cfg_h = self.cfg.display.expected_width, self.cfg.display.expected_height
            
            if mon_w != cfg_w or mon_h != cfg_h:
                print(f"\n⚠️  Monitor resolution: {mon_w}x{mon_h}")
                print(f"   Config expects: {cfg_w}x{cfg_h}")
                print("\nTemplates might not match if resolutions differ.")
                print(" 1. Update config to match monitor (Recommended)")
                print(" 2. Keep current config")
                
                while True:
                    choice = input("\nSelect (1-2): ").strip()
                    if choice == "1":
                        self.cfg.display.expected_width = mon_w
                        self.cfg.display.expected_height = mon_h
                        print(f">> Config updated to {mon_w}x{mon_h}")
                        break
                    elif choice == "2":
                        print(">> Keeping config as-is")
                        break
            else:
                print(f">> Resolution matches config ({mon_w}x{mon_h}) [OK]")
        
        # Persist settings
        try:
            cfg_path = Path("config.yaml")
            if cfg_path.exists():
                content = cfg_path.read_text(encoding="utf-8")
                
                # Update monitor index
                content = re.sub(
                    r'(monitor:\s*)\d+',
                    f'\\1{monitor_choice}',
                    content,
                    count=1
                )
                
                # Update resolution
                content = re.sub(r'(expected_width:\s*)\d+', f'\\1{self.cfg.display.expected_width}', content)
                content = re.sub(r'(expected_height:\s*)\d+', f'\\1{self.cfg.display.expected_height}', content)
                
                cfg_path.write_text(content, encoding="utf-8")
                print(">> Settings saved [OK]")
        except Exception as e:
            print(f">> Warning: Failed to save settings: {e}")
        
        # STEP 3: Profile Selection
        print("\n" + "─"*60)
        print(" STEP 3: PROFILE SETUP")
        print("─"*60)
        print("Select a profile (folder with your button templates).\n")
        
        # Scan profiles
        available = [d.name for d in profiles_dir.iterdir() if d.is_dir()]
        
        if not available:
            print("(!) No profiles found.")
            print("    Creating default profile: 'example'")
            # Default name; user can rename the folder or create new profiles later
            (profiles_dir / "example").mkdir(parents=True, exist_ok=True)
            self.profile = "example"
            time.sleep(1.0)
        else:
            print("Available Profiles:")
            for i, name in enumerate(available, 1):
                print(f"  {i}. {name}")
            print(f"  {len(available)+1}. [Create New Profile]")
            
            while True:
                try:
                    s = input(f"\nSelect Profile (1-{len(available)+1}): ").strip()
                    choice = int(s)
                    if 1 <= choice <= len(available):
                        self.profile = available[choice-1]
                        break
                    elif choice == len(available) + 1:
                        new_name = input("Enter new profile name: ").strip()
                        # S-2: Sanitize profile name to prevent path traversal
                        new_name = new_name.replace("\\", "").replace("/", "").replace("..", "").strip(". ")
                        if new_name:
                            new_path = (profiles_dir / new_name).resolve()
                            if not str(new_path).startswith(str(profiles_dir.resolve())):
                                print(">> Invalid profile name.")
                                continue
                            new_path.mkdir(exist_ok=True)
                            self.profile = new_name
                            break
                except ValueError:
                    pass

        # Save profile choice
        print(f"\n>> Selected Profile: '{self.profile}'")
        self.cfg.profiles.active_profile = self.profile
        
        try:
            cfg_path = Path("config.yaml")
            if cfg_path.exists():
                content = cfg_path.read_text(encoding="utf-8")
                new_content = re.sub(
                    r'(active_profile:\s*)["\']?.*?["\']?(\s*#|$)', 
                    f'\\1"{self.profile}"\\2', 
                    content, 
                    count=1
                )
                if new_content != content:
                    cfg_path.write_text(new_content, encoding="utf-8")
                    print(">> Profile saved to config [OK]")
        except Exception as e:
            print(f">> Warning: Failed to save config: {e}")

        # Final instructions
        print("\n" + "─"*60)
        print(" SETUP COMPLETE!")
        print("─"*60)
        print(" To change these settings later:")
        print(" 1. Edit 'config.yaml' manually")
        print(" 2. OR delete 'active_profile' line to re-run this wizard")
        print("─"*60 + "\n")
        time.sleep(2.0)
        print("─"*60 + "\n")
        time.sleep(2.0) # Let them read it

    def _init_ui(self):
        cycle_key = getattr(self.cfg.hotkeys, 'cycle_strategy', 'f8')
        self.dash = Dashboard(
            profile=self.cfg.profiles.active_profile,
            night_hour=self.cfg.ui.night_mode_hour,
            refresh_ms=self.cfg.ui.refresh_rate_ms,
            pause_key=self.cfg.hotkeys.pause_bot,
            stop_key=self.cfg.hotkeys.stop_bot,
            reload_key=self.cfg.hotkeys.reload_bot,
            cycle_key=cycle_key
        )
        self.dash.stats.load()
        self.log = make_logger(self.dash)
        self.dash.start()


    def _load_templates(self) -> Dict[str, np.ndarray]:
        # Load all template images from current profile folder
        templates = {}
        base = Path("profiles") / self.profile
        if base.exists():
            for p in base.glob("*.png"):
                img = cv2.imread(str(p))
                if img is not None:
                    templates[p.stem] = img
        return templates

    def _reload_systems(self, initial: bool = False):
        # Reinitialize matcher/mouse when config changes
        # Update components with new config values
        self.matcher = TemplateMatcher(
            confidence=self.cfg.matching.confidence_threshold,
            marginal=self.cfg.matching.marginal_threshold,
            grayscale=self.cfg.matching.use_grayscale,
            strategy=self.cfg.matching.strategy,
            debug_path=Path("logs/debug") if self.cfg.visual.debug_mode else None,
            log_fn=self.log
        )
        
        self.mouse = HumanMouse(
            speed=self.cfg.mouse.speed_factor,
            resolution=self.cfg.mouse.curve_resolution,
            jitter_amp=self.cfg.mouse.jitter_amplitude if self.cfg.mouse.jitter_enabled else 0,
            jitter_freq=self.cfg.mouse.jitter_frequency if self.cfg.mouse.jitter_enabled else 0,
            overshoot=self.cfg.mouse.overshoot_enabled,
            overshoot_prob=self.cfg.mouse.overshoot_probability,
            hesitate_range=(self.cfg.timing.hesitation_min_ms, self.cfg.timing.hesitation_max_ms),
            stealth_callback=lambda s: self.dash.set_stealth(True, s)
        )
        
        # Load templates
        self.templates = self._load_templates()
        
        if not initial:
            self.log(f"System reloaded. Strategy: {self.cfg.matching.strategy.upper()}", "SUCCESS")
            self.log(f"Templates loaded: {len(self.templates)}", "INFO")

    def handle_reload(self):
        # Hot-reload config and systems
        self.reload_requested = False
        try:
            old_profile = self.profile
            self.cfg = load_config()
            self._ensure_profile() # Re-verify profile logic
            
            if self.profile != old_profile:
                self.log(f"Profile switched: {old_profile} -> {self.profile}", "SUCCESS")
                
            self._reload_systems()
            
        except Exception as e:
            self.log(f"Reload failed: {e}", "ERROR")

    def handle_cycle(self):
        # Switch between matching algorithms
        self.cycle_requested = False
        try:
            strategies = ["cascade", "template", "orb", "akaze"]
            current = self.cfg.matching.strategy.lower()
            
            try:
                idx = strategies.index(current)
                new_strat = strategies[(idx + 1) % len(strategies)]
            except ValueError:
                new_strat = "cascade"
            
            self.cfg.matching.strategy = new_strat
            self._reload_systems()
            
        except Exception as e:
            self.log(f"Cycle failed: {e}", "ERROR")

    def smart_sleep(self, duration: float, jitter: float = 0.0):
        # Responsive sleep - keeps UI alive and checks hotkeys
        if jitter > 0:
            duration += duration * random.uniform(-jitter, jitter)
            
        if duration <= 0: return

        end_time = time.time() + duration
        while time.time() < end_time:
            # 1. Hotkey Checks
            if self.reload_requested: self.handle_reload()
            if self.cycle_requested: self.handle_cycle()
            if not self.running or self.paused: break
            
            # 2. UI Refresh
            if self.dash: self.dash.update()
            
            # 3. Small sleep to prevent CPU spinning
            # 50ms is fast enough for 20fps UI updates
            time.sleep(0.05)

    def run(self):
        # Main bot loop
        self.bootstrap()
        
        try:
            while self.running:
                # 1. Input Handling (also handled inside smart_sleep now)
                if self.reload_requested: self.handle_reload()
                if self.cycle_requested: self.handle_cycle()
                
                # 2. Pause Logic
                if self.paused:
                    if not self.last_pause_state:
                        self.dash.set_status(Dashboard.STATUS_IDLE, "Paused")
                        self.dash.pause_timer()
                        self.log("PAUSED via Hotkey", "WARN") # Added log
                        self.last_pause_state = True
                    
                    # Responsive pause loop
                    self.dash.update()
                    time.sleep(0.1) 
                    continue
                
                if self.last_pause_state:
                    self.dash.resume_timer()
                    self.log("RESUMED operation", "SUCCESS") # Added log
                    self.last_pause_state = False
                    
                # 3. Core Loop
                self._tick()
                
                # 4. Anti-Burnout Sleep (Responsive)
                sleep_duration = random.uniform(self.cfg.timing.min_sleep_seconds, self.cfg.timing.max_sleep_seconds)
                self.smart_sleep(sleep_duration, self.cfg.timing.jitter_pct)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            time.sleep(3.0) # Give user time to see it
        finally:
            self.shutdown()

    def _tick(self):
        # One scan-and-click cycle
        self.dash.stats.inc_cycles()
        self.dash.set_status(Dashboard.STATUS_SCANNING)
        self.dash.set_stealth(False)
        self.dash.update()
        
        screenshot = self.screen.capture()
        self.log(f"Scanning...", "INFO") # Heartbeat log
        
        # Sort templates based on priority
        # Priority: stop_ > web_ (if expecting) > others
        scan_order = list(self.templates.items())
        def get_priority(name):
            n = name.lower()
            if n.startswith("stop_"): return 0
            if self.expecting_web and n.startswith("web_"): return 1
            return 2
            
        scan_order.sort(key=lambda x: get_priority(x[0]))
        
        if self.cfg.timing.fallback_cycles > 0 and self.no_match_streak >= self.cfg.timing.fallback_cycles:
             self.log(f"Fallback mode: full scan (streak {self.no_match_streak})", "WARN")
             # Shuffle non-stop templates; stop_ templates stay at the front
             stop_items = [(n, t) for n, t in scan_order if n.lower().startswith("stop_")]
             other_items = [(n, t) for n, t in scan_order if not n.lower().startswith("stop_")]
             random.shuffle(other_items)
             scan_order = stop_items + other_items

        matched = False
        
        # Scan
        for name, template in scan_order:

            # Update Dash
            self.dash.set_template(name, self.cfg.matching.strategy.upper())
            self.dash.update()
            time.sleep(SCAN_VISUAL_DELAY)
            
            # Match
            # Use appropriate threshold
            if name.lower().startswith("stop_"):
                # High confidence for stop signals to avoid false positives
                thresh = 0.85
            else:
                 thresh = self.cfg.matching.marginal_threshold

            result = self.matcher.match(template, screenshot, name)
            
            if result.found and result.confidence >= thresh:
                if name.lower().startswith("stop_"):
                    self.log(f"STOP SIGNAL: {name}", "SUCCESS")
                    self.log("Collection installation complete. Exiting.", "SUCCESS")
                    self.running = False
                    return

                self._handle_match(name, result)
                matched = True
                break
            
            # Allow UI update during heavy scanning
            self.dash.update()
        
        if not matched:
            self.no_match_streak += 1
        else:
            self.no_match_streak = 0

    def _handle_match(self, name: str, result: Any):
        # Handle click on found target
        self.dash.stats.inc_matches()
        
        algo = result.algorithm.upper() if result.algorithm else "?"
        self.log(f"Match: {name} [{algo}] ({result.confidence:.2f})", "SUCCESS")
        
        self.dash.set_stealth(True, "Approaching Target")
        self.dash.update()
        
        # Coordinate Logic
        cx, cy = result.center
        if self.cfg.mouse.click_offset_enabled:
            cx, cy = result.random_click_point(self.cfg.mouse.click_offset_ratio)
            
        # Action
        x, y = self.mouse.move_and_click(cx, cy, return_home=False)
        
        self.dash.stats.inc_clicks()
        self.dash.stats.save()
        self.log(f"Click executed @ {x},{y}", "CLICK")
        
        # Post-Click State Updates
        if name.lower().startswith("web_"):
            self.expecting_web = False
            self.log(f"Web clicked. Waiting {self.cfg.timing.web_click_delay}s", "INFO")
            self.smart_sleep(self.cfg.timing.web_click_delay, self.cfg.timing.jitter_pct)
            
            # Verification: Check for "Your download has started"
            verify_template = next((k for k in self.templates.keys() if k.startswith("web_download_started")), None)
            
            if verify_template:
                self.log("Verifying download text...", "INFO")
                self.dash.set_template("Verifying...", "TEXT_CHECK")
                self.dash.update()
                
                start_verify = time.time()
                verified = False
                
                while time.time() - start_verify < self.cfg.timing.download_verify_timeout:
                    scr = self.screen.capture()
                    # High confidence needed for text
                    res = self.matcher.match(self.templates[verify_template], scr, verify_template)
                    
                    if res.found and res.confidence >= 0.85:
                        self.log("Download CONFIRMED.", "SUCCESS")
                        verified = True
                        break
                        
                    self.smart_sleep(0.5)
                    
                if not verified:
                    self.log("Download verification TIMEOUT. Closing anyway.", "WARN")
            
            # FOCUS CLICK: Ensure browser is focused before Ctrl+W
            # Click exactly where we are (in place) to regain focus
            self.log("Focusing window (Click-in-place)", "INFO")
            pyautogui.click()

            self.log(f"Closing tab ({self.cfg.hotkeys.close_tab})", "INFO")
            pyautogui.hotkey(*self.cfg.hotkeys.close_tab.split('+'))
        else:
            self.expecting_web = True
            self.log(f"Vortex detected. Expecting browser...", "INFO")
            # Use smart_sleep here too
            self.smart_sleep(self.cfg.timing.vortex_launch_delay, self.cfg.timing.jitter_pct)

    def shutdown(self):
        # Unregister hotkeys
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        # Close screen capture handle
        if self.screen and self.screen._sct:
            try:
                self.screen._sct.close()
                self.screen._sct = None
            except Exception:
                pass
        if self.dash:
            self.dash.stop()
        print("\nExiting Nexus-AutoDL...")

if __name__ == "__main__":
    bot = NexusBot()
    bot.run()
