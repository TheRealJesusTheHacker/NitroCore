# Changelog

All notable changes to NitroCore are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.1.6] - 2026-10-20

Visual release: NitroCore gets its own colors. No optimizer behavior
changes — same layout, same words, same safety model. The 1.1.5
launcher fix (asInvoker manifest, self-elevation at startup, the
release workflow's staged start proof) is untouched, and the staged
start proof still gates this release before anything is published.

Release: https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.6

### Changed
- **New palette — "nitrous."** The interface now wears NitroCore's own
  namesake colors instead of the generic grey-and-orange theme it
  shipped with: carbon-black surfaces, a nitrous-azure primary, and
  cool steel text. The two profiles keep distinct accent colors, now
  both from the nitrous family — Gaming is azure (`#2EA3FF`),
  Cybersecurity is pale nitrous (`#7CC4FF`); they were orange and teal.
  All colors live in one place (`source/gui/theme.py`); the profile
  accents in `source/utils/profiles.py` are pinned to it by test.
- **Readable by measurement, not by eye.** Text painted on
  accent-colored buttons is now dark instead of white — white on the
  new azure measures only ~2.7:1. Every text/background pairing the
  interface renders now measures at least 4.5:1 (WCAG AA), including
  hover and pressed states, the risk badges, and disabled buttons.
  One quiet fix falls out of this: the High-risk badge previously
  measured ~4.35:1; its pill tint is shallower now and it passes.
- **Danger reads as danger, fleet-wide.** Destructive-action buttons
  now use the Sentinel fleet's danger red (`#B03A2E` with white text,
  6.02:1) — the same red as the other Sentinel tools — instead of the
  brighter red the old theme used for everything. Error *text* in the
  log keeps the brighter signal red on purpose: the darker fleet red
  measures only ~3.4:1 as text on a dark surface and would be harder
  to read.
- The hidden Pip-Boy mode is unchanged, green and all. It's supposed
  to look like that.

### Added
- **`tests/test_theme.py`.** Pins the palette constants to the design
  values, pins the profile accents to the theme, recomputes the
  derived tones (hover, soft border, faint, disabled) from their
  documented formulas, asserts every rendered pairing measures
  >= 4.5:1, and fails if a color literal ever appears in a gui module
  outside `theme.py` again.

## [1.1.5] - 2026-10-20

Field fix: NitroCore would not start when another program launched it.

Release: https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.5

### Fixed
- **Start failure from launchers (WinError 740).** The 1.1.4
  executables carried a `requireAdministrator` manifest. Windows
  Explorer can start such a program (it shows the UAC prompt via
  ShellExecute), but a program that starts NitroCore directly —
  the Technician's Toolkit launcher, a task scheduler, a script —
  uses CreateProcess, which cannot show the prompt and refuses the
  start outright: "The requested operation requires elevation."
  In the Toolkit, NitroCore's card therefore showed "could not be
  started" while Argus and the other tools started normally
  (field report, 2026-10-20; reproduced on a Windows runner with a
  non-administrator account in both the standalone portable layout
  and the bundle layout). The executables now ship with an
  `asInvoker` manifest — any launcher can start them — and
  NitroCore raises the UAC prompt itself at startup
  (`relaunch_elevated()` in `main.py`): accept it and the program
  runs fully elevated exactly as before; decline it and the
  program exits with the same "Access Denied" message as before.
  No optimizer behavior changes.

### Added
- **`--self-check` mode.** A headless health proof in the fleet's
  staged-self-check pattern: prints one line
  (`NitroCore 1.1.5 self-check OK`), optionally writes it to the
  file named by the `NITROCORE_SELF_CHECK_OUT` environment
  variable, and exits 0. No GUI, no changes, no elevation. The
  release workflow now runs a staged start proof on its Windows
  runner before anything is published: it assembles the
  portable in both the standalone layout and a bundle-style
  layout and starts it the way the Toolkit launcher does —
  including as a non-administrator user — so this failure mode
  cannot ship again unnoticed.

## [1.1.4] - 2026-10-20

Packaging release that ships the portable edition
(`NitroCorePortable.zip`) for the first time, together with the
bug-fix, performance, and packaging work accumulated on `main`
since 1.1.3 (itemized below). No new optimizer behavior is
introduced beyond those itemized fixes and performance changes.

Release: https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.4

### Added
- Portable edition packaging: `NitroCore/nitrocore-portable.spec`
  (PyInstaller one-folder build of the same `main.py` entry point,
  same datas/hidden imports/icon/elevation as `nitrocore.spec`) and
  `NitroCore/portable/README-PORTABLE.txt`. The release workflow now
  builds the portable folder on its Windows runner, zips it as
  `NitroCorePortable.zip`, covers it in `SHA256SUMS.txt` and the
  build-provenance attestation, and uploads it with the release.
  This release (1.1.4) is the first to ship the portable zip;
  1.1.3 and earlier ship only the single-file .exe.
  "Portable" means no installer - NitroCore still requires admin
  rights and still writes logs/undo snapshots under
  %APPDATA%\NitroCore (documented in README-PORTABLE.txt).

### Performance
- Headless `--dry-run` no longer imports tkinter or the GUI modules
  (deferred until the window is actually built), cutting preview startup
  substantially
- Temp purge and Downloads scans are faster: removed a redundant
  per-directory existence probe from the purge walk, and the Downloads
  scan now compares epoch timestamps instead of building a datetime
  object for every file
- Stats header polls no longer run on the UI thread — the periodic
  snapshot (which can spawn `powercfg`) is fetched on a worker thread
  and rendered back on the UI thread, so the window cannot freeze when
  the power-plan cache expires

### Removed
- Dead GUI modules `source/gui/layout.py` and `source/gui/entry.py`
  (imported nowhere) and a write-only attribute in the progress panel

### Fixed
- Registry writes and registry-undo restores no longer leak the key
  handle when the value write fails — `CloseKey` sat after the write in
  both paths, the W-4/W-5 pattern already fixed for service handles
  (bug hunt #2 2026-10-19; 3 new tests in `tests/test_bughunt2.py`)
- Downloads cleanup no longer crashes when the top-level scan fails
  with a non-PermissionError `OSError` (e.g. the Downloads path is a
  plain file); it reports a zero-clean result like the temp purge does
  (bug hunt #2 2026-10-19)
- Service stops now report unexpected (non-Windows-API) failures
  per-service instead of aborting the whole services step and discarding
  every result — the same guard startup changes received in W-5, applied
  to the stop path (bug hunt 2026-10-13, BH2-1)
- Stop polling no longer mistakes a just-issued stop for a timeout: a
  service still reporting "running" right after the stop request keeps
  being polled until it stops or the deadline passes (BH2-2)
- Registry undo restore no longer crashes on a corrupt or hand-edited
  undo file whose JSON parses but has the wrong shape — it reports the
  file as unreadable instead (BH2-3)
- The registry module's `powercfg` (hibernation) and PowerShell
  (pagefile) calls are now time-bounded like every other subprocess
  call in the app (BH2-4)
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
