"""Pure-logic tests for source.utils.registry.RegistryOptimizer.

Only the side-effect-free helpers are exercised here: value formatting,
undo-snapshot serialization, and the rule table. ``apply_all`` /
``apply_for_profile`` actually write registry keys and are NEVER called
in tests (see the windows_only suite policy in CONTRIBUTING).
"""

import sys

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
