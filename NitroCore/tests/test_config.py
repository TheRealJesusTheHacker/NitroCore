"""Tests for CLI argument parsing (source.utils.config.Config).

``parse_arguments`` uses ``parse_known_args`` and only flips class flags —
safe to exercise on any platform. The autouse fixture in conftest.py
restores ``Config`` state after each test.
"""

import sys

from source.utils.config import Config
from source.utils.profiles import GAMING


def test_defaults_without_flags(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py"])
    Config.parse_arguments()
    assert Config.PI_BOY_MODE is False
    assert Config.DRY_RUN is False
    assert Config.CLICK_COUNTER == 0
    assert Config.ACTIVE_PROFILE == GAMING


def test_dry_run_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "--dry-run"])
    Config.parse_arguments()
    assert Config.DRY_RUN is True


def test_fallout_flag_enables_pip_boy_mode(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "--fallout"])
    Config.parse_arguments()
    assert Config.PI_BOY_MODE is True


def test_flags_combine(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "--dry-run", "--fallout"])
    Config.parse_arguments()
    assert Config.DRY_RUN is True
    assert Config.PI_BOY_MODE is True


def test_unknown_args_are_ignored_not_fatal(monkeypatch):
    # parse_known_args: stray flags must never crash startup
    monkeypatch.setattr(sys, "argv", ["main.py", "--no-such-flag", "positional"])
    Config.parse_arguments()
    assert Config.DRY_RUN is False
    assert Config.PI_BOY_MODE is False
