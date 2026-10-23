# ⚡ NitroCore — application source

This folder is the NitroCore application itself: entry point, importable `source` package, tests, packaging files, and assets. NitroCore is a safety-first Windows system optimizer with two one-click profiles (Gaming and Cybersecurity), a preview mode, restore-point gating, and registry undo snapshots.

👉 **Full documentation — features, profiles, install options (winget / .exe / source / pip), usage, safety model, and roadmap — is in the [main README](../README.md).**

Current version: **1.1.6**, read at build time from [`VERSION`](VERSION) by `setup.py`, and kept in sync with `pyproject.toml` and `source/__init__.py` — `tests/test_version.py` asserts all three agree.

## Quick start (from source)

Requires Python 3.9+ on Windows. Run from this folder **as administrator**:

```powershell
pip install -r requirements.txt
python main.py
```

Without admin rights, the GUI path tells you and exits with code 1 — it can't tune the system otherwise. The one path that needs no elevation is the headless preview, which changes nothing:

```powershell
python main.py --dry-run
```

## Layout

- `main.py` — entry point: CLI flags (`--dry-run`, `--self-check`, hidden `--fallout`), admin gate, single-instance mutex, GUI construction, headless preview runner
- `source/` — the importable package (this is what the wheel built from the repo-root `pyproject.toml` / this folder's `setup.py` ships)
  - `source/gui/` — dashboard UI: tabs, custom widgets, theme, fonts, profile selector, stats header, progress panel
  - `source/modules/` — the five pipeline workers (`registry`, `temp_files`, `disk_cleanup`, `services`, `performance`) plus `system_stats` and `async_worker`
  - `source/utils/` — profiles and pipeline layout, dry-run preview recorder, config/CLI parsing, restore points, platform helpers, logging, lifecycle (single-instance)
- `tests/` — pytest suite (196 tests collected; non-mutating logic and dry-run paths only). Run it from the repo root: `python -m pytest NitroCore/tests`
- `assets/` — application icon (`icon.ico`) and its generator script (`create_icon.py`)
- `requirements.txt` — pinned runtime dependencies (`psutil==7.0.0`, `pywin32==312`)
- `requirements-dev.txt` — pinned test/lint tooling; deliberately Linux-safe (does not pull in `pywin32`)
- `nitrocore.spec` — PyInstaller spec used to build the release `.exe`
- `nitrocore-portable.spec` — PyInstaller one-folder spec for the portable edition; the release workflow zips its output as `NitroCorePortable.zip` (shipped starting with [v1.1.4](https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.1.4))
- `portable/` — `README-PORTABLE.txt`, the honest what's-in-the-zip note the release workflow copies into `NitroCorePortable.zip`
- `setup.py` — setuptools build for the `source` package; version from `VERSION`, dependencies from `requirements.txt`
- `VERSION` — the version file for this folder's build
- `MANIFEST.in` / `LICENSE` — packaging manifest and the MIT license text (same license as the repo-root [`LICENSE`](../LICENSE))
