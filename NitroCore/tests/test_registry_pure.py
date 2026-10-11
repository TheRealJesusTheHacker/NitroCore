"""Pure-logic tests for source.utils.registry.RegistryOptimizer.

Only the side-effect-free helpers are exercised here: value formatting,
undo-snapshot serialization, and the rule table. ``apply_all`` /
``apply_for_profile`` actually write registry keys and are NEVER called
in tests (see the windows_only suite policy in CONTRIBUTING).
"""

import json
import sys
from unittest import mock

import pytest
from source.modules.registry import RegistryOptimizer


def test_format_value_none():
    assert RegistryOptimizer._format_value(None) == "(not set)"


def test_format_value_bytes_as_hex():
    assert RegistryOptimizer._format_value(b"\xde\xad\xbe\xef") == "0xdeadbeef"
    assert RegistryOptimizer._format_value(b"") == "0x"


def test_format_value_scalars_use_repr():
    assert RegistryOptimizer._format_value(1) == "1"
    assert RegistryOptimizer._format_value("10") == "'10'"


def test_serialize_bytes_uses_hex_encoding():
    assert RegistryOptimizer._serialize_value(b"\xab\xcd") == {
        "encoding": "hex",
        "data": "abcd",
    }


def test_serialize_raw_values_pass_through():
    assert RegistryOptimizer._serialize_value(42) == {
        "encoding": "raw",
        "data": 42,
    }
    assert RegistryOptimizer._serialize_value("10") == {
        "encoding": "raw",
        "data": "10",
    }


@pytest.mark.parametrize("value", [123, "10", b"\x01\x02\xff", None, b""])
def test_serialize_deserialize_roundtrip(value):
    payload = RegistryOptimizer._serialize_value(value)
    assert RegistryOptimizer._deserialize_value(payload) == value


def test_undo_dirname_constant():
    # undo snapshots live under %APPDATA%\NitroCore\<this dir>
    assert RegistryOptimizer.UNDO_DIRNAME == "registry_undo"


def _seed_entry(optimizer, value_name):
    optimizer._undo_entries.append(
        {
            "hive_name": "HKCU",
            "sub_key": r"Software\NitroCoreTest",
            "value_name": value_name,
            "old_value": 1,
            "old_type": 4,
            "existed": True,
        }
    )


def test_write_undo_file_clears_entries_on_success(tmp_path, monkeypatch):
    # Repeated runs must not accumulate stale snapshots: once the undo file
    # is durable, the in-memory list is dropped so a later "undo" restores
    # the previous run only — not values from runs before it.
    optimizer = RegistryOptimizer()
    monkeypatch.setattr(optimizer, "_undo_dir", lambda: str(tmp_path))
    _seed_entry(optimizer, "First")

    first_file = optimizer._write_undo_file()

    assert first_file is not None
    assert optimizer._undo_entries == []

    _seed_entry(optimizer, "Second")
    second_file = optimizer._write_undo_file()
    assert second_file is not None and second_file != first_file
    with open(second_file, encoding="utf-8") as handle:
        payload = json.load(handle)
    assert [e["value_name"] for e in payload["entries"]] == ["Second"]


def test_write_undo_file_keeps_entries_when_write_fails(tmp_path, monkeypatch):
    # If the write fails, the snapshots are all we have — keep them so a
    # later run can still persist them.
    optimizer = RegistryOptimizer()
    monkeypatch.setattr(optimizer, "_undo_dir", lambda: str(tmp_path))
    _seed_entry(optimizer, "First")

    with mock.patch("builtins.open", side_effect=OSError("disk full")):
        assert optimizer._write_undo_file() is None

    assert len(optimizer._undo_entries) == 1


def test_write_undo_file_no_entries_writes_nothing(tmp_path, monkeypatch):
    optimizer = RegistryOptimizer()
    monkeypatch.setattr(optimizer, "_undo_dir", lambda: str(tmp_path))
    assert optimizer._write_undo_file() is None
    assert list(tmp_path.iterdir()) == []


def test_optimization_rules_table():
    optimizer = RegistryOptimizer()
    assert set(optimizer.optimization_rules) == {
        "disable_hibernation",
        "optimize_pagefile",
        "optimize_performance",
    }
    assert optimizer._undo_entries == []


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows guard")
def test_read_registry_value_degrades_gracefully_off_windows():
    # winreg is None off Windows: reads return None instead of raising
    optimizer = RegistryOptimizer()
    assert optimizer._read_registry_value(None, "some\\key", "value") is None
    assert optimizer._read_registry_value_full(None, "some\\key", "value") == (
        None,
        None,
    )
