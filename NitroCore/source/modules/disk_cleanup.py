import os
import subprocess
import psutil
from datetime import datetime, timedelta

from source.utils.config import Config
from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs
from source.utils.preview import preview
from source.utils.helpers import is_reparse_point


def _recycle_path_windows(path: str) -> bool:
    """
    Move a file or folder to the Recycle Bin via SHFileOperationW
    (FO_DELETE + FOF_ALLOWUNDO). Returns True only if the shell confirms
    the move. Fail-closed: any error means "not recycled".
    """
    if not IS_WINDOWS:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("wFunc", wintypes.UINT),
                ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR),
                ("fFlags", wintypes.UINT),
                ("fAnyOperationsAborted", wintypes.BOOL),
                ("hNameMappings", wintypes.LPVOID),
                ("lpszProgressTitle", wintypes.LPCWSTR),
            ]

        FO_DELETE = 3
        FOF_ALLOWUNDO = 0x40
        FOF_NOCONFIRMATION = 0x10
        FOF_SILENT = 0x04
        FOF_NOERRORUI = 0x400

        # pFrom must be double-null-terminated; create_unicode_buffer adds
        # the final null on top of the explicit one.
        from_buf = ctypes.create_unicode_buffer(path + "\0")
        op = SHFILEOPSTRUCTW()
        op.hwnd = None
        op.wFunc = FO_DELETE
        op.pFrom = ctypes.cast(from_buf, wintypes.LPCWSTR)
        op.pTo = None
        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI

        rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        return rc == 0 and not op.fAnyOperationsAborted
    except Exception:
        return False


class DiskCleanup:
    def __init__(self):
        self.min_disk_space_gb = 10.0

    def get_disk_usage(self):
        """
        Get current disk usage statistics for local fixed drives only.
        """
        usage = {}
        for partition in psutil.disk_partitions(all=False):
            if "fixed" not in partition.opts.lower():
                continue
            try:
                usage_stats = psutil.disk_usage(partition.mountpoint)
                usage[partition.device] = {
                    "total_gb": round(usage_stats.total / (1024 ** 3), 2),
                    "used_gb": round(usage_stats.used / (1024 ** 3), 2),
                    "free_gb": round(usage_stats.free / (1024 ** 3), 2),
                    "percent": usage_stats.percent,
                }
            except (PermissionError, FileNotFoundError, OSError):
                continue
        return usage

    def clean_system_files(self):
        """
        Run Windows Disk Cleanup silently for the system drive, with DISM fallback.
        """
        if not IS_WINDOWS:
            return "Skipped: system file cleanup is Windows-only"
        if Config.DRY_RUN:
            # The exact savings of cleanmgr/DISM cannot be known without running
            # them, so the preview describes the commands that would execute.
            preview.record(
                "Would run: cleanmgr /verylowdisk "
                "(Windows Disk Cleanup: update leftovers, temporary setup files)"
            )
            preview.record(
                "Would run if needed: DISM /Online /Cleanup-Image /StartComponentCleanup "
                "(component store cleanup)"
            )
            return "Windows Disk Cleanup: would run (preview) — exact savings unknown until executed"
        run_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            **hidden_subprocess_kwargs(),
        }
        try:
            proc = subprocess.run(
                ["cleanmgr", "/verylowdisk"],
                timeout=300,
                **run_kwargs,
            )
            if proc.returncode == 0:
                return "Windows Native Cleanup executed successfully"
            # L-7: record WHY cleanmgr failed before falling through to DISM.
            cleanmgr_note = (
                f"cleanmgr exited with code {proc.returncode}: "
                f"{proc.stderr.decode(errors='ignore').strip() or 'no error output'}"
            )
        except subprocess.TimeoutExpired:
            return "Windows Native Cleanup timed out (System spent too long compressing old updates)"
        except FileNotFoundError:
            cleanmgr_note = "cleanmgr not found on this system"
        except Exception as e:
            return f"Error executing System File Cleanup: {str(e)}"

        try:
            proc = subprocess.run(
                ["dism", "/Online", "/Cleanup-Image", "/StartComponentCleanup"],
                timeout=600,
                **run_kwargs,
            )
            if proc.returncode == 0:
                return f"DISM component cleanup completed successfully ({cleanmgr_note})"
            stderr = proc.stderr.decode(errors="ignore").strip()
            return f"System cleanup failed: {stderr or 'Unknown error'} ({cleanmgr_note})"
        except subprocess.TimeoutExpired:
            return f"DISM cleanup timed out ({cleanmgr_note})"
        except Exception as e:
            return f"Error executing System File Cleanup: {str(e)} ({cleanmgr_note})"

    def clean_downloads(self, retention_days=30):
        """
        Scan and clean files in the user downloads folder older than specified retention days.

        H-2 hardening: files are moved to the Recycle Bin (recoverable) instead
        of permanently deleted. Files that cannot be recycled are left in place
        and reported — never silently destroyed. Callers must still confirm with
        the user before invoking this (see tabs._run_disk_downloads).
        """
        downloads_path = os.path.realpath(os.path.expandvars("%USERPROFILE%\\Downloads"))

        if not os.path.exists(downloads_path):
            return "Downloads folder not found"

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        files_removed = 0
        files_skipped = 0
        bytes_saved = 0
        dry_run = Config.DRY_RUN

        def _purge_old_files(target_path, execute=True):
            nonlocal files_removed, files_skipped, bytes_saved
            try:
                with os.scandir(target_path) as entries:
                    for entry in entries:
                        try:
                            if entry.is_file(follow_symlinks=False):
                                file_mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                                if file_mtime < cutoff_date:
                                    file_size = entry.stat().st_size
                                    if execute:
                                        # Recycle, don't destroy. Fail closed:
                                        # if the shell won't take it, leave it.
                                        if _recycle_path_windows(entry.path):
                                            files_removed += 1
                                            bytes_saved += file_size
                                        else:
                                            files_skipped += 1
                                    else:
                                        files_removed += 1
                                        bytes_saved += file_size
                            elif is_reparse_point(entry):
                                # H-3: never recurse into junctions/symlinks —
                                # they can point outside the Downloads tree.
                                continue
                            elif entry.is_dir(follow_symlinks=False):
                                _purge_old_files(entry.path, execute=execute)
                                if execute:
                                    try:
                                        if not os.listdir(entry.path):
                                            os.rmdir(entry.path)
                                    except OSError:
                                        pass
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
            except PermissionError:
                pass

        _purge_old_files(downloads_path, execute=not dry_run)
        mb_saved = bytes_saved / (1024 * 1024)
        skipped_note = (
            f" ({files_skipped} file(s) could not be moved to the Recycle Bin "
            f"and were left untouched)"
            if files_skipped else ""
        )
        if dry_run:
            preview.record(
                f"Would move {files_removed} file(s) older than {retention_days} days "
                f"({mb_saved:.2f} MB) from {downloads_path} to the Recycle Bin"
            )
            return (
                f"Downloads Clean: Would move {files_removed} files older than "
                f"{retention_days} days ({mb_saved:.2f} MB would be freed) to the "
                f"Recycle Bin (preview)"
            )
        return (
            f"Downloads Clean: Moved {files_removed} files older than "
            f"{retention_days} days ({mb_saved:.2f} MB freed) to the Recycle Bin"
            f"{skipped_note}"
        )
