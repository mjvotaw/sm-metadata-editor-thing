import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, 
    QHBoxLayout, QComboBox, QLabel, QFileDialog
)
from PyQt6.QtGui import QTextCursor, QColor
from PyQt6.QtCore import pyqtSlot
from pathlib import Path
from typing import Tuple

from src.utils.app_paths import AppPaths
from src.utils.logger import LogHandler

class LogViewerDialog(QDialog):
    """Dialog for viewing application logs."""
    
    LEVEL_COLORS = {
        'DEBUG': QColor(100, 100, 100),
        'INFO': QColor(0, 0, 0),
        'WARNING': QColor(200, 100, 0),
        'ERROR': QColor(200, 0, 0),
        'CRITICAL': QColor(255, 0, 0),
    }
    
    def __init__(self, log_handler: LogHandler, parent=None):
        super().__init__(parent)
        self.log_handler = log_handler
        self.buffered_logs: list[Tuple[int, str]] = []
        self.filter_level = logging.NOTSET
        self.setWindowTitle("Application Logs")
        self.resize(800, 600)
        self.setup_ui()
        self.load_buffered_logs()
        # Connect to log handler
        self.log_handler.log_emitted.connect(self.append_log)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Top controls
        controls = QHBoxLayout()
        
        # Level filter
        controls.addWidget(QLabel("Filter:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR'])
        self.level_filter.setCurrentText('ALL')
        self.level_filter.currentTextChanged.connect(self.apply_filter)
        controls.addWidget(self.level_filter)
        
        controls.addStretch()
        
        # Buttons
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_logs)
        controls.addWidget(self.clear_btn)
        
        layout.addLayout(controls)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_display)
        
        # Bottom info
        log_dir = AppPaths.log_dir()
        self.info_label = QLabel(f"Logs are stored in: {log_dir}")
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)

    def load_buffered_logs(self):
        self.buffered_logs = self.log_handler.get_buffered_logs()
        if self.buffered_logs:
            for level, message in self.buffered_logs:
                self._display_log(level, message)

    
    @pyqtSlot(int, str)
    def append_log(self, level: int, message: str):
        """Append a new log message with appropriate coloring."""
        self.buffered_logs.append((level, message))
        self._display_log(level, message)
    
    def _display_log(self, level: int, message: str):
        if self.filter_level == logging.NOTSET or level >= self.filter_level:
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            level_name = logging.getLevelName(level)

            # Apply color based on level
            color = self.LEVEL_COLORS.get(level_name, QColor(0, 0, 0))
            cursor.insertHtml(
                f'<span style="color: rgb({color.red()}, {color.green()}, {color.blue()});">'
                f'{message}</span><br>'
            )
            
            # Auto-scroll to bottom
            self.log_display.setTextCursor(cursor)
            self.log_display.ensureCursorVisible()
    
    def clear_logs(self):
        self.log_display.clear()
        self.buffered_logs = []
    
    def apply_filter(self, text:str):
        
        if text == "ALL":
            self.filter_level = logging.NOTSET
        else:
            level_names_map = logging.getLevelNamesMapping()
            if text in level_names_map:
                self.filter_level = level_names_map[text]
            else:
                self.filter_level = logging.NOTSET

        # clear display and re-apply the buffered logs
        self.log_display.clear()
        for level, message in self.buffered_logs:
            self._display_log(level, message)

    