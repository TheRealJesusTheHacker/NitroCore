# NitroCore — Windows System Optimizer

**A safety-first Windows system optimizer with two one-click tuning profiles — Gaming and Cybersecurity — a preview mode that shows every change before it happens, restore-point gating on high-impact steps, and registry undo snapshots.**

[![CI](https://img.shields.io/github/actions/workflow/status/TheRealJesusTheHacker/NitroCore/ci.yml?style=flat-square)](https://github.com/TheRealJesusTheHacker/NitroCore/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/TheRealJesusTheHacker/NitroCore?style=flat-square)](https://github.com/TheRealJesusTheHacker/NitroCore/releases)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**Status:** Released. Current version **1.1.6** — the same version string is carried in `pyproject.toml`, `NitroCore/VERSION`, and `source/__init__.py` (`__version__`), and a test (`tests/test_version.py`) asserts they stay in sync. (1.1.6 is a visual release: the interface now wears NitroCore's own nitrous-azure palette — no behavior changes; see the changelog.) Distributed via winget, as a standalone `.exe` from GitHub Releases, and from source (Python 3.9+, Windows). A portable edition (`NitroCorePortable.zip`, a one-folder build with no installer — see Option B2 below) ships as of [v1.1.4](https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.4); the 1.1.3 release and earlier ship only the single-file `.exe` and `SHA256SUMS.txt`. NitroCore is **not published on PyPI** — there is no publish workflow in this repo, and the pip paths below build and install from this source tree.

## Contents

- [Overview](#overview)
- [Who is it for?](#who-is-it-for)
- [The two profiles](#the-two-profiles)
- [Features](#features)
- [Safety model](#safety-model)
- [Installation](#installation)
- [Usage](#usage)
- [How it works](#how-it-works)
- [Files NitroCore writes](#files-nitrocore-writes)
- [Development and testing](#development-and-testing)
- [Verified downloads](#verified-downloads)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Donations, contact, changelog, and license](#donations-contact-changelog-and-license)

## Overview

Over time, a Windows PC accumulates junk files, runs background services you don't need, and ships with settings that favor battery life and visual flair over raw speed. NitroCore cleans the junk, quiets the background noise, and flips the right switches — through one dashboard, with a restore point offered before anything risky and a preview mode that shows every change before it happens.

The core idea: **two one-click optimization profiles** that encode real tuning knowledge, so you don't need to know what the registry is to benefit from it:

- **Gaming** — maximum FPS and lowest latency. Aggressive power plan, full registry tuning, and background service reduction. It trades automatic patching for speed and tells you so, explicitly.
- **Cybersecurity** — stable tools and patch-friendly. Visual performance tweaks and temp cleanup, while Windows Update and BITS stay alive so security tooling and patches keep flowing.

Every profile runs the same five-step pipeline — **Registry → Temp Files → Disk Cleanup → Services → Performance** (`get_pipeline()` in `source/utils/profiles.py`) — but each step scopes its behavior to the active profile. High-impact steps offer a Windows restore point before they run, and if restore-point creation fails, the pipeline **stops** and asks you what to do instead of silently proceeding without its safety net.

## Who is it for?

- **Gamers** who want a repeatable, one-click tune-up: junk gone, background services quiet, Ultimate Performance power plan engaged.
- **Cybersecurity practitioners and students** who need a stable, patch-friendly workstation without hand-editing the registry or the Services console.
- **Tinkerers** who want to see exactly what an optimizer *would* do first — Preview Mode prints the full change list and changes nothing.

## The two profiles

The profile is chosen on the dashboard's profile-selector cards (`source/gui/profile_selector.py`); it sets `Config.ACTIVE_PROFILE` and scopes every pipeline step:

| Pipeline step | Gaming | Cybersecurity |
|---|---|---|
| Registry | All tweaks: hibernation off, pagefile automatic management, and the visual-performance set | Visual-performance tweaks only |
| Temp Files | `%TEMP%` + `%SYSTEMROOT%\Temp` purge and Chrome/Firefox cache cleanup | Same |
| Disk Cleanup | `cleanmgr` / DISM system cleanup; restore point offered first | Same cleanup; no restore-point prompt for this step |
| Services | Stops **Windows Update (wuauserv)**, **BITS**, and **Windows Search (WSearch)** and sets them to Manual — with an explicit logged warning that security patches will not install automatically until they are re-enabled | Stops **WSearch only**; Windows Update and BITS are left alone so patching keeps flowing |
| Performance | Ultimate Performance power plan (High Performance fallback) and `explorer.exe` / `dwm.exe` raised to Above Normal priority | Same |

Profile metadata (labels, taglines, descriptions, accent colors) lives in `PROFILE_META` in `source/utils/profiles.py`. The default profile at startup is Gaming (`Config.ACTIVE_PROFILE = GAMING` in `source/utils/config.py`).

## Features

### Tabbed dashboard

The GUI is a custom-built tkinter interface (980×780, non-resizable) with six tabs. Every tab carries a risk label — **High**, **Medium**, or **Low** — so you know what you're getting into before you click:

| Tab | Risk | What it does |
|-----|------|--------------|
| Registry Optimization | High | Disables hibernation (`powercfg /hibernate off`), sets the pagefile to automatic management (PowerShell CIM), and applies visual-performance registry tweaks (best-performance visual effects, snappier menus via `MenuShowDelay`). Gaming applies all tweaks; Cybersecurity applies visual tweaks only. Includes **Restore Previous Registry Values** — every write snapshots the old value to a JSON undo file under `%APPDATA%\NitroCore\registry_undo` first. |
| Temporary File Cleanup | Low | Purges `%TEMP%` and `%SYSTEMROOT%\Temp` (de-duplicated) plus Chrome (`Cache_Data`) and Firefox (`cache2`, profile wildcards resolved) caches, with a before/after MB-freed report. Never recurses into symlinks or NTFS junctions — a junction inside a temp tree could point outside it, so those are skipped fail-closed. |
| Disk Cleanup | Medium | **Refresh Disk Usage** shows per-drive usage for local fixed drives. **Run Windows Disk Cleanup** runs `cleanmgr /verylowdisk`, falling back to `DISM /Online /Cleanup-Image /StartComponentCleanup` if it fails (and tells you *why* it failed). **Clean Old Downloads (30+ days)** moves stale Downloads to the **Recycle Bin** via the Windows shell (`SHFileOperation`) — never permanent deletion; files the shell won't take are left in place and reported. |
| Service Management | High | Gaming stops **Windows Update (wuauserv)**, **BITS**, and **Windows Search (WSearch)** and sets them to Manual. Cybersecurity stops **Search only**, keeping patching alive. Whenever the update services are touched, NitroCore logs an explicit security warning that patches will not install automatically until you re-enable them. |
| Performance Tuning | Low | Switches to the **Ultimate Performance** power plan via `powercfg` (checks first so it never clones a duplicate scheme; falls back to **High Performance** if Ultimate is unavailable) and raises `explorer.exe` / `dwm.exe` to **Above Normal** priority via psutil. |
| Status & Logs | Low | Live scrolling log of every step as it runs. Full logs are also saved to `%APPDATA%\NitroCore\logs` (rotating, 5 MB × 3 backups). |

A **Run All (<profile>)** button runs the full five-step pipeline for the active profile in order.

### Live stats header

CPU %, RAM (% and GB used/total), free disk space, and the active power-plan name — polled continuously, with the expensive queries cached (disk 30 s, power plan 120 s) and the power-plan cache invalidated the moment a pipeline changes it. The periodic snapshot is fetched on a worker thread and rendered back on the UI thread, so the window cannot freeze when the power-plan cache expires.

### Preview Mode (`--dry-run`)

Run the whole pipeline without changing anything:

```powershell
python main.py --dry-run
```

In dry-run mode every mutating module records a human-readable *"would do"* entry instead of acting, and the app prints a numbered report. The real output format (step headers, per-step results, numbered change list, footer) is:

```text
NitroCore dry run — Gaming profile
============================================================
--- Registry ---
...
--- Temp Files ---
...
2 change(s) previewed, 0 applied
  1. Would delete ...
  2. Would delete ...
PREVIEW ONLY — no changes were made.
```

(On a non-Windows machine the Windows-only steps report themselves as skipped instead — the preview still runs, which is how the test suite exercises it.) Dry runs skip the admin-elevation gate and the single-instance lock entirely — a read-only preview never fights you for privileges — and they do not import tkinter or the GUI modules at all. Restore-point creation is skipped in preview mode (nothing will change, so there's nothing to roll back).

### Pip-Boy mode (`--fallout`)

There's also a hidden `--fallout` flag, suppressed from `--help`. And if you click the title bar 7 times… you'll find the Fallout-themed Pip-Boy mode. Its big red "System Purge" button still asks for confirmation, offers a restore point, respects preview mode, and can't double-fire mid-run. Click the header to return to the normal UI.

## Safety model

NitroCore runs elevated and changes system state, so the safety mechanisms are part of the product, not an afterthought:

- **Restore-point gating.** Before high-impact steps (registry and services on either profile, plus disk cleanup on Gaming — `step_requires_restore_prompt()` in `source/utils/profiles.py`), NitroCore offers to create a system restore point via PowerShell `Checkpoint-Computer` (`-RestorePointType MODIFY_SETTINGS`, run with `-NoProfile -NonInteractive`, time-bounded at 180 s). If creation fails, the run **blocks** with a dialog: *Try Again / Continue Without It / Abort* — it never silently proceeds without the safety net.
- **Registry undo snapshots.** Every registry write snapshots the previous value to a JSON undo file under `%APPDATA%\NitroCore\registry_undo` before writing, and **Restore Previous Registry Values** replays it. Undo restores refuse any snapshot entry outside HKCU, so a planted undo file can never turn this elevated process into a registry writer in another hive.
- **Recycle Bin, never permanent deletion**, for old Downloads (Windows shell `SHFileOperation`); files the shell refuses are left in place and reported.
- **Reparse-point fail-closed cleanup.** Temp and cache purges never recurse into symlinks or NTFS junctions.
- **System32-resolved helpers.** The executables NitroCore shells out to (`powershell`, `powercfg`, `cleanmgr`, `dism`) are resolved via `%SystemRoot%\System32` (`system_tool_path()` in `source/utils/platform.py`), never via PATH — a PATH-hijacked binary can never be picked up with admin rights.
- **No `shell=True` anywhere** — all subprocess calls use argument lists, and the subprocess calls are time-bounded so a hung helper reports an error instead of wedging a worker thread.
- **No telemetry, no network.** NitroCore collects no telemetry and makes no network connections; per [SECURITY.md](SECURITY.md), unexpected network activity from a NitroCore binary is a security issue to report, not intended behavior.
- **Honest trade-offs.** When the Gaming profile sets Windows Update and BITS to Manual, the app logs an explicit security warning naming the trade — patches will not install automatically until those services are re-enabled.

## Installation

### Option A — winget (easiest)

```powershell
winget install TheRealJesusTheHacker.NitroCore
```

The winget manifests for the current version (1.1.6) are published in microsoft/winget-pkgs; see [winget/README.md](winget/README.md) for the manifest reference, installer URL, and verified SHA-256.

### Option B — Ready-to-run .exe

1. Download `NitroCoreOptimizer.exe` from the [Releases](https://github.com/TheRealJesusTheHacker/NitroCore/releases) page.
2. **Verify it** (optional but smart) — compare against `SHA256SUMS.txt` from the same release:

   ```powershell
   certutil -hashfile NitroCoreOptimizer.exe SHA256
   ```

3. Run it — double-click is enough. NitroCore needs elevation to modify system settings, so it asks for it itself when it starts (one UAC prompt). If you decline the prompt, it exits with an "Access Denied" message and exit code 1 instead of half-working.

### Option B2 — Portable edition (`.zip`, no install) — shipped in v1.1.4

The portable edition is the same application built as a folder (PyInstaller one-folder build from `NitroCore/nitrocore-portable.spec`) instead of a single file: no installer, no setup step. The release workflow (`.github/workflows/release.yml`) builds and zips it on a Windows runner, and it ships as of [v1.1.4](https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.4). The 1.1.3 release (and every earlier one) lists only `NitroCoreOptimizer.exe` and `SHA256SUMS.txt`; if a Releases page does not list `NitroCorePortable.zip`, that release predates the portable edition.

From v1.1.4 onward:

1. Download `NitroCorePortable.zip` from that release and verify it against `SHA256SUMS.txt` from the same release (same `certutil` check as Option B, run on the `.zip`).
2. Unzip it anywhere — a USB stick works. Keep the folder together: `NitroCoreOptimizer.exe` needs its `_internal` folder beside it.
3. Run `NitroCoreOptimizer.exe` from that folder — it asks for elevation itself, exactly as in Option B. (Since v1.1.5 it also starts correctly when another program launches it, e.g. from the Technician's Toolkit bundle; earlier builds could only be started from Explorer or a shell.)

Portable means *no install*, not *no footprint*: NitroCore still writes its log and registry-undo snapshots under `%APPDATA%\NitroCore`, and its tuning still applies to the machine it runs on. The full honest list ships inside the zip as `README-PORTABLE.txt` (source: `NitroCore/portable/README-PORTABLE.txt`).

### Option C — From source

Requires Python 3.9+ on Windows.

```powershell
git clone https://github.com/TheRealJesusTheHacker/NitroCore.git
cd NitroCore\NitroCore
pip install -r requirements.txt
python main.py
```

The GUI path enforces the admin gate described above — started from a normal shell, the program relaunches itself elevated (one UAC prompt) rather than refusing to run.

### Option D — pip install from source / local wheel

The packaging in the root `pyproject.toml` (and `NitroCore/setup.py`) builds the importable `source` package — the same package `main.py` imports as `source.*`. From the repository root:

```powershell
pip install .
```

…or build a wheel first and install that:

```powershell
python -m build --wheel
pip install dist\nitrocore-1.1.6-py3-none-any.whl
```

Two honest caveats:

- There is **no console-script entry point** — neither `pyproject.toml` nor `setup.py` defines one, so pip does not create a `nitrocore` command. The application is run as `python main.py` from the `NitroCore\` folder (Option C), or via the `.exe` / winget installs. The pip path installs the `source` package itself, which is what the test suite and other tooling import.
- Runtime dependencies are pinned exactly in `NitroCore/requirements.txt` (`psutil==7.0.0`, `pywin32==312`); `pywin32` is Windows-only, so on non-Windows platforms the corresponding entry in `pyproject.toml` carries a `sys_platform == 'win32'` marker and is skipped.

## Usage

```powershell
# Full GUI (the program asks for elevation itself at startup)
python main.py

# Headless dry-run preview of the active profile — changes nothing,
# needs no elevation, prints the report to stdout
python main.py --dry-run

# Start directly in the hidden Pip-Boy theme
python main.py --fallout
```

Those are the only command-line flags: `--dry-run` and the hidden `--fallout`, both parsed in `source/utils/config.py` (`Config.parse_arguments()`). Everything else happens in the GUI:

1. **Pick a profile** — Gaming or Cybersecurity — on the selector cards at the top of the dashboard.
2. **Run a single tab's action**, or press **Run All (<profile>)** to run Registry → Temp Files → Disk Cleanup → Services → Performance in order.
3. **Answer the restore-point prompt** when a high-impact step offers one. If restore-point creation fails, choose *Try Again*, *Continue Without It*, or *Abort* — the run will not proceed silently.
4. **Watch the Status & Logs tab** for the live per-step results, and use **Restore Previous Registry Values** on the Registry tab if you want the last registry run undone.

Long operations run on daemon worker threads (`source/modules/async_worker.py`), so the window stays responsive while a step runs.

## How it works

- **`NitroCore/main.py`** — entry point: parses flags, runs the headless preview and returns if `--dry-run` is set, otherwise enforces the admin gate (relaunches itself elevated via the UAC prompt; exit code 1 if the user declines), enforces single-instance via `LifecycleManager`, then builds the GUI. GUI imports are deferred until after the preview path so a dry run never pays the tkinter import cost.
- **`source/modules/`** — the five pipeline workers (`registry`, `temp_files`, `disk_cleanup`, `services`, `performance`) plus `system_stats` (telemetry for the header) and `async_worker` (daemon-thread dispatch so long operations never freeze the UI).
- **`source/utils/profiles.py`** — profile definitions and the pipeline layout (`get_pipeline`, `step_requires_restore_prompt`, `execute_step`).
- **`source/utils/preview.py`** — the process-wide dry-run recorder behind Preview Mode (`preview.start()` / `record()` / `report()`).
- **`source/utils/config.py`** — global runtime flags (`ACTIVE_PROFILE`, `DRY_RUN`, `PI_BOY_MODE`, …) and CLI parsing.
- **`source/utils/restore_point.py`** — restore-point creation with dry-run and platform guards.
- **`source/utils/platform.py`** — every Windows-only assumption centralized (`IS_WINDOWS`, `system_tool_path`, `hidden_subprocess_kwargs`), so the app degrades gracefully — reporting steps as skipped — instead of crashing on other platforms.
- **`source/utils/logger.py`** — thread-safe logging to console and to the rotating file under `%APPDATA%\NitroCore\logs`.
- **`source/gui/`** — custom tkinter widgets (buttons, dialogs, tabs, theme, fonts, profile selector, stats header, progress panel) — no stock-ttk look.

## Files NitroCore writes

| Location | What |
|---|---|
| `%APPDATA%\NitroCore\logs\nitrocore.log` | Rotating application log (5 MB per file, 3 backups) |
| `%APPDATA%\NitroCore\registry_undo\undo-*.json` | Registry undo snapshots — the previous value of every registry write, for **Restore Previous Registry Values** |

NitroCore writes nothing else of its own outside the system locations its cleanup and tuning steps act on (temp folders, the Recycle Bin, the registry, service configuration, and the active power plan).

## Development and testing

Clone the repo (Option C above), then install the dev requirements. On Windows, install both files; on Linux/macOS, the dev file alone is enough and is deliberately Linux-safe (it does not pull in `pywin32`):

```powershell
pip install -r NitroCore\requirements-dev.txt
```

Run the suite, linters, and formatter check — the same commands CI runs:

```powershell
python -m pytest NitroCore\tests -v
ruff check NitroCore
black --check NitroCore
```

**Verified test count (2026-10-23, from a fresh clone of HEAD `9a9ce2e`):** `pytest --collect-only` collects **196 tests**; a full run on Linux (Python 3.12, `psutil==7.0.0`, `pytest==8.3.5`) reports **195 passed, 1 skipped**. The suite only exercises non-mutating logic and dry-run paths — no test mutates the registry, services, or filesystem — and Windows-only paths are marked `windows_only`. Test files map to the modules they cover (`test_registry_undo.py`, `test_services.py`, `test_temp_files_dryrun.py`, `test_version.py`, and the rest under `NitroCore/tests/`).

CI (`.github/workflows/ci.yml`) runs on every push and pull request to `main`: a byte-compile check on Ubuntu and on Windows, the pytest suite on Ubuntu, and ruff + black checks. CodeQL analysis (`.github/workflows/codeql.yml`) runs on push, pull request, and a weekly schedule. Releases are built by `.github/workflows/release.yml` on `v*` tags (a manual `workflow_dispatch` run builds the same artifacts without uploading a release): PyInstaller builds the `.exe` on a Windows runner, the same job also builds the portable one-folder edition from `nitrocore-portable.spec` and zips it as `NitroCorePortable.zip`, `SHA256SUMS.txt` is generated covering both downloads, build-provenance attestations are created, and the files are uploaded to the GitHub Release. The portable zip ships starting with [v1.1.4](https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.4) — releases up to and including 1.1.3 contain only the `.exe` and `SHA256SUMS.txt`. There is no PyPI publish step anywhere in the repo.

Building the `.exe` locally uses the same spec the release workflow uses:

```powershell
cd NitroCore
pip install pyinstaller==6.11.1
pyinstaller --noconfirm nitrocore.spec
```

Building the portable edition locally uses the portable spec the same way — it produces a `NitroCoreOptimizer` folder under `dist` instead of a single file:

```powershell
cd NitroCore
pyinstaller --noconfirm nitrocore-portable.spec
```

## Verified downloads

Every release ships:

- **`NitroCoreOptimizer.exe`** — the standalone single-file build.
- **`NitroCorePortable.zip`** — the portable edition (shipped starting with [v1.1.4](https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.4); earlier releases ship the single-file `.exe` only).
- **`SHA256SUMS.txt`** — hashes for every release artifact, so you can confirm your download wasn't tampered with.
- **Signed build-provenance attestations** — cryptographic proof the binaries were built from this repo's code.

Release binaries are currently **unsigned** — Windows SmartScreen will warn on first run. Verify the hash before trusting the binary. (Code signing is a planned manual release step.)

## Roadmap

From [CHANGELOG.md](CHANGELOG.md)'s Unreleased section and the project's own notes:

- **Portable edition** — shipped: the first `NitroCorePortable.zip` was released in [v1.1.4](https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.4) (one-folder spec `NitroCore/nitrocore-portable.spec`, release-workflow zip step, `README-PORTABLE.txt`).
- **Code-signed release binaries** — planned manual release step (see SECURITY.md); removes the SmartScreen warning.
- **GUI screenshot for this README** — needs a capture on a real Windows machine, which isn't available in the current dev environment.
- The changelog entries for headless-preview startup, temp/Downloads scan performance, stats polling off the UI thread, and the bug-hunt #2 fixes shipped in v1.1.4 — see the changelog for the itemized list.

## Contributing

Pull requests are welcome. A few ground rules:

- **Never break intended functionality** to satisfy a scanner — fix *around* the feature, and document anything that can't be fixed without neutering it.
- New behavior needs Preview Mode coverage and, where it mutates the system, a restore-point prompt and (for registry) undo snapshots.
- Run the checks before pushing: `python -m pytest NitroCore/tests`, `ruff check NitroCore`, `black --check NitroCore`.
- Use the PR template's safety checklist.

## Donations, contact, changelog, and license

**Donations** — if this tool earned its keep, BTC is welcome:

```text
bc1qvydns2fmyjzj55wzxq7ta28nxdhcmu9l9m6yg0
```

**Contact** — business inquiries: **Sentinelsafeguard@outlook.com**

**Security vulnerabilities:** do not open a public issue — email Sentinelsafeguard@outlook.com instead. See [SECURITY.md](SECURITY.md).

**Changelog** — all notable changes are documented in [CHANGELOG.md](CHANGELOG.md).

**License** — MIT License, copyright (c) 2026 JesusTheHacker — see [LICENSE](LICENSE) for the full text.
