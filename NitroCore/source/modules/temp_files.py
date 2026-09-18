import os
import shutil
import glob

from source.utils.config import Config
from source.utils.preview import preview

class TempFileCleaner:
    def __init__(self):
        # De-duplicating folders (%TEMP% and %LOCALAPPDATA%\Temp are usually identical)
        self.paths_to_clean = list(set([
            os.path.realpath(os.path.expandvars('%TEMP%')),
            os.path.realpath(os.path.expandvars('%SYSTEMROOT%\\Temp'))
        ]))
        
    def _fast_dir_purge(self, target_dir, execute=True):
        """
        High-performance, non-recursive file and directory purger using os.scandir.
        When execute=False, only scans (read-only) and counts what would be removed.
        Returns a tuple: (deleted_file_count, bytes_saved)
        """
        files_deleted = 0
        bytes_saved = 0
        
        if not os.path.exists(target_dir):
            return files_deleted, bytes_saved

        try:
            # os.scandir() is heavily optimized at the OS file-system level on Windows
            with os.scandir(target_dir) as entries:
                for entry in entries:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            file_size = entry.stat().st_size
                            if execute:
                                os.remove(entry.path)
                            files_deleted += 1
                            bytes_saved += file_size
                        elif entry.is_dir(follow_symlinks=False):
                            # Recursively purge subdirectories
                            sub_files, sub_bytes = self._fast_dir_purge(entry.path, execute=execute)
                            files_deleted += sub_files
                            bytes_saved += sub_bytes
                            
                            if execute:
                                # Attempt to clean up the directory shell if it's now empty
                                os.rmdir(entry.path)
                    except (PermissionError, FileNotFoundError):
                        # Skip locked files (in-use logs/system locks) without overhead
                        continue
        except PermissionError:
            pass
            
        return files_deleted, bytes_saved

    def clean_temp_directories(self):
        """Clean all temporary directories cleanly and return a metric string"""
        total_files = 0
        total_bytes = 0
        dry_run = Config.DRY_RUN

        for path in self.paths_to_clean:
            files, bytes_freed = self._fast_dir_purge(path, execute=not dry_run)
            if dry_run:
                mb = bytes_freed / (1024 * 1024)
                preview.record(
                    f"Would delete {files} temp file(s) ({mb:.2f} MB) from {path}"
                )
            total_files += files
            total_bytes += bytes_freed

        mb_saved = total_bytes / (1024 * 1024)
        if dry_run:
            return (
                f"System Temp: Would remove {total_files} files "
                f"({mb_saved:.2f} MB would be freed) (preview)"
            )
        return f"System Temp: Removed {total_files} files ({mb_saved:.2f} MB freed)"
    
    def clean_browser_cache(self):
        """Clean browser cache files accurately resolving profile wildcards"""
        browser_paths = [
            ('%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache\\Cache_Data', 'Chrome'),
            ('%APPDATA%\\Mozilla\\Firefox\\Profiles\\*\\cache2', 'Firefox')
        ]
        
        total_files = 0
        total_bytes = 0
        dry_run = Config.DRY_RUN

        for path_template, browser_name in browser_paths:
            expanded_template = os.path.expandvars(path_template)
            
            # Use glob to properly resolve wildcards like '*' in Firefox profiles
            target_paths = glob.glob(expanded_template)
            
            for path in target_paths:
                files, bytes_freed = self._fast_dir_purge(path, execute=not dry_run)
                if dry_run:
                    mb = bytes_freed / (1024 * 1024)
                    preview.record(
                        f"Would delete {files} cached file(s) ({mb:.2f} MB) "
                        f"from {browser_name} cache at {path}"
                    )
                total_files += files
                total_bytes += bytes_freed

        mb_saved = total_bytes / (1024 * 1024)
        if dry_run:
            return (
                f"Browser Cache: Would clean {total_files} files "
                f"({mb_saved:.2f} MB would be freed) (preview)"
            )
        return f"Browser Cache: Cleaned {total_files} files ({mb_saved:.2f} MB freed)"
