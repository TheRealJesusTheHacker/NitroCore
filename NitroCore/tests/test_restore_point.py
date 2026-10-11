"""Tests for create_restore_point — dry-run and platform-guard branches only.

The real branch shells out to PowerShell's ``Checkpoint-Computer`` and
creates an actual system restore point, so it is NEVER called in tests.
"""

import sys

import pytest
from source.utils.config import Config
from source.utils.restore_point import create_restore_point


def test_dry_run_never_touches_the_system(monkeypatch):
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    ok, message = create_restore_point("NitroCore - test")
    assert ok is False
    assert "Preview mode" in message
    assert "nothing will change" in message


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows guard")
def test_non_windows_reports_unavailable(monkeypatch):
    monkeypatch.setattr(Config, "DRY_RUN", False, raising=False)
    ok, message = create_restore_point("NitroCore - test")
    assert ok is False
    assert "only available on Windows" in message


def test_dry_run_takes_precedence_over_platform_guard(monkeypatch):
    # even on Windows, a dry run must not attempt restore-point creation
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    ok, message = create_restore_point("NitroCore - test")
    assert ok is False
    assert "Preview mode" in message


def test_default_description():
    # documents the default restore-point label used by the GUI
    import inspect

    sig = inspect.signature(create_restore_point)
    assert sig.parameters["description"].default == "NitroCore Pre-Optimization"
