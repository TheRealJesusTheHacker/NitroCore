"""The VERSION file and the package ``__version__`` must always agree.

Releases, the winget manifest, and the window title all read from one of
these two sources — a mismatch ships the wrong version string somewhere.
"""

import os

import source as source_pkg


def test_version_matches_version_file():
    version_file = os.path.normpath(
        os.path.join(os.path.dirname(source_pkg.__file__), "..", "VERSION")
    )
    with open(version_file, encoding="utf-8") as handle:
        file_version = handle.read().strip()
    assert file_version, "VERSION file is empty"
    assert source_pkg.__version__ == file_version


def test_version_looks_like_semver():
    parts = source_pkg.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
