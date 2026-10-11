"""Guard-path and dry-run tests for PerformanceTuner.

The dry-run branch only records preview entries — ``powercfg`` is never
executed and no process priorities change — so it is safe on every
platform by forcing ``IS_WINDOWS`` on the module under test.
"""

import sys

import pytest
import source.modules.performance as perf_module
from source.modules.performance import PerformanceTuner
from source.utils.config import Config
from source.utils.preview import preview


def test_power_plan_guids():
    tuner = PerformanceTuner()
    assert tuner.ultimate_perf_guid == "e9a42b02-d5df-448d-aa00-03f14749eb61"
    assert tuner.high_perf_guid == "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows guard")
def test_guards_off_windows():
    tuner = PerformanceTuner()
    assert tuner.optimize_power_plan().startswith("Skipped:")
    assert tuner.set_process_priority().startswith("Skipped:")


def test_dry_run_power_plan_records_preview_without_powercfg(monkeypatch):
    monkeypatch.setattr(perf_module, "IS_WINDOWS", True)
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    monkeypatch.setattr(
        PerformanceTuner, "_current_power_scheme", lambda self: "'Balanced' "
    )
    preview.start()

    result = PerformanceTuner().optimize_power_plan()

    assert "(preview)" in result
    entries = preview.report()
    assert any("Ultimate Performance" in entry for entry in entries)
    assert any("Balanced" in entry for entry in entries)


def test_dry_run_process_priority_records_preview(monkeypatch):
    # psutil.process_iter is read-only; dry run must not call proc.nice()
    monkeypatch.setattr(perf_module, "IS_WINDOWS", True)
    monkeypatch.setattr(Config, "DRY_RUN", True, raising=False)
    preview.start()

    result = PerformanceTuner().set_process_priority()

    assert "(preview)" in result
    assert any("Above Normal" in entry for entry in preview.report())
