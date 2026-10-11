"""Dry-run (read-only) tests for TempFileCleaner.

``_fast_dir_purge(..., execute=False)`` only scans — it counts what *would*
be removed without deleting anything — so these tests are safe on every
platform, including CI. The mutating path (``execute=True``) is never
exercised here.
"""

from source.modules.temp_files import TempFileCleaner
from source.utils.config import Config
from source.utils.preview import preview


def _build_tree(root):
    (root / "a.txt").write_bytes(b"x" * 100)
    sub = root / "sub"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"y" * 200)
    (sub / "nested").mkdir()
    (sub / "nested" / "c.txt").write_bytes(b"z" * 300)
    return 600  # total bytes across the tree


def test_fast_dir_purge_scan_counts_without_deleting(tmp_path):
    total_bytes = _build_tree(tmp_path)
    files, freed = TempFileCleaner()._fast_dir_purge(str(tmp_path), execute=False)
    assert (files, freed) == (3, total_bytes)
    # scan mode deleted nothing
    assert (tmp_path / "a.txt").exists()
    assert (tmp_path / "sub" / "nested" / "c.txt").exists()


def test_fast_dir_purge_missing_dir_returns_zeros(tmp_path):
    assert TempFileCleaner()._fast_dir_purge(
        str(tmp_path / "does-not-exist"), execute=False
    ) == (0, 0)


def test_fast_dir_purge_never_follows_symlinks(tmp_path):
    # a symlink loop inside the tree must be skipped, not recursed into —
    # the H-3 fail-closed guarantee, verified without deleting anything.
    target = tmp_path / "real"
    target.mkdir()
    (target / "f.txt").write_bytes(b"z")
    (target / "loop").symlink_to(target, target_is_directory=True)
    files, _ = TempFileCleaner()._fast_dir_purge(str(target), execute=False)
    assert files == 1  # the loop symlink is skipped, so no infinite recursion


def test_fast_dir_purge_survives_pathological_depth(tmp_path):
    # A tree nested deeper than the interpreter recursion limit must not
    # kill the whole cleanup step: the deep subtree is skipped and the
    # rest of the tree is still counted.
    deep = tmp_path
    for _ in range(1200):
        deep = deep / "d"
        deep.mkdir()
    (tmp_path / "top.txt").write_bytes(b"z")
    files, freed = TempFileCleaner()._fast_dir_purge(str(tmp_path), execute=False)
    assert (files, freed) == (1, 1)
    assert (tmp_path / "top.txt").exists()  # scan mode deleted nothing


def test_clean_temp_directories_dry_run_reports_and_records(monkeypatch, tmp_path):
    _build_tree(tmp_path)
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    cleaner = TempFileCleaner()
    monkeypatch.setattr(cleaner, "paths_to_clean", [str(tmp_path)])
    preview.start()

    result = cleaner.clean_temp_directories()

    assert "(preview)" in result
    assert "Would remove 3 files" in result
    entries = preview.report()
    assert len(entries) == 1
    assert "Would delete 3 temp file(s)" in entries[0]
    assert str(tmp_path) in entries[0]
    # and the tree is untouched
    assert (tmp_path / "a.txt").exists()


def test_clean_temp_directories_dry_run_sums_multiple_paths(monkeypatch, tmp_path):
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir()
    second.mkdir()
    (first / "a.txt").write_bytes(b"x" * 10)
    (second / "b.txt").write_bytes(b"y" * 20)
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    cleaner = TempFileCleaner()
    monkeypatch.setattr(cleaner, "paths_to_clean", [str(first), str(second)])
    preview.start()

    result = cleaner.clean_temp_directories()

    assert "Would remove 2 files" in result
    assert len(preview.report()) == 2  # one preview entry per path
