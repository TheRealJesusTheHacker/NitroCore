"""Tests for source.utils.platform — the single place where Windows-only
assumptions are centralized so the app degrades gracefully elsewhere."""

import subprocess
import sys

import pytest
from source.utils import platform as platform_mod


def test_is_windows_matches_runtime():
    assert platform_mod.IS_WINDOWS == (sys.platform == "win32")


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows behavior")
def test_hidden_subprocess_kwargs_empty_off_windows():
    # subprocess.STARTUPINFO does not exist off Windows; callers spread
    # these kwargs into subprocess.run, so this must be a plain dict.
    kwargs = platform_mod.hidden_subprocess_kwargs()
    assert kwargs == {}
    assert isinstance(kwargs, dict)


@pytest.mark.windows_only
def test_hidden_subprocess_kwargs_hides_console_on_windows():
    kwargs = platform_mod.hidden_subprocess_kwargs()
    assert isinstance(kwargs["startupinfo"], subprocess.STARTUPINFO)
    assert kwargs["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW
    assert "creationflags" in kwargs
