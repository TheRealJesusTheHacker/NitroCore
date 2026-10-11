"""Tests for the dry-run preview recorder (source.utils.preview).

The recorder is the backbone of Preview Mode: mutating modules describe
what they *would* do instead of doing it. These tests cover the recorder
contract only — no system changes of any kind.
"""

from source.utils import preview as preview_module
from source.utils.preview import PREVIEW_FOOTER, preview


def test_record_before_start_is_dropped():
    preview.record("nothing is recording yet")
    assert preview.report() == []


def test_start_record_report_preserves_order():
    preview.start()
    preview.record("first change")
    preview.record("second change")
    assert preview.report() == ["first change", "second change"]


def test_start_discards_previous_entries():
    preview.start()
    preview.record("stale entry")
    preview.start()
    assert preview.report() == []


def test_report_returns_a_copy():
    preview.start()
    preview.record("one")
    report = preview.report()
    report.append("caller-side mutation")
    report.clear()
    assert preview.report() == ["one"]


def test_reset_stops_recording_and_clears():
    preview.start()
    preview.record("one")
    preview.reset()
    preview.record("recorded after reset — must be dropped")
    assert preview.report() == []


def test_empty_report_when_nothing_recorded():
    preview.start()
    assert preview.report() == []


def test_preview_footer_constant():
    assert "PREVIEW ONLY" in PREVIEW_FOOTER
    assert "no changes were made" in PREVIEW_FOOTER


def test_preview_is_a_process_wide_singleton():
    # modules do `from source.utils.preview import preview` — they must all
    # share this exact recorder instance for reports to be complete.
    assert preview_module.preview is preview
