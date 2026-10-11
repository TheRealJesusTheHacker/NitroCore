"""Shared fixtures for the NitroCore test suite.

``Config`` stores runtime state as class attributes and ``preview`` is a
process-wide singleton recorder — both leak between tests if left alone.
This autouse fixture snapshots and restores them around every test so each
test starts from a clean slate.
"""

import sys

import pytest


def pytest_collection_modifyitems(items):
    """Tests marked ``windows_only`` only run on a Windows runner.

    They exercise real registry / service / powercfg code paths, so on any
    other platform they are skipped instead of failed.
    """
    if sys.platform == "win32":
        return
    skip_windows = pytest.mark.skip(reason="requires Windows")
    for item in items:
        if "windows_only" in item.keywords:
            item.add_marker(skip_windows)


@pytest.fixture(autouse=True)
def _isolate_global_state():
    from source.utils.config import Config
    from source.utils.preview import preview

    saved = {
        name: getattr(Config, name)
        for name in ("PI_BOY_MODE", "CLICK_COUNTER", "ACTIVE_PROFILE", "DRY_RUN")
    }
    preview.reset()
    yield
    for name, value in saved.items():
        setattr(Config, name, value)
    preview.reset()
