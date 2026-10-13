# Changelog

All notable changes to NitroCore are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed
- Service startup changes no longer leak the service handle when
  `ChangeServiceConfig` fails, and a failure is reported per-service instead
  of aborting the remaining services in the step (audit 2026-10-13, W-5)
- Power-plan switching (`powercfg`) is now time-bounded like every other
  subprocess call in the app — a hung `powercfg` reports a Power Plan Error
  instead of wedging the worker thread (audit 2026-10-13, W-6)
- Import ordering in three modules restored to the project's ruff style,
  returning the CI lint job to green

### Documentation
- winget README now documents the published 1.1.3 manifests (hash verified
  against the v1.1.3 release) instead of only the original 1.1.2 submission

## [1.1.3] - 2026-10-11

### Security
- Registry undo restore now refuses any snapshot entry outside HKCU — a
  planted `%APPDATA%\NitroCore\registry_undo\undo-*.json` can never turn this
  elevated process into a registry writer in another hive (every snapshot the
  app writes is HKCU)
- Helper executables (`powershell`, `powercfg`, `cleanmgr`, `dism`) are now
  resolved via `%SystemRoot%\System32` instead of PATH (`system_tool_path()`),
  so a PATH-hijacked binary can never be picked up with admin rights
- Build and dev dependencies fully pinned (`setuptools==75.8.2` in
  `pyproject.toml`; exact pins across `requirements.txt` /
  `requirements-dev.txt`) for reproducible privileged builds

### Added
- First pytest suite (`NitroCore/tests/`, 90+ tests): profiles/pipeline logic,
  preview recorder, CLI parsing, reparse-point fail-closed gate, registry
  undo serialization, dry-run paths for temp/disk/performance/services, and
  restore-point guards. Windows-only paths are marked `windows_only` and
  skipped off Windows; no test mutates the registry, services, or filesystem.
- `pyproject.toml`: pytest config, ruff (E/F/I/W) and black (88 cols) settings.
- CI now runs the pytest suite and ruff + black checks on every push/PR
  (ubuntu runner, SHA-pinned actions).
- `requirements-dev.txt` is now Linux-safe (no longer pulls in pywin32 via
  `requirements.txt`); adds `ruff`.
- Issue templates (bug report, feature request) and a PR template with a
  safety checklist for system-mutating changes.
- README rewritten with full per-tab feature rundown, architecture notes,
  Preview Mode docs, verification guide, roadmap, and a Donations section.

### Fixed
- Registry undo: snapshots are now cleared from memory once written to disk,
  so repeated runs can't accumulate stale snapshots (a later "undo" could
  previously revert values from an earlier run instead of the run being undone)
- Temp/Downloads cleanup: pathologically deep directory trees (deeper than the
  interpreter recursion limit) now skip that subtree instead of failing the
  whole cleanup step with a `RecursionError`
- Run All pipeline now invalidates the cached power-plan reading on
  completion, so the header can't show a stale plan for up to 120 s (the
  Pip-Boy purge path already did this)
- Service Manager: service handles are now released in `finally`, fixing a
  handle leak when a query/control call raised after the handle was opened
- Restore-point PowerShell call now runs with `-NonInteractive`, matching the
  pagefile optimization call site

### Changed
- Whole codebase formatted with black and ruff --fix (whitespace, import
  order, two genuinely-unused imports removed). No behavior changes.

## [1.1.2] - 2026-10-10

### Security
- Pillow bumped 11.0.0 → 12.3.0 (known CVEs in 11.0.0); moved to dev requirements (unused at runtime)
- Removed the dead `wmic` fallback — zero `shell=True` calls remain repo-wide
- Registry reads now close key handles in `finally` (no leak on failed reads)
- Admin-denial and already-running exits now return code 1 instead of 0
- Removed dead code: `tray.py` (undeclared pystray dependency), unused helpers
- CI jobs pinned to least-privilege permissions; release actions pinned to commit SHAs
- `python_requires` corrected to >=3.9 (codebase uses 3.9+ syntax)

### Performance
- `SHFILEOPSTRUCTW` ctypes struct hoisted to module level (was rebuilt per recycled file)
- Disk usage cached 30 s instead of re-queried every 2 s tick
- `FontEngine` skips font rebuild when the family is unchanged
- Power-plan cache invalidation wired into pipeline completion

## [1.1.1] - 2026-09-25

### Fixed
- Critical crash-on-launch fix: the new `ToggleSwitch` widget in the v1.1.0 GUI
  redesign stored its size in `self._w` / `self._h`, clobbering tkinter's internal
  Tcl widget-name attribute — the app died with `TclError: invalid command name`
  before the window ever drew. Renamed to `self._tw` / `self._th`. The v1.1.0
  release is broken on every machine; everyone should upgrade to v1.1.1.

## [1.1.0] - 2026-09-25

### Fixed — bug bounty security & safety fixes
- H-1: the Pip-Boy "System Purge" button no longer runs the full destructive
  pipeline with one click. It now asks for explicit confirmation (themed
  `ConfirmDialog`), offers a restore point, respects preview mode, and can't
  double-fire while a run is active. Entering Pip-Boy mode still takes 7
  clicks; clicking the header exits back to the normal UI.
- H-2: "Clean Old Downloads" now asks for explicit confirmation and a
  restore point before touching user files; deleted files are moved to the
  Recycle Bin (via `SHFileOperation`) instead of being permanently destroyed,
  and files that can't be recycled are left in place and reported.
- H-3: recursive cleanup in temp files and Downloads now skips NTFS
  junctions, symlinks, and reparse points (fail-closed) so a junction can
  never redirect deletion outside the intended tree.
- M-1: a failed restore-point creation now BLOCKS the pipeline. The user gets
  a "Restore Point Failed" dialog with Retry / Continue Without It / Abort —
  the run never silently proceeds without its safety net.
- M-2: service optimization now logs an explicit security warning whenever
  Windows Update (wuauserv) or BITS is set to Manual, in both live and
  preview runs.
- M-3: `powercfg /l` is checked for the Ultimate Performance scheme before
  duplicating, so repeated clicks no longer clone power plans.
- M-4: every registry write snapshots the previous value first; snapshots
  persist to timestamped JSON undo files under
  `%APPDATA%\NitroCore\registry_undo\`, and a new "Restore Previous Registry
  Values" button restores the most recent snapshot (one-click undo).
- M-5: `setup.py` now points at the real `source/` package layout and the
  correct GitHub URL (`TheRealJesusTheHacker/NitroCore`); a `VERSION` file
  (`1.0.2`) is the single version source.
- M-6: runtime and build dependencies are exactly pinned (`requirements.txt`,
  PyInstaller in release CI) for reproducible privileged builds.
- M-7: `upx=False` in the PyInstaller spec (UPX trips AV heuristics); dead
  `yaml` hidden import removed; releases documented as unsigned with
  SHA256SUMS verification until code signing is configured (see SECURITY.md).
- L-2: removed the misleading "QueueHandler" comment in the logger — handlers
  are direct (thread-safe via stdlib locking), and the docs now say so.
- L-3: `hash_password_secure()` now uses PBKDF2-HMAC-SHA256 (600k iterations)
  instead of single-round SHA-256 (still unused by the app).
- L-4: progress panel `reset()` stops the indeterminate bar animation.
- L-5: worker completion callbacks are guarded against GUI teardown
  (`_safe_after`, TclError-safe `after`, no double `on_complete` in
  `AsyncWorker`).
- L-6: service stop now polls `QueryServiceStatus` until STOPPED (15s) and
  reports the observed state instead of fire-and-forget.
- L-7: `cleanmgr` failures (return code + stderr) are logged before the DISM
  fallback instead of being swallowed.
- L-8: removed dead spec metadata; version strings unified on 1.0.2.
- L-9: Pip-Boy mode exits via header click; click counter resets on entry.

### Changed — GUI design overhaul
- New single design system (`source/gui/theme.py`): one dark palette, one
  spacing scale, shared `Card`, `Badge`, and `ToggleSwitch` primitives, plus
  color helpers (`darken`, `tint`, `mix`).
- Buttons are now rounded canvas-drawn controls with real hover, pressed, and
  disabled states (clicks fire on release, like native buttons).
- New branded header: accent "N" logo mark, display title, and a friendly
  on/off switch replacing the "Preview only" checkbox.
- Stat cards, profile cards, and the progress panel are now bordered cards;
  the active profile shows an accent ring, a tinted fill, and a selection dot.
- Tab risk levels ("High risk" etc.) are now tinted pill badges; action
  buttons are left-aligned with subtle borders; the log view sits in a sunken
  bordered frame.
- Friendlier microcopy throughout ("Ready when you are.", "All done",
  "Welcome to NitroCore — pick a profile above…"), with no behavior changes.
- Dialogs restyled with icon badges and rounded buttons; the restore-point
  prompt now reads in plain language.
- Focus ring added to text entries; the system-tray icon is now a rounded
  accent badge matching the in-app brand.
- Extended the type scale (`display`, `subheader`, `small`, `caption`) in
  `FontEngine`; all existing roles unchanged.

## [1.0.2] — 2026-09-18

### Fixed
- Pagefile optimization no longer fails on Windows 11 24H2+: `wmic` was removed
  from Windows, so the step now uses PowerShell CIM
  (`Get-CimInstance Win32_ComputerSystem | Set-CimInstance ...`) with a `wmic`
  fallback for older systems.

### Changed
- Repository renamed from `NitroCore1.0` to `NitroCore` — the release tags carry
  the version, so it no longer belongs in the name. All in-repo links updated.

## [1.0.1] — 2026-09-18

### Fixed
- Temp File Cleanup no longer fails outright when a temp subfolder still holds
  locked or in-use files: the purger now skips unremovable entries (including
  non-empty directories left behind) instead of aborting the whole run.
- The "Preview only — don't change anything" toggle moved from the crowded tab
  bar into the header row, so its label is never clipped between the Status tab
  and the Run All button.

### Changed
- Long descriptions in tab headers and profile cards now wrap to a second line
  instead of being cut off mid-sentence.
- The progress bar and summary line stay hidden while idle so the dashboard
  sits tighter; they appear only while an operation is running.

## [1.0.0] — 2026-09-18

The first public-ready release.

### Added
- Preview (dry-run) mode: a "Preview only — don't change anything" toggle in the
  GUI plus `python main.py --dry-run` on the CLI. Scans everything and reports
  exactly what would change, with "PREVIEW ONLY — no changes were made." at the
  end. No admin rights needed, no restore point created.
- `SECURITY.md` with vulnerability reporting policy and telemetry-free pledge.
- Every release ships `SHA256SUMS.txt` so downloads can be verified.
- GitHub Pages landing page (`docs/`) and draft winget manifests (`winget/`).
- Windows `.exe` built automatically by the release workflow (`NitroCoreOptimizer.exe`).
- Restore-point dialog with plain-language confirmation before registry, service,
  and disk changes (`source/gui/dialogs.py`, wired into `source/gui/tabs.py`).
- New `source/utils/platform.py`: centralizes every Windows-only assumption so the
  app degrades gracefully instead of crashing on other platforms.
- MIT License, professional README with badges / install / usage / safety / FAQ,
  this changelog, `.gitignore`, and GitHub Actions CI + release workflows.

### Fixed
- Crashes from unguarded `ctypes.windll` and `subprocess.STARTUPINFO` usage on
  non-Windows platforms.
- Admin-check failure path no longer calls a Windows-only message box before exiting.
- Background worker threads no longer touch Tkinter widgets directly — all UI
  updates are marshalled to the main thread via `after()`.

### Changed
- Fewer redundant subprocess calls, cached repeated lookups, leaner file scans.
- UI copy rewritten in plain language for non-technical users: every action
  explains what it does, with progress feedback and clear success/failure messages.
- Repository layout flattened — the app now lives at `NitroCore/` at the repo root.
- Removed all committed `__pycache__` bytecode from version control.

### Kept
- The Pip-Boy easter egg. Obviously.
