# NitroCore — Windows System Optimizer

[![CI](https://github.com/TheRealJesusTheHacker/NitroCore/actions/workflows/ci.yml/badge.svg)](https://github.com/TheRealJesusTheHacker/NitroCore/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/TheRealJesusTheHacker/NitroCore)](https://github.com/TheRealJesusTheHacker/NitroCore/releases)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Status:** Released. Current version 1.1.3, as stated in `pyproject.toml` — distributed via winget, as a standalone `.exe` from GitHub Releases, and from source (Python 3.9+, Windows).

## What is NitroCore?

**NitroCore is a Windows system optimizer with a safety-first design.** Over time, a Windows PC accumulates junk files, runs background services you don't need, and ships with settings that favor battery life and visual flair over raw speed. NitroCore cleans the junk, quiets the background noise, and flips the right switches — through one dashboard, with a restore point offered before anything risky and a preview mode that shows every change before it happens.

The core idea: **two one-click optimization profiles** that encode real tuning knowledge, so you don't need to know what the registry is to benefit from it:

- **Gaming** — maximum FPS and lowest latency. Aggressive power plan, full registry tuning, and background service reduction. It trades automatic patching for speed and tells you so, explicitly.
- **Cybersecurity** — stable tools and patch-friendly. Visual performance tweaks and temp cleanup, while Windows Update and BITS stay alive so security tooling and patches keep flowing.

Every profile runs the same five-step pipeline — **Registry → Temp Files → Disk Cleanup → Services → Performance** — but each step scopes its behavior to the active profile. High-impact steps (registry, services, and disk cleanup on the Gaming profile) offer a Windows restore point before they run, and if restore-point creation fails, the pipeline **stops** and asks you what to do instead of silently proceeding without its safety net.

## Who is it for?

- **Gamers** who want a repeatable, one-click tune-up: junk gone, background services quiet, Ultimate Performance power plan engaged.
- **Cybersecurity practitioners and students** who need a stable, patch-friendly workstation without hand-editing the registry or Services console.
- **Tinkerers** who want to see exactly what an optimizer *would* do first — Preview Mode prints the full change list and changes nothing.

## Features

### Tabbed dashboard

The GUI is a custom-built tkinter interface (980×780) with six tabs. Every tab carries a risk label — **High**, **Medium**, or **Low** — so you know what you're getting into before you click:

| Tab | Risk | What it does |
|-----|------|--------------|
| Registry Optimization | High | Disables hibernation (`powercfg /hibernate off`), sets the pagefile to automatic management (PowerShell CIM), and applies visual-performance registry tweaks (best-performance visual effects, snappier menus via `MenuShowDelay`). Gaming applies all tweaks; Cybersecurity applies visual tweaks only. Includes **Restore Previous Registry Values** — every write snapshots the old value to a JSON undo file under `%APPDATA%\NitroCore\registry_undo` first. |
| Temporary File Cleanup | Low | Purges `%TEMP%` and `%SYSTEMROOT%\Temp` (de-duplicated) plus Chrome (`Cache_Data`) and Firefox (`cache2`, profile wildcards resolved) caches, with a before/after MB-freed report. Never recurses into symlinks or NTFS junctions — a junction inside a temp tree could point outside it, so those are skipped fail-closed. |
| Disk Cleanup | Medium | **Refresh Disk Usage** shows per-drive usage for local fixed drives. **Run Windows Disk Cleanup** runs `cleanmgr /verylowdisk`, falling back to `DISM /Online /Cleanup-Image /StartComponentCleanup` if it fails (and tells you *why* it failed). **Clean Old Downloads (30+ days)** moves stale Downloads to the **Recycle Bin** via the Windows shell — never permanent deletion; files the shell won't take are left in place and reported. |
| Service Management | High | Gaming stops **Windows Update (wuauserv)**, **BITS**, and **Windows Search (WSearch)** and sets them to Manual. Cybersecurity stops **Search only**, keeping patching alive. Whenever the update services are touched, NitroCore logs an explicit security warning that patches will not install automatically until you re-enable them. |
| Performance Tuning | Low | Switches to the **Ultimate Performance** power plan via `powercfg` (checks first so it never clones a duplicate scheme; falls back to **High Performance** if Ultimate is unavailable) and raises `explorer.exe` / `dwm.exe` to **Above Normal** priority via psutil. |
| Status & Logs | Low | Live scrolling log of every step as it runs. Full logs are also saved to `%APPDATA%\NitroCore\logs`. |

### Live stats header

CPU %, RAM (% and GB used/total), free disk space, and the active power-plan name — polled continuously, with the expensive queries cached (disk 30 s, power plan 120 s) and the power-plan cache invalidated the moment a pipeline changes it.

### Preview Mode (`--dry-run`)

Run the whole pipeline without changing anything:

```powershell
python main.py --dry-run
```

In dry-run mode every mutating module records a human-readable *"would do"* entry instead of acting, and the app prints a numbered report plus a `PREVIEW ONLY — no changes were made.` footer. Dry runs skip the admin-elevation gate and the single-instance lock entirely — a read-only preview never fights you for privileges. Restore-point creation is skipped in preview mode (nothing will change, so there's nothing to roll back).

### Restore-point safety net

Before high-impact steps, NitroCore offers to create a system restore point via PowerShell `Checkpoint-Computer` (`-RestorePointType MODIFY_SETTINGS`, run with `-NoProfile -NonInteractive`). If creation fails, the run **blocks** with a dialog: *Try Again / Continue Without It / Abort* — it never silently proceeds without the safety net.

### Command-line usage

```powershell
# Full GUI (must run as administrator)
python main.py

# Headless dry-run preview of the active profile — changes nothing
python main.py --dry-run
```

There's also a hidden `--fallout` flag. And if you click the title bar 7 times… you'll find the Fallout-themed Pip-Boy mode. Its big red "System Purge" button still asks for confirmation, offers a restore point, respects preview mode, and can't double-fire mid-run. Click the header to return to the normal UI.

### Under the hood

- **`main.py`** — entry point: parses flags, enforces the admin gate (exit code 1 without elevation), enforces single-instance via a global mutex, then builds the GUI or runs the headless preview.
- **`source/modules/`** — the five pipeline workers (`registry`, `temp_files`, `disk_cleanup`, `services`, `performance`) plus `system_stats` (telemetry) and `async_worker` (daemon-thread dispatch so long operations never freeze the UI).
- **`source/utils/profiles.py`** — profile definitions and the pipeline layout (`get_pipeline`, `step_requires_restore_prompt`, `execute_step`).
- **`source/utils/preview.py`** — the process-wide dry-run recorder behind Preview Mode.
- **`source/utils/config.py`** — global runtime flags (`ACTIVE_PROFILE`, `DRY_RUN`, …) and CLI parsing.
- **`source/utils/restore_point.py`** — restore-point creation with dry-run and platform guards.
- **`source/gui/`** — custom tkinter widgets (buttons, dialogs, tabs, theme, fonts) — no stock-ttk look.
- Every Windows-only assumption is centralized in `source/utils/platform.py` (`IS_WINDOWS`), so the app degrades gracefully instead of crashing on other platforms. No `shell=True` anywhere in the codebase — all subprocess calls use argument lists.

## Installation

### Option A — winget (easiest)

```powershell
winget install TheRealJesusTheHacker.NitroCore
```

### Option B — Ready-to-run .exe

1. Download `NitroCoreOptimizer.exe` from the [Releases](https://github.com/TheRealJesusTheHacker/NitroCore/releases) page.
2. **Verify it** (optional but smart) — compare against `SHA256SUMS.txt` from the same release:

   ```powershell
   certutil -hashfile NitroCoreOptimizer.exe SHA256
   ```

3. Right-click → **Run as administrator**. NitroCore needs elevation to modify system settings; without it, it exits with an "Access Denied" message instead of half-working.

### Option C — From source

Requires Python 3.9+ on Windows.

```powershell
git clone https://github.com/TheRealJesusTheHacker/NitroCore.git
cd NitroCore\NitroCore
pip install -r requirements.txt
```

Then **run as administrator**:

```powershell
python main.py
```

To run the test suite (works on any platform — it only exercises non-mutating logic and dry-run paths):

```powershell
pip install -r requirements-dev.txt
python -m pytest NitroCore\tests -v
```

> **Screenshot:** a GUI screenshot is on the to-do list — it has to be captured on a real Windows machine, which isn't available in this dev environment.

## Verified downloads

Every release ships:

- **`SHA256SUMS.txt`** — hashes for every release artifact, so you can confirm your download wasn't tampered with.
- **Signed build-provenance attestations** — cryptographic proof the binaries were built from this repo's code.

Release binaries are currently **unsigned** — Windows SmartScreen will warn on first run. Verify the hash before trusting the binary. (Code signing is a planned manual release step.)

## Roadmap

- **Code-signed release binaries** — planned manual release step (see SECURITY.md); kills the SmartScreen warning.
- GUI screenshot for this README (needs a Windows capture).

## Contributing

Pull requests are welcome. A few ground rules:

- **Never break intended functionality** to satisfy a scanner — fix *around* the feature, and document anything that can't be fixed without neutering it.
- New behavior needs Preview Mode coverage and, where it mutates the system, a restore-point prompt and (for registry) undo snapshots.
- Run the checks before pushing: `python -m pytest NitroCore/tests`, `ruff check NitroCore`, `black --check NitroCore`.
- Use the PR template's safety checklist.

## Donations

If this tool earned its keep, BTC is welcome:

```
bc1qvydns2fmyjzj55wzxq7ta28nxdhcmu9l9m6yg0
```

## Contact

Business inquiries: **Sentinelsafeguard@outlook.com**

Security vulnerabilities: **do not open a public issue** — email Sentinelsafeguard@outlook.com instead. See [SECURITY.md](SECURITY.md).

## Changelog

All notable changes are documented in [CHANGELOG.md](CHANGELOG.md).

## License

MIT License — see [LICENSE](LICENSE) for the full text.
