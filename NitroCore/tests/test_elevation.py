"""Elevation gate + self-check behavior (v1.1.5 field fix).

Field report 2026-10-20: the v1.1.4 executables carried a
requireAdministrator manifest, so any CreateProcess-based launcher
(the Technician's Toolkit launcher, task schedulers, scripts) got
WinError 740 — "The requested operation requires elevation" — and
NitroCore "could not be started", while starting the same .exe from
Explorer (ShellExecute, which can show the prompt) worked fine.

The fix has three parts, all pinned here:

- both PyInstaller specs ship asInvoker, never requireAdministrator;
- the program raises the UAC prompt itself at startup
  (relaunch_elevated / ensure_admin_or_exit in main.py) and exits 1
  with the unchanged Access Denied message if the user declines;
- a headless --self-check mode the release pipeline starts on its
  Windows runner — including as a non-administrator user, in the
  bundle layout — before anything is published.
"""

import os
import sys

import main as nitro_main
import pytest
from source import __version__
from source.utils.config import Config


def _spec_text(name):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", name), encoding="utf-8") as handle:
        return handle.read()


@pytest.mark.parametrize("spec", ["nitrocore.spec", "nitrocore-portable.spec"])
def test_specs_ship_asinvoker_not_require_administrator(spec):
    text = _spec_text(spec)
    assert "uac_admin=True" not in text
    assert "uac_admin=False" in text


def test_quote_cmdline_arg():
    quote = nitro_main._quote_cmdline_arg
    assert quote("plain") == "plain"
    assert quote("--dry-run") == "--dry-run"
    assert quote("two words") == '"two words"'
    assert quote("") == '""'
    assert quote('say "hi"') == '"say \\"hi\\""'
    assert quote("C:\\path with space\\") == '"C:\\path with space\\\\"'


def test_elevation_command_from_source(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "argv", ["main.py", "--dry-run"])
    executable, params = nitro_main.elevation_command()
    assert executable == sys.executable
    script = os.path.abspath(nitro_main.__file__)
    assert params == f"{nitro_main._quote_cmdline_arg(script)} --dry-run"


def test_elevation_command_frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "argv", ["NitroCoreOptimizer.exe", "two words"])
    executable, params = nitro_main.elevation_command()
    assert executable == sys.executable
    assert params == '"two words"'


def test_relaunch_elevated_non_windows(monkeypatch):
    monkeypatch.setattr(nitro_main, "IS_WINDOWS", False)

    def boom(*_args):
        raise AssertionError("ShellExecute must not be called off Windows")

    monkeypatch.setattr(nitro_main, "_shell_execute_runas", boom)
    assert nitro_main.relaunch_elevated() is False


def test_relaunch_elevated_result_codes(monkeypatch):
    monkeypatch.setattr(nitro_main, "IS_WINDOWS", True)
    # > 32: Windows accepted the request (elevated copy takes over).
    monkeypatch.setattr(nitro_main, "_shell_execute_runas", lambda *_a: 33)
    assert nitro_main.relaunch_elevated() is True
    # 5 = SE_ERR_ACCESSDENIED: the user declined the UAC prompt.
    monkeypatch.setattr(nitro_main, "_shell_execute_runas", lambda *_a: 5)
    assert nitro_main.relaunch_elevated() is False

    def explode(*_a):
        raise OSError("no shell")

    monkeypatch.setattr(nitro_main, "_shell_execute_runas", explode)
    assert nitro_main.relaunch_elevated() is False


def test_gate_passes_silently_when_admin(monkeypatch):
    monkeypatch.setattr(nitro_main, "is_admin", lambda: True)
    monkeypatch.setattr(
        nitro_main,
        "relaunch_elevated",
        lambda: (_ for _ in ()).throw(AssertionError("must not relaunch")),
    )
    assert nitro_main.ensure_admin_or_exit() is None


def test_gate_exits_zero_after_successful_relaunch(monkeypatch):
    monkeypatch.setattr(nitro_main, "is_admin", lambda: False)
    monkeypatch.setattr(nitro_main, "relaunch_elevated", lambda: True)
    with pytest.raises(SystemExit) as excinfo:
        nitro_main.ensure_admin_or_exit()
    assert excinfo.value.code == 0


def test_gate_exits_one_with_message_when_elevation_declined(monkeypatch):
    shown = []
    monkeypatch.setattr(nitro_main, "is_admin", lambda: False)
    monkeypatch.setattr(nitro_main, "relaunch_elevated", lambda: False)
    monkeypatch.setattr(
        nitro_main,
        "show_blocking_message",
        lambda t, x, icon=0x10: shown.append((t, x)),
    )
    with pytest.raises(SystemExit) as excinfo:
        nitro_main.ensure_admin_or_exit()
    assert excinfo.value.code == 1
    assert shown and shown[0][0] == "Access Denied"
    assert "Administrative Privileges" in shown[0][1]


def test_self_check_writes_proof_file(monkeypatch, tmp_path, capsys):
    out = tmp_path / "selfcheck.out"
    monkeypatch.setenv("NITROCORE_SELF_CHECK_OUT", str(out))
    assert nitro_main.run_self_check() == 0
    assert out.read_text(encoding="utf-8") == f"NitroCore {__version__} self-check OK\n"
    assert "self-check OK" in capsys.readouterr().out


def test_self_check_without_out_file(monkeypatch):
    monkeypatch.delenv("NITROCORE_SELF_CHECK_OUT", raising=False)
    assert nitro_main.run_self_check() == 0


def test_self_check_bad_out_path_fails(monkeypatch, tmp_path):
    monkeypatch.setenv("NITROCORE_SELF_CHECK_OUT", str(tmp_path / "no-dir" / "x.out"))
    assert nitro_main.run_self_check() == 1


def test_config_self_check_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["NitroCoreOptimizer.exe", "--self-check"])
    Config.parse_arguments()
    assert Config.SELF_CHECK is True
    assert Config.DRY_RUN is False
