# Changelog

All notable changes to NitroCore are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
