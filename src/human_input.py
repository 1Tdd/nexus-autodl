# Mouse control with bezier curves

import time
import random
import math
import pyautogui
from dataclasses import dataclass
from typing import Tuple, List, Optional, Callable

# Disable pyautogui fail-safe if you want, but be careful
pyautogui.FAILSAFE = True

@dataclass
class Point:
    x: float
    y: float

def pascal_row(n: int) -> List[int]:
    # Generate Pascal's triangle row for bezier math
    result = [1]
    x = 1
    for i in range(1, n + 1):
        x = x * (n - i + 1) // i
        result.append(x)
    return result

def make_bezier(control_points: List[Point]) -> Callable[[float], Point]:
    # Build bezier curve function from control points
    n = len(control_points) - 1
    combinations = pascal_row(n)
    
    def bezier(t: float) -> Point:
        # Bernstein polynomials
        result_x = 0.0
        result_y = 0.0
        for i, point in enumerate(control_points):
            bernstein = combinations[i] * (t ** i) * ((1 - t) ** (n - i))
            result_x += point.x * bernstein
            result_y += point.y * bernstein
        return Point(result_x, result_y)
    
    return bezier

class HumanMouse:
    # Mouse controller with bezier curves, variable speed, and jitter
    
    def __init__(
        self,
        resolution: int = 60,
        speed: float = 1.0,
        jitter_amp: float = 1.5,
        jitter_freq: float = 0.25,
        overshoot: bool = True,
        overshoot_prob: float = 0.20,
        overshoot_dist: Tuple[int, int] = (4, 12),
        overshoot_delay: int = 60,
        hesitate_range: Tuple[int, int] = (80, 250),
        stealth_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        self.res = resolution
        self.speed = speed
        self.jitter_amp = jitter_amp
        self.jitter_freq = jitter_freq
        self.overshoot = overshoot
        self.overshoot_prob = overshoot_prob
        self.over_dist = overshoot_dist
        self.over_delay = overshoot_delay
        self.hesitate_rng = hesitate_range
        self.callback = stealth_callback or (lambda x: None)
        
    def _pos(self) -> Point:
        x, y = pyautogui.position()
        return Point(x, y)
        
    def hesitate(self) -> None:
        # Quick random pause before clicking
        ms = random.randint(*self.hesitate_rng)
        time.sleep(ms / 1000.0)
        
    def move_to(self, x: int, y: int, duration: float = 0.0) -> None:
        # Move mouse using cubic bezier curve
        start = self._pos()
        end = Point(x, y)
        
        # Calculate distance
        dist = math.hypot(end.x - start.x, end.y - start.y)
        
        # Determine control points for arc
        # Random offsets scaled by distance
        offset = min(dist * 0.5, 400.0) 
        c1 = Point(
            start.x + random.uniform(-offset, offset),
            start.y + random.uniform(-offset, offset)
        )
        c2 = Point(
            end.x + random.uniform(-offset, offset),
            end.y + random.uniform(-offset, offset)
        )
        
        # Control points
        points = [start, c1, c2, end]
        curve = make_bezier(points)
        
        # Duration based on distance if not provided
        if duration <= 0:
            base_speed = random.uniform(0.0003, 0.0006) # seconds per pixel
            duration = (dist * base_speed) / self.speed
            duration = max(0.1, duration)
        
        self.callback("Moving")
        
        # Execute movement
        steps = self.res
        start_time = time.time()
        
        for i in range(steps + 1):
            t = i / steps
            
            # Easing: easeInOutQuad or similar
            # t_eased = t * t * (3 - 2 * t) # smoothstep
            # Cleaner acceleration
            if t < 0.5:
                t_eased = 2 * t * t
            else:
                t_eased = -1 + (4 - 2 * t) * t
                
            pos = curve(t_eased)
            
            # Add jitter
            if self.jitter_amp > 0 and random.random() < self.jitter_freq:
                pos.x += random.uniform(-self.jitter_amp, self.jitter_amp)
                pos.y += random.uniform(-self.jitter_amp, self.jitter_amp)
            
            # Move
            pyautogui.moveTo(pos.x, pos.y, _pause=False)
            
            # Sleep remainder of time slice to match duration
            elapsed = time.time() - start_time
            target_time = duration * (i / steps)
            if elapsed < target_time:
                time.sleep(target_time - elapsed)

    def click(self) -> Tuple[int, int]:
        # Click with human-like hesitation
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.06, 0.14)) # Human hold time
        pyautogui.mouseUp()
        pos = pyautogui.position()
        return (pos[0], pos[1])

    def move_and_click(
        self, 
        x: int, y: int,
        hesitate: bool = True,
        return_home: bool = True
    ) -> Tuple[int, int]:
        
        home = self._pos() if return_home else None
        
        # Overshoot logic
        target_x, target_y = x, y
        did_overshoot = False
        
        if self.overshoot and random.random() < self.overshoot_prob:
            # Calculate overshoot target
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(*self.over_dist)
            over_x = x + int(math.cos(angle) * dist)
            over_y = y + int(math.sin(angle) * dist)
            
            # Move to overshoot
            self.move_to(over_x, over_y)
            time.sleep(self.over_delay / 1000.0)
            did_overshoot = True
        
        # Move to actual target
        self.move_to(target_x, target_y)
        
        if hesitate:
            self.hesitate()
            
        coords = self.click()
        
        if home:
            time.sleep(random.uniform(0.04, 0.08))
            self.move_to(int(home.x), int(home.y))
        
        return coords
