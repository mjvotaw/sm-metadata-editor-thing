import re
from typing import Optional
from PyQt6.QtCore import QAbstractItemModel, QSortFilterProxyModel, Qt, QModelIndex
from src.tree_view.simfile_tree_model import TreeColumn, SimfileTreeModel
from src.models import SimfileMetadata

from src.utils.logger import get_logger
logger = get_logger(__name__)

class SimfileFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering simfiles based on search criteria."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.search_field:TreeColumn|None = None  # None means "All fields"
        self.use_regex:bool = False
        self.case_sensitive: bool = False
        self.filter_enabled:bool = False  # Whether to actually filter or just track results

        # Cache compiled regex
        self._compiled_regex = None
    
    def get_simfile_id_from_index(self, proxy_index: QModelIndex) -> Optional[str]:
        """Get simfile ID from a proxy index."""
        source_model = self._tree_model
        if not source_model:
            return None
        
        # Map proxy index to source index
        source_index = self.mapToSource(proxy_index)
        
        # Use source model's helper
        return source_model.get_simfile_id_from_index(source_index)

    def get_simfile_from_index(self, proxy_index: QModelIndex) -> Optional[SimfileMetadata]:
        """Get SimfileMetadata from a proxy index."""
        source_model = self._tree_model
        if not source_model:
            return None
        
        source_index = self.mapToSource(proxy_index)
        return source_model.get_simfile_from_index(source_index)

    def is_pack_index(self, proxy_index: QModelIndex) -> bool:
        """Check if proxy index represents a pack."""
        source_model = self._tree_model
        if not source_model:
            return False
        
        source_index = self.mapToSource(proxy_index)
        return source_model.is_pack_index(source_index)

    def is_simfile_index(self, proxy_index: QModelIndex) -> bool:
        """Check if proxy index represents a simfile."""
        source_model = self._tree_model
        if not source_model:
            return False
        
        source_index = self.mapToSource(proxy_index)
        return source_model.is_simfile_index(source_index)

    def setSourceModel(self, sourceModel: QAbstractItemModel | None) -> None:
        if sourceModel is not None and not isinstance(sourceModel, SimfileTreeModel):
            raise TypeError(f"Expected SimfileTreeModel, got {type(sourceModel)}")
        
        self._tree_model = sourceModel
        return super().setSourceModel(sourceModel)
    
    def set_search_criteria(self, text: str, field: TreeColumn|None = None, use_regex: bool = False, case_sensitive: bool = False):
        """Update search criteria and refresh filter."""
        self.search_text = text
        self.search_field = field
        self.use_regex = use_regex
        self.case_sensitive = case_sensitive

        # Compile regex if needed
        if use_regex and text:
            try:
                regex_case = re.IGNORECASE if not case_sensitive else 0
                self._compiled_regex = re.compile(text, regex_case)
            except re.error as e:
                logger.error(f"Error compiling regex: {e}")
                self._compiled_regex = None
        else:
            self._compiled_regex = None
        
        self.invalidateFilter()
    
    def set_filter_enabled(self, enabled: bool):
        """Toggle whether filtering is active."""
        self.filter_enabled = enabled
        self.setDynamicSortFilter(enabled)
        self.invalidateFilter()
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Determine if a row should be shown."""
        # If filtering is disabled, show everything
        if not self.filter_enabled or not self.search_text:
            return True
        
        source_model = self._tree_model
        if not source_model:
            return False
        index = source_model.index(source_row, 0, source_parent)
        
        # Always show packs (they're containers)
        if source_model.is_pack_index(index):
            # But only show packs that have matching children
            return self._pack_has_matching_children(source_row, source_parent)
        
        # For simfiles, check if they match
        return self._row_matches_search(source_row, source_parent)
    
    def _pack_has_matching_children(self, pack_row: int, parent: QModelIndex) -> bool:
        """Check if any children of this pack match the search."""
        source_model = self.sourceModel()
        if not source_model:
            return False
        pack_index = source_model.index(pack_row, 0, parent)
        
        child_count = source_model.rowCount(pack_index)
        for child_row in range(child_count):
            if self._row_matches_search(child_row, pack_index):
                return True
        return False
    
    def _row_matches_search(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Check if a simfile row matches search criteria."""
        source_model = self._tree_model
        if source_model is None:
            return False
        
        # Determine which fields to search
        if self.search_field:
            fields_to_search = [self.search_field]
        else:
            # Search all text fields
            fields_to_search = [
                TreeColumn.TITLE,
                TreeColumn.SUBTITLE,
                TreeColumn.ARTIST,
                TreeColumn.GENRE
            ]
        
        # Check each field
        for field in fields_to_search:
            column_index = source_model.get_column_order().index(field)
            index = source_model.index(source_row, column_index, source_parent)
            value = source_model.data(index, Qt.ItemDataRole.DisplayRole) or ""
            
            if self._text_matches(value):
                return True
        
        return False
    
    def _text_matches(self, text: str) -> bool:
        """Check if text matches search criteria."""
        if not self.search_text:
            return True
        
        if self.use_regex and self._compiled_regex:
            return self._compiled_regex.search(text) is not None
        else:
            if self.case_sensitive:
                return self.search_text in text
            else:
                return self.search_text.lower() in text.lower()
    
    def get_matching_rows(self) -> list[QModelIndex]:
        """Get all rows that match current search (in proxy coordinates)."""
        matches = []
        self._collect_matches(QModelIndex(), matches)
        return matches
    
    def _collect_matches(self, parent: QModelIndex, matches: list):
        """Recursively collect matching rows."""
        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            
            # Map to source to check if it's a simfile
            source_index = self.mapToSource(index)
            source_model = self._tree_model
            if source_model is not None:
                if source_model.is_simfile_index(source_index):
                    # It's a simfile - check if it matches
                    source_parent = source_index.parent()
                    if self._row_matches_search(source_index.row(), source_parent):
                        matches.append(index)
            
            # Recursively check children
            if self.hasChildren(index):
                self._collect_matches(index, matches)