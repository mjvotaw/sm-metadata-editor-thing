import logging
from logging.handlers import RotatingFileHandler
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
import sys
from collections import deque
from typing import Tuple

class LogHandler(logging.Handler, QObject):

    log_emitted = pyqtSignal(int, str) # level, message

    def __init__(self, max_buffer_size: int = 1000):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.log_buffer: deque[Tuple[int, str]] = deque(maxlen=max_buffer_size)
    
    def emit(self, record):
        msg = self.format(record)
        log_level = record.levelno
        self.log_buffer.append((log_level, msg))
        self.log_emitted.emit(log_level, msg)
    
    def get_buffered_logs(self) -> list[Tuple[int, str]]:
        """
        Get all buffered log messages.
        Returns list of (level, message) tuples.
        """
        return list(self.log_buffer)
    
    def clear_buffer(self):
        """Clear the log buffer."""
        self.log_buffer.clear()



def setup_logging(log_dir: Path|None = None, log_level: str='DEBUG', gui_handler: LogHandler|None = None):
    """
    Configure application-wide logging.
    
    Args:
        log_dir: Directory for log files (default: ~/.simfile_editor/logs)
        gui_handler: Optional handler for GUI log display
    """
    # Create logger
    logger = logging.getLogger('simfile_editor')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler (for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (rotating log files)
    if log_dir is None:
        log_dir = Path.home() / '.simfile_editor' / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'simfile_editor.log'
    
    # Rotate when file reaches 5MB, keep 3 backup files
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # GUI handler (if provided)
    if gui_handler:
        gui_handler.setLevel(logging.DEBUG)
        gui_handler.setFormatter(console_formatter)
        logger.addHandler(gui_handler)
    
    return logger

def teardown_logging(gui_handler: LogHandler):
    logger = logging.getLogger('simfile_editor')
    logger.removeHandler(gui_handler)
    gui_handler.close()

def get_logger(name: str|None = None):
    """
    Get a logger instance.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Loading simfile...")
        logger.error("Failed to load file", exc_info=True)
    """
    if name:
        return logging.getLogger(f'simfile_editor.{name}')
    return logging.getLogger('simfile_editor')
