"""Read-only / guard-path tests for source.modules.disk_cleanup.

``get_disk_usage`` only reads telemetry. ``clean_downloads`` is exercised
in dry-run (scan-only) mode against a fake Downloads folder, so nothing is
recycled or deleted. The real ``cleanmgr``/DISM path is Windows-only and
is never invoked here.
"""

import os
import sys
import time

import pytest
from source.modules.disk_cleanup import DiskCleanup, _recycle_path_windows
from source.utils.config import Config
from source.utils.preview import preview


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows guard")
def test_recycle_path_guard_off_windows(tmp_path):
    # fail-closed: without the Windows shell there is nothing to recycle with
    assert _recycle_path_windows(str(tmp_path)) is False


def test_min_disk_space_threshold():
    assert DiskCleanup().min_disk_space_gb == 10.0


def test_get_disk_usage_shape():
    usage = DiskCleanup().get_disk_usage()
    assert isinstance(usage, dict)
    for device, stats in usage.items():
        assert {"total_gb", "used_gb", "free_gb", "percent"} <= set(stats)
        assert stats["total_gb"] >= stats["free_gb"] >= 0


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows guard")
def test_clean_system_files_guard_off_windows():
    assert DiskCleanup().clean_system_files().startswith("Skipped:")


def _point_downloads_at(monkeypatch, path):
    # clean_downloads() builds its path from %USERPROFILE%\Downloads
    monkeypatch.setattr(os.path, "expandvars", lambda s: str(path))


def test_clean_downloads_missing_folder(monkeypatch, tmp_path):
    _point_downloads_at(monkeypatch, tmp_path / "no-such-dir")
    assert DiskCleanup().clean_downloads() == "Downloads folder not found"


def test_clean_downloads_dry_run_counts_old_files_only(monkeypatch, tmp_path):
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    old = downloads / "old-setup.exe"
    old.write_bytes(b"0" * 2048)
    ancient = time.time() - 60 * 86400  # 60 days ago
    os.utime(old, (ancient, ancient))
    fresh = downloads / "notes.txt"
    fresh.write_bytes(b"hello")

    _point_downloads_at(monkeypatch, downloads)
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    preview.start()

    result = DiskCleanup().clean_downloads(retention_days=30)

    assert "Would move 1 files" in result
    assert "(preview)" in result
    assert old.exists() and fresh.exists()  # dry run: nothing recycled
    entries = preview.report()
    assert len(entries) == 1
    assert "Recycle Bin" in entries[0]
    assert "30 days" in entries[0]


def test_clean_downloads_dry_run_keeps_everything_when_all_recent(
    monkeypatch, tmp_path
):
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "recent.txt").write_bytes(b"data")

    _point_downloads_at(monkeypatch, downloads)
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    preview.start()

    result = DiskCleanup().clean_downloads(retention_days=30)

    assert "Would move 0 files" in result
    assert preview.report() == [] or "0 file(s)" in preview.report()[0]
