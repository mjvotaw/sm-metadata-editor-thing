from typing import Optional
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from src.controller import SimfileController
from src.tree_view.simfile_tree_viewer import SimfileTree
from src.tree_view.simfile_tree_model import TreeColumn
from src.tree_view.find_toolbar import FindToolbar

class TreeViewContainer(QWidget):

    def __init__(self, controller: SimfileController, parent=None):
        super().__init__(parent)

        self.controller = controller
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0,0,0,0)
        self.tree_view = SimfileTree(self.controller)
        self._setup_find_toolbar()
        main_layout.addWidget(self.find_toolbar)
        main_layout.addWidget(self.tree_view, 1)

        self.setLayout(main_layout)

    def _setup_find_toolbar(self):
        self.find_toolbar = FindToolbar()
        self.find_toolbar.setFixedHeight(40)
        self.find_toolbar.setVisible(False)

        self.find_toolbar.searchChanged.connect(self.on_search_changed)
        self.find_toolbar.filterToggled.connect(self.on_filter_toggled)
        self.find_toolbar.nextRequested.connect(self.on_next_result)
        self.find_toolbar.prevRequested.connect(self.on_prev_result)
        self.find_toolbar.closed.connect(self.on_find_closed)


    def show_find(self):
        self.find_toolbar.show_and_focus()

    def refresh(self):
        self.tree_view.refresh()

    @pyqtSlot(bool)
    def on_filter_toggled(self, enabled: bool):
        """Handle filter checkbox toggle."""
        if hasattr(self.tree_view, 'proxy_model'):
            self.tree_view.proxy_model.set_filter_enabled(enabled)
            
            # Update match count (filtering might have changed visible results)
            matches = self.tree_view.proxy_model.get_matching_rows()
            self.find_toolbar.update_results(len(matches))
            self.current_matches = matches

    @pyqtSlot(str, object, bool, bool)
    def on_search_changed(self, text: str, field: Optional[TreeColumn], use_regex: bool, case_sensitive: bool):
        """Handle search criteria changes."""
        if hasattr(self.tree_view, 'proxy_model'):
            self.tree_view.proxy_model.set_search_criteria(text, field, use_regex, case_sensitive)
            
            # Don't store matches - just update the count
            match_count = len(self.tree_view.proxy_model.get_matching_rows())
            self.find_toolbar.update_results(match_count)
            
            # Reset navigation position
            self.find_toolbar.current_result_index = -1

    @pyqtSlot()
    def on_next_result(self):
        """Navigate to next search result."""
        matches = self._get_current_matches()
        if not matches:
            return
        
        current_index = self.find_toolbar.current_result_index
        next_index = (current_index + 1) % len(matches)
        self._select_result_at_index(next_index, matches)

    @pyqtSlot()
    def on_prev_result(self):
        """Navigate to previous search result."""
        matches = self._get_current_matches()
        if not matches:
            return
        
        current_index = self.find_toolbar.current_result_index
        prev_index = (current_index - 1) % len(matches)
        self._select_result_at_index(prev_index, matches)

    @pyqtSlot()
    def on_find_closed(self):
        """Handle find toolbar being closed."""
        # Clear any filtering
        if hasattr(self.tree_view, 'proxy_model'):
            self.tree_view.proxy_model.set_search_criteria("", None, False)
            self.tree_view.proxy_model.set_filter_enabled(False)

    def _get_current_matches(self) -> list:
        """Get fresh list of matching indexes."""
        if hasattr(self.tree_view, 'proxy_model'):
            return self.tree_view.proxy_model.get_matching_rows()
        return []
    
    def _select_result_at_index(self, index: int, matches: list):
        """Select and scroll to a specific result."""
        if not matches or index < 0 or index >= len(matches):
            return
        
        match_index = matches[index]
        
        if not match_index.isValid():
            return
        
        # Select the row
        selection_model = self.tree_view.selectionModel()
        if selection_model:
            selection_model.clearSelection()
            selection_model.select(
                match_index,
                selection_model.SelectionFlag.Select | selection_model.SelectionFlag.Rows
            )
            
            self.tree_view.scrollTo(match_index)
            self.find_toolbar.update_results(len(matches), index)