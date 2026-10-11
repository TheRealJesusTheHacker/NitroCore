"""Tests for source.utils.helpers.is_reparse_point.

This is the safety gate behind the H-3 hardening: cleanup code must NEVER
recurse into symlinks or NTFS junctions, because a junction inside a temp
tree can point outside it and deletion would escape the intended tree.

The function is fail-closed — anything it cannot classify is treated as a
reparse point (skipped). These tests pin that contract with fake DirEntry
objects; no filesystem fixtures with real symlinks are needed.
"""

from source.utils.helpers import is_reparse_point

FILE_ATTRIBUTE_REPARSE_POINT = 0x400


class FakeStat:
    def __init__(self, file_attributes=0):
        self.st_file_attributes = file_attributes


class FakeEntry:
    """Minimal os.DirEntry stand-in with injectable failures."""

    def __init__(
        self,
        *,
        junction=False,
        junction_raises=None,
        file_attributes=0,
        stat_raises=None,
        symlink=False,
        symlink_raises=None,
        has_junction_method=True,
    ):
        self._junction = junction
        self._junction_raises = junction_raises
        self._file_attributes = file_attributes
        self._stat_raises = stat_raises
        self._symlink = symlink
        self._symlink_raises = symlink_raises
        if not has_junction_method and hasattr(self, "is_junction"):
            del self.is_junction

    def is_junction(self):
        if self._junction_raises is not None:
            raise self._junction_raises
        return self._junction

    def stat(self, follow_symlinks=True):
        if self._stat_raises is not None:
            raise self._stat_raises
        return FakeStat(self._file_attributes)

    def is_symlink(self):
        if self._symlink_raises is not None:
            raise self._symlink_raises
        return self._symlink


class NoJunctionMethodEntry(FakeEntry):
    """Entry from a Python without DirEntry.is_junction (pre-3.12)."""

    def __getattribute__(self, name):
        if name == "is_junction":
            raise AttributeError(name)
        return super().__getattribute__(name)


def test_plain_file_is_not_a_reparse_point():
    assert is_reparse_point(FakeEntry()) is False


def test_ntfs_junction_is_detected():
    assert is_reparse_point(FakeEntry(junction=True)) is True


def test_reparse_point_file_attribute_is_detected():
    entry = FakeEntry(file_attributes=FILE_ATTRIBUTE_REPARSE_POINT)
    assert is_reparse_point(entry) is True


def test_plain_symlink_is_detected():
    assert is_reparse_point(FakeEntry(symlink=True)) is True


def test_old_python_without_is_junction_still_classifies():
    # falls through to the stat-attribute and is_symlink checks
    assert is_reparse_point(NoJunctionMethodEntry()) is False
    assert (
        is_reparse_point(
            NoJunctionMethodEntry(file_attributes=FILE_ATTRIBUTE_REPARSE_POINT)
        )
        is True
    )
    assert is_reparse_point(NoJunctionMethodEntry(symlink=True)) is True


def test_fail_closed_when_junction_check_raises():
    assert is_reparse_point(FakeEntry(junction_raises=OSError())) is True


def test_fail_closed_when_stat_raises():
    assert is_reparse_point(FakeEntry(stat_raises=OSError())) is True


def test_fail_closed_when_is_symlink_raises():
    assert is_reparse_point(FakeEntry(symlink_raises=OSError())) is True


def test_combined_attributes_still_detected():
    entry = FakeEntry(
        junction=True,
        file_attributes=FILE_ATTRIBUTE_REPARSE_POINT,
        symlink=True,
    )
    assert is_reparse_point(entry) is True
