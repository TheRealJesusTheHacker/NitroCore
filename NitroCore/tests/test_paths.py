"""Tests for resource path resolution (source.utils.paths)."""

import os
import sys

from source.utils.paths import resource_path


def test_resource_path_dev_mode_is_absolute():
    result = resource_path(os.path.join("assets", "icon.ico"))
    assert os.path.isabs(result)
    assert result.endswith(os.path.join("assets", "icon.ico"))


def test_resource_path_dev_mode_anchors_at_package_root():
    # in dev mode the base is the NitroCore/ directory (parent of source/)
    result = resource_path("x")
    assert os.path.dirname(result).endswith("NitroCore")


def test_resource_path_frozen_uses_meipass(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert resource_path("x.bin") == os.path.join(str(tmp_path), "x.bin")
