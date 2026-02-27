# Dashboard UI

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.rule import Rule

VERSION = "v0.4.1"

COLORS = {
    "bg": "#0f172a",
    "border": "#334155",
    "border_active": "#10b981",
    "muted": "#64748b",
    "text": "#e2e8f0",
    "text_dim": "#94a3b8",
    "heading": "#fa933c", # Nexus Orange
    "success": "#10b981",
    "warning": "#f59e0b",
    "warn": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",
    "click": "#10b981",
    "stealth": "#a855f7",
    "idle": "#64748b",
    "active": "#10b981",
}

HEADER_ART = (
    "███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗         █████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ ██╗     \n"
    "████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝        ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██║     \n"
    "██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗______  ███████║██║   ██║   ██║   ██║   ██║██║  ██║██║     \n"
    "██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║______║ ██╔══██║██║   ██║   ██║   ██║   ██║██║  ██║██║     \n"
    "██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║        ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██████╔╝███████╗\n"
    "╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝        ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝"
)
HEADER_COMPACT = "▓▓▓ NEXUS AUTO-DL ▓▓▓"

class Stats:
    # Session stats with JSON persistence
    STATS_FILE = "logs/stats.json"
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start = datetime.now()
        self._paused_duration = timedelta(0)
        self._pause_start: Optional[datetime] = datetime.now()  # Start paused (bot starts paused)
        self.cycles = 0
        self.matches = 0
        self.clicks = 0
        self.errors = 0
        self._total_clicks = 0
        self._total_matches = 0
        
    def pause(self) -> None:
        with self._lock:
            if not self._pause_start:
                self._pause_start = datetime.now()
                
    def resume(self) -> None:
        with self._lock:
            if self._pause_start:
                paused = datetime.now() - self._pause_start
                self._paused_duration += paused
                self._pause_start = None
                
    def inc_cycles(self) -> None:
        with self._lock: self.cycles += 1
        
    def inc_matches(self) -> None:
        with self._lock: 
            self.matches += 1
            self._total_matches += 1
            
    def inc_clicks(self) -> None:
        with self._lock: 
            self.clicks += 1
            self._total_clicks += 1
            
    def inc_errors(self) -> None:
        with self._lock: self.errors += 1
        
    def save(self) -> None:
        import json
        from pathlib import Path
        try:
            with self._lock:
                data = {
                    "total_clicks": self._total_clicks,
                    "total_matches": self._total_matches,
                    "last_save": datetime.now().isoformat()
                }
            Path(self.STATS_FILE).parent.mkdir(parents=True, exist_ok=True)
            with open(self.STATS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception: pass
        
    def load(self) -> None:
        import json
        from pathlib import Path
        try:
            if Path(self.STATS_FILE).exists():
                with open(self.STATS_FILE, 'r') as f:
                    data = json.load(f)
                with self._lock:
                    self._total_clicks = data.get("total_clicks", 0)
                    self._total_matches = data.get("total_matches", 0)
        except Exception: pass
        
    def get(self) -> dict:
        """Returns dict with keys: runtime, runtime_sec, cycles, matches,
        clicks, errors, hit_rate, time_saved_min, total_clicks, total_matches."""
        with self._lock:
            now = datetime.now()
            current_pause = timedelta(0)
            if self._pause_start:
                current_pause = now - self._pause_start
            total_active = (now - self._start) - (self._paused_duration + current_pause)
            total_sec = max(0, int(total_active.total_seconds()))
            h, rem = divmod(total_sec, 3600)
            m, s = divmod(rem, 60)
            
            hit_rate = (self.matches / self.cycles * 100) if self.cycles > 0 else 0
            time_saved = self._total_clicks * 5
            
            return {
                "runtime": f"{h:02d}:{m:02d}:{s:02d}",
                "runtime_sec": total_sec,
                "cycles": self.cycles,
                "matches": self.matches,
                "clicks": self.clicks,
                "errors": self.errors,
                "hit_rate": hit_rate,
                "time_saved_min": time_saved // 60,
                "total_clicks": self._total_clicks,
                "total_matches": self._total_matches
            }

from collections import deque

class LogBuffer:
    def __init__(self, max_lines: int = 15) -> None:
        self._lines = deque(maxlen=max_lines)
        self._lock = threading.Lock()
        
    def add(self, message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        with self._lock:
            self._lines.append((timestamp, level, message))
                
    def get_all(self):
        with self._lock: return list(self._lines)

class Dashboard:
    STATUS_IDLE = "idle"
    STATUS_SCANNING = "scanning"
    STATUS_STEALTH = "stealth"
    STATUS_ERROR = "error"
    
    def __init__(
        self, profile: str = "", night_hour: int = 19, refresh_ms: int = 100,
        pause_key: str = "f9", stop_key: str = "f10", reload_key: str = "f5",
        cycle_key: str = "f8", compact: bool = False
    ) -> None:
        self._live = None
        self._profile = profile
        self._night_hour = night_hour
        self._refresh_ms = refresh_ms
        self._pause_key = pause_key.upper()
        self._stop_key = stop_key.upper()
        self._reload_key = reload_key.upper()
        self._cycle_key = cycle_key.upper()
        self._compact = compact
        self._console = Console()
        self._stats = Stats()
        self._log = LogBuffer(max_lines=50)
        self._status = self.STATUS_IDLE
        self._status_detail = ""
        self._current_template = ""
        self._stealth_mode = False
        self._stealth_action = ""
        self._current_algo = ""
        self._lock = threading.Lock()
        
    @property
    def stats(self): return self._stats
    
    def log(self, message: str, level: str = "INFO"):
        self._log.add(message, level)
        
    def set_status(self, status: str, detail: str = ""):
        with self._lock:
            self._status = status
            self._status_detail = detail
            
    def set_template(self, name: str, algo: str = ""):
        with self._lock: 
            self._current_template = name
            self._current_algo = algo
        
    def set_stealth(self, active: bool, action: str = ""):
        with self._lock:
            self._stealth_mode = active
            self._stealth_action = action
            
    def pause_timer(self): self._stats.pause()
    def resume_timer(self): self._stats.resume()
    
    def start(self):
        self._live = Live(
            self._render(), console=self._console,
            refresh_per_second=1000 // self._refresh_ms,
            screen=True, transient=False
        )
        self._live.start()
        
    def update(self):
        if self._live: self._live.update(self._render())
        
    def stop(self):
        if self._live:
            self._live.stop()
            self._live = None
            
    def _is_night(self):
        h = datetime.now().hour
        return h >= self._night_hour or h < 6
        
    def _render(self):
        layout = Layout()
        layout.split(
            Layout(name="header", size=9 if not self._compact else 4),
            Layout(name="middle", size=10),
            Layout(name="log", ratio=1, minimum_size=5),
            Layout(name="footer", size=3)
        )
        layout["middle"].split_row(
            Layout(name="stats", ratio=2),
            Layout(name="stealth", ratio=1)
        )
        layout["header"].update(self._render_header())
        layout["stats"].update(self._render_stats())
        layout["stealth"].update(self._render_stealth())
        layout["log"].update(self._render_log())
        layout["footer"].update(self._render_footer())
        return layout
        
    def _render_header(self):
        if self._status == self.STATUS_IDLE:
             badge = Text(" ● Idle ", style=f"bold {COLORS['idle']}")
        elif self._status == self.STATUS_SCANNING:
             badge = Text(" ⚡ Scanning ", style=f"bold {COLORS['active']}")
        elif self._status == self.STATUS_STEALTH:
             badge = Text(" ⚡ Stealth ", style=f"bold {COLORS['stealth']}")
        elif self._status == self.STATUS_ERROR:
             badge = Text(" ✖ Error ", style=f"bold {COLORS['error']}")
        else:
             badge = Text(f" ● {self._status} ", style=f"bold {COLORS['muted']}")
             
        header_text = Text(HEADER_COMPACT if self._compact else HEADER_ART.strip(), style=COLORS['heading'])
        subtitle = Text()
        subtitle.append(f"  {VERSION}  ", style=f"bold {COLORS['text_dim']}")
        subtitle.append("│ Profile: ", style=COLORS['border'])
        subtitle.append(self._profile or "None", style=f"bold {COLORS['text']}")
        subtitle.append("  │  ", style=COLORS['border'])
        subtitle.append_text(badge)
        if self._status_detail:
            subtitle.append(f"  {self._status_detail}", style=COLORS['text_dim'])
            
        return Panel(Align.center(Group(Align.center(header_text), Text(), Align.center(subtitle))), border_style=COLORS['border'])

    def _render_stats(self):
        data = self._stats.get()
        table = Table.grid(padding=(0, 2), expand=True)
        table.add_column("L", justify="right", style=COLORS['muted'])
        table.add_column("V", justify="left", style=f"bold {COLORS['text']}")
        table.add_row("Runtime", data["runtime"])
        table.add_row("Cycles", str(data["cycles"]))
        table.add_row("Matches", str(data["matches"]))
        table.add_row("Clicks", str(data["clicks"]))
        hr = data["hit_rate"]
        hr_color = COLORS['success'] if hr >= 80 else COLORS['warning'] if hr >= 50 else COLORS['error']
        table.add_row("Hit Rate", Text(f"{hr:.1f}%", style=f"bold {hr_color}"))
        table.add_row("Saved", f"~{data['time_saved_min']} min")
        if data["errors"] > 0:
            table.add_row("Errors", Text(str(data["errors"]), style=f"bold {COLORS['error']}"))
            
        return Panel(table, title=f"[{COLORS['heading']}]Live Stats[/]", border_style=COLORS['border'])

    def _render_stealth(self):
        lines = []
        if self._stealth_mode:
            lines.append(Align.center(Text("▓ ACTIVE ▓", style=f"bold {COLORS['stealth']}")))
            lines.append(Text())
            lines.append(Align.center(Text(self._stealth_action, style=COLORS['stealth'])))
            lines.append(Text())
            lines.append(Align.center(Text("◉ ◉ ◉", style=f"bold {COLORS['stealth']}")))
        else:
            lines.append(Align.center(Text("○ STANDBY ○", style=COLORS['muted'])))
            lines.append(Text())
            lines.append(Align.center(Text("Waiting...", style=COLORS['text_dim'])))
            
        if self._current_template:
            lines.append(Text())
            lines.append(Rule(style=COLORS['border']))
            lines.append(Align.center(Text(f"Target: {self._current_template}", style=COLORS['text'])))
            if hasattr(self, '_current_algo') and self._current_algo:
                lines.append(Align.center(Text(f"[{self._current_algo}]", style=COLORS['text_dim'])))
            
        return Panel(Group(*lines), title=f"[{COLORS['heading']}]Stealth[/]", border_style=COLORS['stealth'] if self._stealth_mode else COLORS['border'])

    def _render_log(self):
        lines = self._log.get_all()
        term_height = self._console.size.height
        avail = max(3, term_height - 25) # Approx
        visible = lines[-avail:] if lines else []
        
        text = Text()
        if not visible:
            return Panel(Align.center(Text("Waiting...", style=COLORS['muted'])), title=f"[{COLORS['heading']}]Log[/]", border_style=COLORS['border'])
            
        for ts, lvl, msg in visible:
            text.append(f" {ts} ", style=COLORS['text_dim'])
            c = COLORS.get(lvl.lower(), COLORS['info'])
            text.append(f"[{lvl:^7}]", style=f"bold {c}")
            text.append(f" {msg}\n", style=COLORS['text'])
            
        return Panel(Align(text, vertical="bottom"), title=f"[{COLORS['heading']}]Event Log[/]", border_style=COLORS['border'])

    def _render_footer(self):
        f = Text()
        f.append(f"  {self._pause_key} Start/Stop  ", style=COLORS['muted'])
        f.append(f"{self._reload_key} Reload  ", style=COLORS['muted'])
        f.append(f"{self._cycle_key} Strategy  ", style=COLORS['muted'])
        f.append(f"{self._stop_key} Quit  ", style=COLORS['muted'])
        if self._is_night(): f.append("  🌙 Night Mode", style=COLORS['text_dim'])
        return Panel(Align.center(f), border_style=COLORS['border'])

def make_logger(dash: Dashboard):
    def log(msg: str, level: str = "INFO"):
        dash.log(msg, level)
        dash.update()
    return log
