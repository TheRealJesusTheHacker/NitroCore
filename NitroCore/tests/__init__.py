"""Pytest bootstrap for the NitroCore test suite.

Production code imports as top-level ``source`` packages
(e.g. ``from source.utils.config import Config``) because ``main.py`` puts
the ``NitroCore/`` directory on ``sys.path``. Mirror that here so the tests
import the real modules the same way, with no install step required.
"""

import os
import sys

NITROCORE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if NITROCORE_ROOT not in sys.path:
    sys.path.insert(0, NITROCORE_ROOT)
