# v0.4

- Initial release with smart sleep system
- Zero-lag event loop (20fps)
- OCR-free download verification
- Interactive profile setup wizard
- Stealth algorithm display
- Startup resolution check

---

# v0.7.0

## Breaking Changes

- **Config structure changed.** Delete old `config.json` and let the app regenerate `config.yaml`.
- **Python 3.10+ required.**
- **Tkinter GUI removed.** Now uses Rich terminal UI.

## New Features

### Added
- **Configurable Jitter**: All delays now have random +/- 15% variance (configurable) for human-like behavior.
- **F5 Reload**: Reload `config.yaml` on the fly without restarting.
- **Mouse Return**: Cursor returns to original position after handling browser tabs.
- **Smart Priority**: Dynamic priority shifting ensures web buttons are clicked even if Mod Manager is visible.
- **Configurable Delays**: Added `web_click_delay` and `vortex_launch_delay`.

### Changed
- **UI:** Renamed "Stealth Mode" to "Current Action".
- **Startup:** Bot now starts in PAUSED state (press F9 to begin).
- **Controls:** Replaced Ctrl+C with F10 (Stop) and F9 (Pause).

- **ORB/AKAZE Vision Cascade.** Template correlation → ORB → AKAZE fallback. Handles edge cases better than cv2.matchTemplate alone.
- **Human-Like Mouse Movement.** Cubic Bézier curves, micro-jitter (hand tremor), overshoot + correction. Passes as natural user interaction.
- **Rich Terminal Dashboard.** Three-panel layout with centered ASCII header, live stats, scrolling log, and dynamic status indicators (`● Idle` / `⚡ Active`).
- **Standalone EXE Support.** Build with `build.bat` or PyInstaller directly. Auto-creates config and profile folders on first run.
- **Interactive Profile Selection.** If no `--profile` specified, shows menu of available profiles.

## Fixes

### Fixed
- Fixed issue where Vortex button was repeatedly clicked in side-by-side window setups.
- Fixed logic for closing browser tabs.

- **Auto-config generation.** Missing `config.yaml` is created with defaults instead of crashing.
- **Resolution mismatch check.** Fails fast with clear error if screen resolution doesn't match config.
- **Low resolution warning.** Logs warning if height < 720p.
- **Fail-safe implementation.** Move mouse to top-left corner (0,0) to immediately abort.
- **Function key exit.** Press F10 to stop gracefully (configurable). Session summary displayed on exit.
- **Type hints.** Fixed `any` → `Any`, added hints throughout codebase.
- **Magic numbers eliminated.** Delays and thresholds moved to config or constants.

## Dependencies

```
pyautogui>=0.9.54
opencv-python>=4.8.0
mss>=9.0.0
rich>=13.7.0
pyyaml>=6.0
numpy>=1.26.0
keyboard>=0.13.5
```

## Upgrade Instructions

1. Delete old installation
2. Clone fresh or download release
3. Run `pip install -r requirements.txt`
4. Move template images to `profiles/<name>/`
5. Run `python main.py --profile <name>` or use the EXE
