"""Restore-path tests for RegistryOptimizer.restore_last_undo (BH2-3).

The undo file is user-writable JSON under %APPDATA%. Before this round, a
file that parsed as valid JSON but had the wrong shape — a list instead
of an object, ``entries`` that wasn't a list, non-object entries — raised
AttributeError/TypeError out of restore_last_undo instead of returning
the friendly "Could not read undo file" result. These tests pin the
graceful behavior with a fake winreg, plus the happy path and the S-1
HKCU-only refusal.
"""

import pytest
import source.modules.registry as registry_module
from source.modules.registry import RegistryOptimizer

_HKCU = 0x80000001
_HKLM = 0x80000002


class _FakeWinreg:
    """Minimal winreg stand-in recording every write."""

    HKEY_CURRENT_USER = _HKCU
    HKEY_LOCAL_MACHINE = _HKLM
    HKEY_CLASSES_ROOT = 0x80000000
    HKEY_USERS = 0x80000003
    HKEY_CURRENT_CONFIG = 0x80000005
    KEY_SET_VALUE = 0x0002

    def __init__(self):
        self.created = []
        self.set_calls = []
        self.deleted = []

    def CreateKeyEx(self, hive, sub_key, reserved, access):
        self.created.append((hive, sub_key))
        return f"key:{sub_key}"

    def SetValueEx(self, key, name, reserved, value_type, value):
        self.set_calls.append((key, name, value_type, value))

    def DeleteValue(self, key, name):
        self.deleted.append((key, name))

    def CloseKey(self, key):
        pass


@pytest.fixture()
def fake_winreg(monkeypatch):
    fake = _FakeWinreg()
    monkeypatch.setattr(registry_module, "winreg", fake)
    monkeypatch.setattr(
        registry_module,
        "_HIVE_NAMES",
        {
            _HKCU: "HKCU",
            _HKLM: "HKLM",
            fake.HKEY_CLASSES_ROOT: "HKCR",
            fake.HKEY_USERS: "HKU",
            fake.HKEY_CURRENT_CONFIG: "HKCC",
        },
    )
    return fake


def _optimizer_with_undo(tmp_path, monkeypatch, payload_text):
    (tmp_path / "undo-20990101-000000-000000.json").write_text(
        payload_text, encoding="utf-8"
    )
    optimizer = RegistryOptimizer()
    monkeypatch.setattr(optimizer, "_undo_dir", lambda: str(tmp_path))
    return optimizer


@pytest.mark.parametrize(
    "payload_text",
    [
        "[]",
        "null",
        '"just a string"',
        "42",
        '{"entries": 42}',
        '{"entries": null}',
        '{"entries": {"a": 1}}',
        '{"no_entries_here": true}',
        "{not json",
    ],
)
def test_restore_survives_malformed_undo_files(
    tmp_path, monkeypatch, fake_winreg, payload_text
):
    optimizer = _optimizer_with_undo(tmp_path, monkeypatch, payload_text)
    result = optimizer.restore_last_undo()
    assert result.startswith("Could not read undo file")
    assert fake_winreg.created == []


def test_restore_counts_non_object_entries_as_failed(
    tmp_path, monkeypatch, fake_winreg
):
    optimizer = _optimizer_with_undo(
        tmp_path, monkeypatch, '{"entries": ["junk", 7, null]}'
    )
    result = optimizer.restore_last_undo()
    assert "restored 0 value(s)" in result
    assert "3 failed" in result
    assert fake_winreg.created == []


def _entry(**overrides):
    entry = {
        "hive": "HKCU",
        "sub_key": r"Software\NitroCoreTest",
        "value_name": "MenuShowDelay",
        "existed": True,
        "old_type": 1,
        "old_value": {"encoding": "raw", "data": "400"},
    }
    entry.update(overrides)
    return entry


def test_restore_valid_entry_writes_old_value(tmp_path, monkeypatch, fake_winreg):
    import json

    optimizer = _optimizer_with_undo(
        tmp_path, monkeypatch, json.dumps({"entries": [_entry()]})
    )
    result = optimizer.restore_last_undo()
    assert "restored 1 value(s)" in result
    assert fake_winreg.set_calls == [
        (r"key:Software\NitroCoreTest", "MenuShowDelay", 1, "400")
    ]


def test_restore_entry_that_did_not_exist_deletes_value(
    tmp_path, monkeypatch, fake_winreg
):
    import json

    optimizer = _optimizer_with_undo(
        tmp_path,
        monkeypatch,
        json.dumps({"entries": [_entry(existed=False)]}),
    )
    result = optimizer.restore_last_undo()
    assert "restored 1 value(s)" in result
    assert fake_winreg.deleted == [(r"key:Software\NitroCoreTest", "MenuShowDelay")]
    assert fake_winreg.set_calls == []


def test_restore_refuses_non_hkcu_entries(tmp_path, monkeypatch, fake_winreg):
    # S-1: a planted undo file must never write outside HKCU.
    import json

    optimizer = _optimizer_with_undo(
        tmp_path,
        monkeypatch,
        json.dumps({"entries": [_entry(hive="HKLM")]}),
    )
    result = optimizer.restore_last_undo()
    assert "restored 0 value(s)" in result
    assert "1 failed" in result
    assert fake_winreg.created == []


def test_restore_entry_missing_fields_fails_not_raises(
    tmp_path, monkeypatch, fake_winreg
):
    import json

    optimizer = _optimizer_with_undo(
        tmp_path,
        monkeypatch,
        json.dumps({"entries": [{"hive": "HKCU"}]}),
    )
    result = optimizer.restore_last_undo()
    assert "restored 0 value(s)" in result
    assert "1 failed" in result
