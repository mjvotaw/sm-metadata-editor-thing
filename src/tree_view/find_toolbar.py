import re
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton,
    QLabel, QToolButton 
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt6.QtGui import QKeySequence, QShortcut

from src.tree_view.simfile_tree_model import TreeColumn
from src.utils.logger import get_logger
logger = get_logger(__name__)

class FindToolbar(QWidget):

    searchChanged = pyqtSignal(str, object, bool, bool)  # text, field (TreeColumn or None), use_regex, case_sensitive
    filterToggled = pyqtSignal(bool)  # filter_enabled
    nextRequested = pyqtSignal()
    prevRequested = pyqtSignal()
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_result_index = -1
        self.total_results = 0
        
        self.setup_ui()
        self.setup_shortcuts()
        
        # Connect internal signals
        self.search_input.textChanged.connect(self._on_search_changed)
        self.field_combo.currentIndexChanged.connect(self._on_search_changed)
        self.regex_checkbox.toggled.connect(self._on_search_changed)
        self.case_checkbox.toggled.connect(self._on_search_changed)
        self.filter_checkbox.toggled.connect(self.filterToggled)
        
        self.next_button.clicked.connect(self.nextRequested)
        self.prev_button.clicked.connect(self.prevRequested)
        self.close_button.clicked.connect(self.close_toolbar)
    
    def setup_ui(self):
        """Build the toolbar UI."""
        layout = QHBoxLayout()
        layout.setSpacing(3)

        layout.setContentsMargins(0,0,0,0)
        
        # Close button
        self.close_button = QToolButton()
        self.close_button.setText("×")
        self.close_button.setToolTip("Close find toolbar (Esc)")
        layout.addWidget(self.close_button)
        
        # Label
        find_label = QLabel("Find:")
        layout.addWidget(find_label)
        
        # Field selector
        self.field_combo = QComboBox()
        self.field_combo.addItem("All Fields", None)
        self.field_combo.addItem("Title", TreeColumn.TITLE)
        self.field_combo.addItem("Subtitle", TreeColumn.SUBTITLE)
        self.field_combo.addItem("Artist", TreeColumn.ARTIST)
        self.field_combo.addItem("Genre", TreeColumn.GENRE)
        self.field_combo.setToolTip("Select which field to search")
        self.field_combo.setMinimumWidth(120)
        layout.addWidget(self.field_combo)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(200)
        layout.addWidget(self.search_input)
        
        # Regex checkbox
        self.regex_checkbox = QPushButton(".*")
        self.regex_checkbox.setCheckable(True)
        self.regex_checkbox.setToolTip("Use regular expressions")
        layout.addWidget(self.regex_checkbox)
        
        self.case_checkbox = QPushButton("aA")
        self.case_checkbox.setCheckable(True)
        self.case_checkbox.setToolTip("Match case")
        layout.addWidget(self.case_checkbox)

        # Results count label
        self.results_label = QLabel("No results")
        self.results_label.setMinimumWidth(100)
        layout.addWidget(self.results_label)
        
        # Previous button
        self.prev_button = QPushButton("▲")
        self.prev_button.setToolTip("Previous result (Shift+F3)")
        self.prev_button.setEnabled(False)
        layout.addWidget(self.prev_button)
        
        # Next button
        self.next_button = QPushButton("▼")
        self.next_button.setToolTip("Next result (F3)")
        self.next_button.setEnabled(False)
        layout.addWidget(self.next_button)
        
        # Filter checkbox
        self.filter_checkbox = QPushButton("Show only matches")
        self.filter_checkbox.setCheckable(True)
        self.filter_checkbox.setToolTip("Hide non-matching simfiles from tree")
        layout.addWidget(self.filter_checkbox)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the toolbar."""
        # F3 - Next result
        next_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F3), self)
        next_shortcut.activated.connect(self.nextRequested)
        
        # Shift+F3 - Previous result
        prev_shortcut = QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Key.Key_F3), self)
        prev_shortcut.activated.connect(self.prevRequested)
        
        # Escape - Close toolbar
        close_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        close_shortcut.activated.connect(self.close_toolbar)
        
        # Enter/Return in search box - Next result
        self.search_input.returnPressed.connect(self.nextRequested)
    
    def show_and_focus(self):
        """Show the toolbar and focus the search input."""
        self.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    @pyqtSlot()
    def close_toolbar(self):
        """Close the toolbar and emit closed signal."""
        self.setVisible(False)
        self.search_input.clear()
        self.closed.emit()
    
    @pyqtSlot()
    def _on_search_changed(self):
        """Handle search criteria changes."""
        text = self.search_input.text()
        field = self.field_combo.currentData()  # TreeColumn or None
        use_regex = self.regex_checkbox.isChecked()
        case_sensitive = self.case_checkbox.isChecked()

        if use_regex:
            try:
                case_flag = re.IGNORECASE if not case_sensitive else 0
                regex = re.compile(text, case_flag)
            except re.error as e:
                logger.error(f"Invalid regex: {e}")
                self.set_results_label("Invalid regex", True)
                return
        self.searchChanged.emit(text, field, use_regex, case_sensitive)
    
    def update_results(self, total: int, current: int = -1):
        """
        Update the results display.
        
        Args:
            total: Total number of matching results
            current: Current result index (0-based), or -1 if none selected
        """
        self.total_results = total
        self.current_result_index = current
        
        # Update label
        if total == 0:
            self.set_results_label("No results", True)
        else:
            if current >= 0:
                self.set_results_label(f"{current + 1} of {total} results")
            else:
                self.set_results_label(f"{total} result{'s' if total != 1 else ''}")
        
        # Enable/disable navigation buttons
        has_results = total > 0
        self.next_button.setEnabled(has_results)
        self.prev_button.setEnabled(has_results)
    
    def set_results_label(self, msg: str, is_error: bool=False):
        self.results_label.setText(msg)
        if is_error:
            self.results_label.setStyleSheet("color: #666666; font-style: italic;")
        else:
            self.results_label.setStyleSheet("")
    def clear_search(self):
        """Clear the search input."""
        self.search_input.clear()
    
    def get_search_text(self) -> str:
        """Get current search text."""
        return self.search_input.text()
    
    def get_search_field(self) -> Optional[TreeColumn]:
        """Get currently selected search field (None = all fields)."""
        return self.field_combo.currentData()
    
    def is_regex_enabled(self) -> bool:
        """Check if regex search is enabled."""
        return self.regex_checkbox.isChecked()
    
    def is_filter_enabled(self) -> bool:
        """Check if tree filtering is enabled."""
        return self.filter_checkbox.isChecked()