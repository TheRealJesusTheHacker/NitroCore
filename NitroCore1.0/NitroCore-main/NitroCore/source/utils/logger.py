import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Union

class Logger:
    """
    High-performance, thread-safe logging utility built for NitroCore.
    Prevents file-locking bottlenecks when multiple system modules log simultaneously.
    """
    
    def __init__(self, name: str = 'app', level: int = logging.INFO, log_filename: str = 'nitrocore.log'):
        """Initialize logger with dynamic instance naming and independent file targets"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Enforce strict propagation boundaries to prevent console duplication
        self.logger.propagate = False
        
        # Prevent duplicate handlers if the logger instance already exists in memory
        if not self.logger.handlers:
            self._setup_handlers(log_filename)
            
    def _setup_handlers(self, log_filename: str) -> None:
        """Sets up asynchronous, thread-safe log sinks for console and file outputs"""
        # Formatter layout matching enterprise diagnostic standards
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. Console Stream Handler (Uses stderr for errors/system output tracking)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        
        # 2. Disk Space Safe Rotating File Handler
        log_dir = Path(os.path.realpath(os.path.expandvars('%APPDATA%\\NitroCore\\logs')))
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / log_filename
        
        # MaxBytes limits file growth to 5MB, maintaining 3 archived backups max
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=5 * 1024 * 1024, 
            backupCount=3,
            encoding='utf-8' # Prevents encoding failures on global Windows locales
        )
        file_handler.setFormatter(formatter)
        
        # 3. QueueHandler Wrap (The Secret to Max Multi-Threading Performance)
        # Instead of writing directly to the disk file on the current execution thread, 
        # Python pushes log entries to an internal memory queue, making log calls near-instantaneous.
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def debug(self, msg: str) -> None:
        self.logger.debug(msg)
        
    def info(self, msg: str) -> None:
        self.logger.info(msg)
        
    def warning(self, msg: str) -> None:
        self.logger.warning(msg)
        
    def error(self, msg: str, exc_info: Union[bool, Exception] = False) -> None:
        """
        Logs error diagnostic records. 
        Pass exc_info=True inside an 'except' block to automatically capture full stack traces.
        """
        self.logger.error(msg, exc_info=exc_info)
        
    def critical(self, msg: str, exc_info: Union[bool, Exception] = False) -> None:
        self.logger.critical(msg, exc_info=exc_info)

    @classmethod
    def get_logger(cls, name: str = 'app', log_filename: str = 'nitrocore.log') -> 'Logger':
        """Named instantiation accessor helper"""
        return cls(name, log_filename=log_filename)
