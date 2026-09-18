import os
import subprocess
import psutil
from datetime import datetime, timedelta

from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs


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
        except subprocess.TimeoutExpired:
            return "Windows Native Cleanup timed out (System spent too long compressing old updates)"
        except FileNotFoundError:
            pass
        except Exception as e:
            return f"Error executing System File Cleanup: {str(e)}"

        try:
            proc = subprocess.run(
                ["dism", "/Online", "/Cleanup-Image", "/StartComponentCleanup"],
                timeout=600,
                **run_kwargs,
            )
            if proc.returncode == 0:
                return "DISM component cleanup completed successfully"
            stderr = proc.stderr.decode(errors="ignore").strip()
            return f"System cleanup failed: {stderr or 'Unknown error'}"
        except subprocess.TimeoutExpired:
            return "DISM cleanup timed out"
        except Exception as e:
            return f"Error executing System File Cleanup: {str(e)}"

    def clean_downloads(self, retention_days=30):
        """
        Scan and clean files in the user downloads folder older than specified retention days.
        """
        downloads_path = os.path.realpath(os.path.expandvars("%USERPROFILE%\\Downloads"))

        if not os.path.exists(downloads_path):
            return "Downloads folder not found"

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        files_removed = 0
        bytes_saved = 0

        def _purge_old_files(target_path):
            nonlocal files_removed, bytes_saved
            try:
                with os.scandir(target_path) as entries:
                    for entry in entries:
                        try:
                            if entry.is_file(follow_symlinks=False):
                                file_mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                                if file_mtime < cutoff_date:
                                    file_size = entry.stat().st_size
                                    os.remove(entry.path)
                                    files_removed += 1
                                    bytes_saved += file_size
                            elif entry.is_dir(follow_symlinks=False):
                                _purge_old_files(entry.path)
                                try:
                                    if not os.listdir(entry.path):
                                        os.rmdir(entry.path)
                                except OSError:
                                    pass
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
            except PermissionError:
                pass

        _purge_old_files(downloads_path)
        mb_saved = bytes_saved / (1024 * 1024)
        return (
            f"Downloads Clean: Removed {files_removed} files older than "
            f"{retention_days} days ({mb_saved:.2f} MB freed)"
        )
