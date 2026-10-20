"""Bug hunt #2 (2026-10-19) regression tests.

1. Registry key-handle leaks: ``CloseKey`` sat after the write in both
   ``RegistryOptimizer._set_registry_value`` and ``restore_last_undo``,
   so a failing ``SetValueEx`` (or a malformed undo payload failing in
   ``_deserialize_value``) leaked the opened key handle — the W-4/W-5
   leak pattern that services.py already had fixed, missed in
   registry.py. Handles must now close on success AND on failure.

2. ``DiskCleanup.clean_downloads`` crashed on a top-level scandir
   failure that wasn't PermissionError: ``_purge_old_files`` caught only
   PermissionError around its outermost ``os.scandir``, so a Downloads
   path that is a plain file (NotADirectoryError) propagated out
   instead of reporting a zero-clean result.
"""

import os

import pytest
import source.modules.registry as registry_module
from source.modules.disk_cleanup import DiskCleanup
from source.modules.registry import RegistryOptimizer

_HKCU = 0x80000001


class _RecordingWinreg:
    """Fake winreg recording CloseKey calls; writes can be made to fail."""

    HKEY_CURRENT_USER = _HKCU
    HKEY_LOCAL_MACHINE = 0x80000002
    HKEY_CLASSES_ROOT = 0x80000000
    HKEY_USERS = 0x80000003
    HKEY_CURRENT_CONFIG = 0x80000005
    KEY_READ = 0x20019
    KEY_SET_VALUE = 0x0002
    REG_DWORD = 4

    def __init__(self, fail_set=False):
        self.fail_set = fail_set
        self.closed = []
        self.created = []

    def OpenKey(self, hive, sub_key, reserved, access):
        raise OSError("no such value in fake registry")

    def CreateKeyEx(self, hive, sub_key, reserved, access):
        key = f"key:{sub_key}"
        self.created.append(key)
        return key

    def SetValueEx(self, key, name, reserved, value_type, value):
        if self.fail_set:
            raise OSError("simulated SetValueEx failure")

    def DeleteValue(self, key, name):
        pass

    def CloseKey(self, key):
        self.closed.append(key)


@pytest.fixture()
def recording_winreg(monkeypatch):
    def _install(fail_set=False):
        fake = _RecordingWinreg(fail_set=fail_set)
        monkeypatch.setattr(registry_module, "winreg", fake)
        monkeypatch.setattr(registry_module, "_HIVE_NAMES", {_HKCU: "HKCU"})
        return fake

    return _install


def test_set_registry_value_closes_key_on_write_failure(recording_winreg):
    fake = recording_winreg(fail_set=True)
    optimizer = RegistryOptimizer()
    assert optimizer._set_registry_value(_HKCU, r"Software\X", "V", 1) is False
    assert fake.closed == fake.created and len(fake.created) == 1


def test_set_registry_value_closes_key_on_success(recording_winreg):
    fake = recording_winreg()
    optimizer = RegistryOptimizer()
    assert optimizer._set_registry_value(_HKCU, r"Software\X", "V", 1) is True
    assert fake.closed == fake.created and len(fake.created) == 1


def test_restore_last_undo_closes_key_on_write_failure(
    recording_winreg, tmp_path, monkeypatch
):
    fake = recording_winreg(fail_set=True)
    (tmp_path / "undo-20990101-000000-000000.json").write_text(
        '{"entries": [{"hive": "HKCU", "sub_key": "Software\\\\X", '
        '"value_name": "V", "existed": true, "old_type": 4, '
        '"old_value": {"encoding": "raw", "data": 7}}]}',
        encoding="utf-8",
    )
    optimizer = RegistryOptimizer()
    monkeypatch.setattr(optimizer, "_undo_dir", lambda: str(tmp_path))
    result = optimizer.restore_last_undo()
    assert "restored 0 value(s)" in result
    assert "1 failed" in result
    assert fake.closed == fake.created and len(fake.created) == 1


def test_clean_downloads_survives_downloads_path_being_a_file(monkeypatch, tmp_path):
    # A plain file where the Downloads folder should be: exists() passes,
    # then scandir raises NotADirectoryError (an OSError, not a
    # PermissionError). clean_downloads must report, not crash.
    not_a_dir = tmp_path / "Downloads"
    not_a_dir.write_bytes(b"i am a file, not the downloads folder")
    monkeypatch.setattr(os.path, "expandvars", lambda s: str(not_a_dir))
    result = DiskCleanup().clean_downloads()
    assert result.startswith("Downloads Clean: Moved 0 files")
