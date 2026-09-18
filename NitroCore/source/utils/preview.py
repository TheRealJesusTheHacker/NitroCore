"""Dry-run preview recorder for NitroCore.

When Config.DRY_RUN is enabled, mutating modules do not execute changes.
Instead they record a human-readable description of what *would* have been
done via the shared ``preview`` recorder below. The caller (GUI or CLI)
starts a recording before a run and renders ``preview.report()`` afterwards.

Recordings are ordered by execution. Runs are serialized by the UI's busy
flag, so a single process-wide recorder is sufficient.
"""

from typing import List


class _PreviewRecorder:
    def __init__(self) -> None:
        self._entries: List[str] = []
        self._active = False

    def start(self) -> None:
        """Begin a new recording, discarding any previous entries."""
        self._entries = []
        self._active = True

    def record(self, description: str) -> None:
        """Append one human-readable 'would do' description, if recording."""
        if self._active:
            self._entries.append(description)

    def report(self) -> List[str]:
        """Return the ordered preview entries collected so far."""
        return list(self._entries)

    def reset(self) -> None:
        """Discard entries and stop recording."""
        self._entries = []
        self._active = False


preview = _PreviewRecorder()

#: Footer line appended to every rendered preview report.
PREVIEW_FOOTER = "PREVIEW ONLY \u2014 no changes were made."
