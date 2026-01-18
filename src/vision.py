"""
src/vision.py - Computer vision and template matching.
"""

import time
import mss
import cv2
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Callable

# mss is fast but we instantiate it per capture or keep generic one
# We'll use a class wrapper

@dataclass
class MatchResult:
    # Template matching result with click coordinates
    found: bool
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    algorithm: str = ""
    
    @property
    def center(self) -> Tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2
    
    def random_click_point(self, offset_ratio: float = 0.35) -> Tuple[int, int]:
        """
        Get a click point randomly offset from center (darts/Gaussian).
        """
        import random
        
        cx, cy = self.center
        
        # Gaussian offset - sigma set so 3σ ≈ offset_ratio (99.7% within bounds)
        sigma_x = (self.width * offset_ratio) / 3
        sigma_y = (self.height * offset_ratio) / 3
        
        # Generate offset
        offset_x = random.gauss(0, sigma_x)
        offset_y = random.gauss(0, sigma_y)
        
        # Clamp to avoid clicking outside
        max_offset_x = self.width * 0.45
        max_offset_y = self.height * 0.45
        
        offset_x = max(-max_offset_x, min(max_offset_x, offset_x))
        offset_y = max(-max_offset_y, min(max_offset_y, offset_y))
        
        return int(cx + offset_x), int(cy + offset_y)

def check_resolution(width: int, height: int) -> bool:
    """Check if resolution is 1080p-ish."""
    # Loose check
    return width > 1600 and height > 900

class ScreenCapture:
    # Screen grabber using mss (way faster than pyautogui)
    
    def __init__(self, monitor_index: int = 1) -> None:
        self._sct: Optional[mss.mss] = None
        self.monitor_index = monitor_index
        
    def __enter__(self):
        self._sct = mss.mss()
        return self
        
    def __exit__(self, exc_type, exc_str, exc_tb):
        if self._sct:
            self._sct.close()
            self._sct = None
    
    def list_monitors(self) -> list:
        # List all monitors with their dimensions
        if not self._sct:
            self._sct = mss.mss()
        return self._sct.monitors
            
    def capture(self) -> np.ndarray:
        if not self._sct:
            self._sct = mss.mss()
        
        # Pick the right monitor (clamped to valid range)
        monitor_idx = max(0, min(self.monitor_index, len(self._sct.monitors) - 1))
        monitor = self._sct.monitors[monitor_idx]
        img = self._sct.grab(monitor)
        
        # Convert to numpy/opencv BGR
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

class TemplateMatcher:
    """
    Handles template matching with various strategies.
    Strategies: 'cascade', 'template', 'orb', 'akaze'.
    """
    
    def __init__(
        self,
        confidence: float = 0.8,
        marginal: float = 0.6,
        grayscale: bool = True,
        strategy: str = "cascade",
        debug_path: Optional[Path] = None,
        log_fn: Optional[Callable[[str, str], None]] = None
    ) -> None:
        self._conf = confidence
        self._marginal = marginal
        self._gray = grayscale
        self._strategy = strategy.lower()
        self._debug = debug_path
        self._log = log_fn or (lambda m, l: None)
        
        # Feature detectors
        self._orb = cv2.ORB_create(nfeatures=800, scaleFactor=1.2, nlevels=8)
        self._akaze = cv2.AKAZE_create(threshold=0.001)
        self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        
    def match(self, template: np.ndarray, screen: np.ndarray, name: str = "") -> MatchResult:
        if self._strategy == "template":
            return self._match_template_only(template, screen, name)
        elif self._strategy == "orb":
            return self._match_orb_only(template, screen, name)
        elif self._strategy == "akaze":
            return self._match_akaze_only(template, screen, name)
        else:
            return self._match_cascade(template, screen, name)
            
    def _correlate(self, template: np.ndarray, screen: np.ndarray) -> MatchResult:
        """Standard tm_ccoeff_normed."""
        # Convert to gray if needed
        t_img = template
        s_img = screen
        
        if self._gray:
            if len(t_img.shape) == 3: t_img = cv2.cvtColor(t_img, cv2.COLOR_BGR2GRAY)
            if len(s_img.shape) == 3: s_img = cv2.cvtColor(s_img, cv2.COLOR_BGR2GRAY)
            
        res = cv2.matchTemplate(s_img, t_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        h, w = t_img.shape[:2]
        return MatchResult(
            found=True, # Checked by caller against threshold
            x=max_loc[0],
            y=max_loc[1],
            width=w,
            height=h,
            confidence=max_val,
            algorithm="template"
        )

    def _feature_match(self, template: np.ndarray, screen: np.ndarray, detector) -> MatchResult:
        try:
            kp1, des1 = detector.detectAndCompute(template, None)
            kp2, des2 = detector.detectAndCompute(screen, None)
            
            if des1 is None or des2 is None or len(kp1) < 2 or len(kp2) < 2:
                return MatchResult(False)
                
            matches = self._matcher.knnMatch(des1, des2, k=2)
            
            good = []
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good.append(m)
                    
            if len(good) > 8:
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None:
                    h, w = template.shape[:2]
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)
                    
                    x_min = int(np.min(dst[:, 0, 0]))
                    y_min = int(np.min(dst[:, 0, 1]))
                    x_max = int(np.max(dst[:, 0, 0]))
                    y_max = int(np.max(dst[:, 0, 1]))
                    
                    # Estimate confidence by inliers ratio
                    conf = len(good) / len(matches) if len(matches) > 0 else 0
                    
                    return MatchResult(
                        found=True,
                        x=x_min,
                        y=y_min,
                        width=x_max - x_min,
                        height=y_max - y_min,
                        confidence=conf
                    )
        except Exception:
            pass
            
        return MatchResult(False)

    def _save_debug(self, screen: np.ndarray, result: MatchResult, name: str) -> None:
        if not self._debug: return
        try:
            self._debug.mkdir(parents=True, exist_ok=True)
            vis = screen.copy()
            cv2.rectangle(
                vis, 
                (result.x, result.y), 
                (result.x + result.width, result.y + result.height), 
                (0, 255, 0), 2
            )
            cv2.putText(vis, f"{name} {result.confidence:.2f} [{result.algorithm}]", 
                       (result.x, result.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            ts = int(time.time() * 1000)
            cv2.imwrite(str(self._debug / f"match_{name}_{ts}.png"), vis)
        except:
            pass

    def _match_template_only(self, template: np.ndarray, screen: np.ndarray, name: str) -> MatchResult:
        result = self._correlate(template, screen)
        result.algorithm = "template"
        
        if result.found:
            if result.confidence >= self._conf:
                self._save_debug(screen, result, name)
            elif result.confidence >= self._marginal:
                self._log(f"Marginal template match {result.confidence:.2f} for {name}", "WARN")
                self._save_debug(screen, result, name)
        return result
    
    def _match_orb_only(self, template: np.ndarray, screen: np.ndarray, name: str) -> MatchResult:
        result = self._feature_match(template, screen, self._orb)
        result.algorithm = "orb"
        if result.found:
            if result.confidence < self._conf:
                self._log(f"Low-confidence ORB match {result.confidence:.2f} for {name}", "WARN")
            self._save_debug(screen, result, name)
        return result
        
    def _match_akaze_only(self, template: np.ndarray, screen: np.ndarray, name: str) -> MatchResult:
        result = self._feature_match(template, screen, self._akaze)
        result.algorithm = "akaze"
        if result.found:
            if result.confidence < self._conf:
                self._log(f"Low-confidence AKAZE match {result.confidence:.2f} for {name}", "WARN")
            self._save_debug(screen, result, name)
        return result

    def _match_cascade(self, template: np.ndarray, screen: np.ndarray, name: str) -> MatchResult:
        # 1. Template Match (Fastest)
        res = self._correlate(template, screen)
        res.algorithm = "template"
        
        if res.confidence >= self._conf:
            self._save_debug(screen, res, name)
            return res
            
        # 2. ORB (Robust to minor changes)
        # If template match was "okay" (marginal), we can try ORB to confirm.
        # But for now, we just proceed to feature matching if template fails.
            
        res_orb = self._feature_match(template, screen, self._orb)
        res_orb.algorithm = "orb"
        if res_orb.found: # Feature matching doesn't return confidence same way
             # We trust feature match if it found enough good matches (filtered inside)
             self._save_debug(screen, res_orb, name)
             return res_orb
             
        # 3. AKAZE (Slowest, handles scale/rotation)
        res_akaze = self._feature_match(template, screen, self._akaze)
        res_akaze.algorithm = "akaze"
        if res_akaze.found:
            self._save_debug(screen, res_akaze, name)
            return res_akaze
            
        # If nothing found, but template match was marginal, returns that?
        # Or return best failure?
        if res.confidence >= self._marginal:
             self._log(f"Marginal template match {res.confidence:.2f} (cascade fallback)", "WARN")
             self._save_debug(screen, res, name)
             return res
             
        return MatchResult(False)
