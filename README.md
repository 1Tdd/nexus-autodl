<div align="center">
<pre>
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗         █████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ ██╗     
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝        ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██║     
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗______  ███████║██║   ██║   ██║   ██║   ██║██║  ██║██║     
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║______║ ██╔══██║██║   ██║   ██║   ██║   ██║██║  ██║██║     
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║        ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██████╔╝███████╗
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝        ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝
</pre>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-0.4-blue?style=flat-square" alt="Version">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Vortex-Supported-da8b31?style=flat-square&logo=nexusmods&logoColor=white" alt="Vortex">
  <img src="https://img.shields.io/badge/MO2-Works-blueviolet?style=flat-square" alt="MO2">
  <img src="https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV">
</p>

<p align="center"><b>Downloads your mods. Acts like a drunk human. Doesn't get banned.</b></p>

---

## Overview

Nexus-DL automates repetitive clicking on Nexus Mods download pages while downloading mod collections. It uses computer vision to detect buttons and clicks them with realistic mouse movements to avoid detection.

<table>
<tr>
<td width="50%">

**On Vortex**
- Clicks download buttons in the Vortex app
- Launches browser downloads automatically

</td>
<td width="50%">

**On Web**
- Clicks "Slow Download" buttons on Nexus
- Verifies download start
- Auto-closes browser tab automatically

</td>
</tr>
</table>

**What makes this different:**

| Feature | Basic Bots | Nexus-DL |
|---------|------------|----------|
| Image Matching | Pixel comparison | ORB/AKAZE feature detection |
| Mouse Movement | Straight lines | Bezier curves with jitter |
| Click Timing | Instant | Hesitation + random delays |
| Responsiveness | Laggy | **Zero-Lag Event Loop (20 FPS)** |
| Detection Risk | High | Low |

---

## Caution

Look, I'll be straight with you. Using automation tools with Nexus Mods is against their Terms of Service:

> Attempting to download files or otherwise record data offered through our services (including but not limited to the Nexus Mods website and the Nexus Mods API) in a fashion that drastically exceeds the expected average, through the use of software automation or otherwise, is prohibited without expressed permission.
>
> Users found in violation of this policy will have their account suspended.

I'm not responsible for what happens to your account. You use this at your own risk.

---

## Setup Guide

### Step 1: Download

Download `Nexus-AutoDL.exe` from the [Releases](../../releases) page.

### Step 2: First Run

Run the executable once. It will create:
- `config.yaml` - Your settings file
- `profiles/` - Folder for your button templates

**New in v0.4:** The bot runs an **Interactive Setup Wizard** to help you select or create a profile, and checks your screen resolution automatically.

### Step 3: Take Screenshots (Important)

This is the most critical step. The bot needs to know what buttons look like.

**4K users:** Check the `profiles/example/` folder. I've included ready-to-use templates for 4K displays:
- `vortex_download_4k.png`
- `web_slow_download_4k.png`
- `web_download_started_4k.png`
- `resume_button_4k.png` (Resumes stalled downloads)
- `install_anyway_4k.png` (Handles "Install to Staging" popup)
- `stop_done_botton_4k.png` (Auto-stop signal)
- `stop_enabled_button_4k.png` (Auto-stop signal)
- `stop_collection_installation complete_text_4k.png` (Auto-stop signal)

Just copy these to your profile folder and you're good to go.

**For other resolutions:** You'll need to take your own screenshots:
1. Open **Snipping Tool** (search in Start menu)
2. Click **New** and select **Rectangular Snip**
3. Draw a box around **ONLY** the button you want to click
4. Save as PNG in your profile folder

**What to screenshot:**

| Button | Save As | Purpose |
|--------|---------|---------|
| Grey "Slow Download" on Nexus website | `web_slow_download.png` | Clicks to start download |
| "Your download has started" text | `web_download_started.png` | **Verifies success** before closing tab |
| Grey download button in Vortex | `vortex_download.png` | Launches browser download |
| Confirmation popup buttons | `web_confirm.png` | Handles popups |

**Naming Convention:**
- Files starting with `vortex_` are checked FIRST (app buttons)
- Files starting with `web_` are checked SECOND (browser buttons)
- After clicking a `web_` button, the bot waits for verification, then sends `Ctrl+W` to close the browser tab.

### Step 4: Configure (Optional)

Edit `config.yaml` to adjust settings. See `config.example.yaml` for detailed explanations.

### Step 5: Run

```bash
Nexus-AutoDL.exe --profile my-mods
```

Or just double-click and select your profile from the menu.

---

## Command Line Options

| Flag | Description |
|------|-------------|
| `--profile NAME` | Profile folder to use |
| `--debug` | Save annotated screenshots to `logs/debug/` |

## Controls

| Key | Action |
|-----|--------|
| **F9** | Pause / Resume |
| **F10** | Stop the bot |
| **F5** | Reload config (hot reload) |
| **F8** | Cycle Matching Strategy (Cascade/ORB/etc) |

Bot starts paused. Press F9 to begin.

Move mouse to top-left corner (0,0) for emergency abort.

---

## Configuration

Key settings in `config.yaml`:

```yaml
display:
  expected_width: 1920
  expected_height: 1080
  monitor: 1  # 0=all monitors, 1=primary, 2+=specific

matching:
  confidence_threshold: 0.80   # Lower to 0.70 if buttons aren't detected
                               # Raise to 0.90 if clicking wrong things

hotkeys:
  close_tab: "ctrl+w"
  stop_bot: "f10"
  pause_bot: "f9"
  reload_bot: "f5"             # Hot reload config without restarting
  cycle_strategy: "f8"         # Switch algorithms on the fly

ui:
  night_mode: "always"         # Options: "always", "auto", "disabled"
  night_mode_start_hour: 20

timing:
  min_sleep_seconds: 1.5       # Random delay between scans
  max_sleep_seconds: 4.0
  vortex_launch_delay: 5.0     # Wait after Vortex click (+/- jitter)
  web_click_delay: 1.5         # Wait after web click before closing tab
  download_verify_timeout: 10.0 # Time to wait for "Download Started" text
  jitter_pct: 0.20             # Adds randomness to all delays (20%)
```

---

## How It Works

### Vision System

1. Captures screen using `mss` (3-5x faster than pyautogui)
2. Runs template correlation first (fast)
3. Falls back to ORB feature matching if confidence is marginal
4. Falls back to AKAZE if ORB fails (handles rotation/scale)

### Mouse Movement

1. Calculates cubic Bezier curve from current position to target
2. Applies micro-jitter to simulate hand tremor
3. Occasionally overshoots and corrects back
4. Hesitates before clicking (humans don't click instantly)
5. Returns to original position after web clicks

### Priority Queue

Templates are processed in this order:
1. `stop_*` files (auto-exit signals) - **Top Priority**
2. `web_*` files (browser buttons) - High Priority (when expecting web)
3. `vortex_*` and others - Standard Priority

After clicking a `vortex_*` button, the bot prioritizes `web_*` templates for the next scan.
After clicking a `web_*` button, the bot checks for `web_download_started.png`, waits for confirmation, then sends `Ctrl+W` to close the browser tab.

---

## Troubleshooting

**Buttons not detected:**
- Run with `--debug` and check `logs/debug/` for annotated screenshots
- Lower `confidence_threshold` to 0.70 or 0.60
- Ensure templates match current screen resolution

**Resolution mismatch error:**
- The bot detects this at startup now. Follow the prompts to auto-update your config.

**Clicks landing in wrong position:**
- Check Windows DPI scaling (set to 100% or recapture templates)

**Tab not closing after web click:**
- Check `hotkeys.close_tab` in config.yaml
- Ensure `web_download_started.png` is properly captured

**Config changes not applying:**
- Press F5 to hot reload, or restart the bot

**Multi-monitor issues:**
- Run the bot once to trigger the monitor selection wizard
- Or edit `display.monitor` in config.yaml (0=all, 1=primary, 2+=specific)

---

## Building the Executable

```bash
pip install pyinstaller
pyinstaller Nexus-AutoDL.spec
```

Or run `build.bat`.

---

## Pro Tip: Nexus No Wait

If you use the [Nexus No Wait](https://greasyfork.org/en/scripts/394039-nexus-no-wait) userscript, downloads start and close automatically.
- You **do not need** any `web_` templates.
- Just create your `vortex_` templates and let the script handle the entire web flow.

## Auto-Stop (Collection Complete)

The bot can automatically stop when it sees a specific image (e.g., "Installation Complete").
1.  Take a screenshot of the text/button that appears when finished.
2.  Save it to your profile starting with `stop_` (e.g., `stop_complete.png`).
3.  When the bot sees this, it will log "Collection Complete" and exit.

---

## A Note on Supporting Mod Authors

Mod authors put real time and effort into their work. If you find yourself downloading a lot, maybe throw a few bucks their way through the donation links on their mod pages. Nexus Premium is also worth considering if you mod heavily. The fast servers and unlimited downloads pay for themselves pretty quick.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Credits

Original concept by [Parsiad Azimzadeh](https://github.com/parsiad)

Maintained by [@1Tdd](https://github.com/1Tdd)
