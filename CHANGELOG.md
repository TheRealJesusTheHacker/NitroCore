# Changelog

All notable changes to NitroCore are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] — 2026-09-18

The first public-ready release.

### Added
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
