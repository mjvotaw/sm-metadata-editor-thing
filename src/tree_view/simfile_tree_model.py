from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Optional

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt

from src.controller import SimfileController
from src.models import SimfileMetadata, PackInfo
from src.field_registry import FieldRegistry
from src.utils.config_manager import ConfigEnum, ConfigManager
from src.utils.logger import get_logger
logger = get_logger(__name__)

class TreeColumn(Enum):
    """Column definitions for the tree view."""
    TITLE = 'title'
    SUBTITLE = 'subtitle'
    ARTIST = 'artist'
    GENRE = 'genre'
    CHARTS = 'charts'
    FILETYPE = 'filetype'


class TreeItem:
    """
    Internal helper class to represent items in the tree.
    
    This makes implementing QAbstractItemModel much easier because we can
    store parent/child relationships explicitly rather than computing them
    on the fly.
    
    Each TreeItem represents either:
    - A Pack (has children, no simfile)
    - A Simfile (no children, has simfile)
    """
    
    def __init__(self, data: Any, parent: Optional['TreeItem'] = None):
        self.data = data  # Either PackInfo or SimfileMetadata
        self.parent_item = parent
        self.children: list['TreeItem'] = []
    
    def append_child(self, child: 'TreeItem'):
        """Add a child item."""
        self.children.append(child)
    
    def child(self, row: int) -> Optional['TreeItem']:
        """Get child at given row."""
        if 0 <= row < len(self.children):
            return self.children[row]
        return None
    
    def child_count(self) -> int:
        """Return number of children."""
        return len(self.children)
    
    def row(self) -> int:
        """Return this item's row position in its parent."""
        if self.parent_item:
            return self.parent_item.children.index(self)
        return 0
    
    def parent(self) -> Optional['TreeItem']:
        """Return parent item."""
        return self.parent_item
    
    def is_pack(self) -> bool:
        """Check if this item represents a pack."""
        return isinstance(self.data, PackInfo)
    
    def is_simfile(self) -> bool:
        """Check if this item represents a simfile."""
        return isinstance(self.data, SimfileMetadata)

@dataclass
class TreeColumnConfig:
    header: str
    field: str
    sort_key_fn: Callable[[Any], Any]
    resizable: bool
    default_width:Optional[int]

class SimfileTreeModel(QAbstractItemModel):
    """
    Tree model for displaying simfiles organized by pack.
    
    Columns are dynamically configured based on COLUMN_CONFIG.
    """
    
    # Column configuration: maps TreeColumn enum to display properties
    COLUMN_CONFIG: dict[TreeColumn, TreeColumnConfig] = {
        TreeColumn.TITLE: TreeColumnConfig(
            header= 'Title',
            field= 'title',
            resizable=True,
            default_width=300,
            sort_key_fn= lambda sf: sf.title.lower(),
        ),
        TreeColumn.SUBTITLE: TreeColumnConfig(
            header= 'Subtitle',
            field= 'subtitle',
            resizable=True,
            default_width=200,
            sort_key_fn= lambda sf: (sf.subtitle or "").lower(),
        ),
        TreeColumn.ARTIST: TreeColumnConfig(
            header= 'Artist',
            field= 'artist',
            resizable=True,
            default_width=150,
            sort_key_fn= lambda sf: sf.artist.lower(),
        ),
        TreeColumn.GENRE: TreeColumnConfig(
            header= 'Genre',
            field= 'genre',
            resizable=False,
            default_width=None,
            sort_key_fn= lambda sf: sf.genre.lower(),
        ),
        TreeColumn.CHARTS: TreeColumnConfig(
            header= 'Chart Count',
            field= 'num_charts',
            resizable=False,
            default_width=None,
            sort_key_fn= lambda sf: sf.num_charts,
        ),
        TreeColumn.FILETYPE: TreeColumnConfig(
            header= 'File Type',
            field= 'file_type',
            resizable=False,
            default_width=None,
            sort_key_fn= lambda sf: sf.file_type,
        ),
    }
    
    @classmethod
    def get_header(cls, column: TreeColumn) -> str:
        """Get header text for a column."""
        return cls.COLUMN_CONFIG[column].header
    
    @classmethod
    def get_field(cls, column: TreeColumn) -> str:
        """Get field name for a column."""
        return cls.COLUMN_CONFIG[column].field
    
    @classmethod
    def get_sort_key_fn(cls, column: TreeColumn):
        """Get sort key function for a column."""
        return cls.COLUMN_CONFIG[column].sort_key_fn
    
    @classmethod
    def default_column_order(cls):
        column_order = [
                TreeColumn.TITLE,
                TreeColumn.SUBTITLE,
                TreeColumn.ARTIST,
                TreeColumn.GENRE,
                TreeColumn.CHARTS,
                TreeColumn.FILETYPE
            ]
        return column_order
    
    def __init__(self, controller: SimfileController, parent=None):
        super().__init__(parent)
        self.controller = controller

        # Create invisible root item (required for tree structure)
        self.root_item = TreeItem(None)
        
        # Build initial tree
        self._rebuild_tree()
        
        # Register for change notifications
        self.controller.register_change_callback(self.on_simfiles_changed)
    
    def _rebuild_tree(self):
        """
        Rebuild the entire tree structure from the controller data.
        
        This is called on initial load and can be called when the data
        structure changes significantly (like loading a new directory).
        """
        logger.debug(f"rebuilding tree")
        self.beginResetModel()
        self.root_item = TreeItem(None)
        packs = self.controller.get_all_packs()
        
        # Build tree structure
        for pack in sorted(packs, key=lambda p: p.name):
            pack_item = TreeItem(pack, self.root_item)
            self.root_item.append_child(pack_item)
            
            # Add simfiles under this pack
            simfiles = self.controller.get_simfiles_in_pack(pack.name)
            for simfile in sorted(simfiles, key=lambda s: s.title.lower()):
                simfile_item = TreeItem(simfile, pack_item)
                pack_item.append_child(simfile_item)
        
        # Notify views that reset is complete
        self.endResetModel()
        self.layoutChanged.emit()
    
    def on_simfiles_changed(self, affected_ids: list[str]):
        """
        Called when simfiles are modified.
        
        We need to find which rows changed and emit dataChanged for them.
        """
        # For simplicity, we'll emit dataChanged for each affected simfile
        # A more optimized version would batch these into ranges
        
        for simfile_id in affected_ids:
            index = self._find_index_for_simfile(simfile_id)
            if index.isValid():
                # Emit dataChanged for all columns of this row
                last_col_index = self.index(index.row(), self.column_count() - 1, index.parent())
                self.dataChanged.emit(index, last_col_index)
    
    def _find_index_for_simfile(self, simfile_id: str) -> QModelIndex:
        """Find the QModelIndex for a given simfile ID."""
        # Walk through the tree looking for this simfile
        for pack_row in range(self.root_item.child_count()):
            pack_item = self.root_item.child(pack_row)
            if pack_item is not None:
              for simfile_row in range(pack_item.child_count()):
                  simfile_item = pack_item.child(simfile_row)
                  if simfile_item is not None:
                    if simfile_item.is_simfile() and simfile_item.data.id == simfile_id:
                        return self.createIndex(simfile_row, 0, simfile_item)
        
        return QModelIndex()
    
    def get_column_order(self):
        # TODO: is this wildly inefficient, reading from ConfigManager
        # constantly? 
        # Maybe I need to add a "configChanged" signal from ConfigManager,
        # and update stuff when that happens
        column_order:list[TreeColumn] = self.controller.config.get(ConfigEnum.COLUMNS_TO_DISPLAY)
        if column_order is None:
            column_order = self.default_column_order()
        return column_order

    def column_count(self) -> int:
        """Get total number of columns."""
        return len(self.get_column_order())
    
    # ==================== Required QAbstractItemModel Methods ====================
    
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """
        Create a QModelIndex for the given row, column, and parent.
        
        This is one of the most important methods. Qt calls this to get
        indexes for items it wants to display or interact with.
        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        # Get the parent item
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        
        # Get the child item
        child_item = parent_item.child(row)
        if child_item:
            # Create index with child_item as the internal pointer
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()
    
    def parent(self, index: QModelIndex) -> QModelIndex:
        """
        Return the parent index of the given index.
        
        Another crucial method. Qt uses this to understand the tree hierarchy.
        """
        if not index.isValid():
            return QModelIndex()
        
        # Get the item from the index
        child_item = index.internalPointer()
        parent_item = child_item.parent()
        
        # If parent is root, return invalid index
        if parent_item is None or parent_item == self.root_item:
            return QModelIndex()
        
        # Create index for parent
        return self.createIndex(parent_item.row(), 0, parent_item)
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Return the number of rows under the given parent.
        
        For packs, this returns the number of simfiles.
        For simfiles, this returns 0 (they have no children).
        For the root, this returns the number of packs.
        """
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        
        if parent_item is None or not isinstance(parent_item, TreeItem):
            print(f"{parent_item}")
            return 0
        
        return parent_item.child_count()
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns."""
        return self.column_count()
    
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Return data for the given index and role.
        """
        if not index.isValid():
            return None
        
        item = index.internalPointer()
        column_order = self.get_column_order()
        if len(column_order) <= index.column():
            return None
        column = column_order[index.column()]
        
        # Display role - the text shown in the cell
        if role == Qt.ItemDataRole.DisplayRole:
            if item.is_pack():
                if column == TreeColumn.TITLE:
                    return item.data.name
                else:
                    return ""  # Packs don't have other fields
            
            elif item.is_simfile():
                simfile = item.data
                field_name = self.get_field(column)
                value = str(getattr(simfile, field_name, ""))                
                return value or ""
        
        # Tooltip role - shown when hovering
        elif role == Qt.ItemDataRole.ToolTipRole:
            if item.is_simfile():
                simfile = item.data
                if column == TreeColumn.TITLE:
                    tooltip = f"Title: {simfile.title}\n"
                    if simfile.subtitle:
                        tooltip += f"Subtitle: {simfile.subtitle}\n"
                    tooltip += f"File: {simfile.file_path}"
                    if simfile.is_modified():
                        tooltip += "\n\n(Modified - unsaved changes)"
                    return tooltip
        
        # Font role - customize font
        elif role == Qt.ItemDataRole.FontRole:
            from PyQt6.QtGui import QFont
            font = QFont()
            
            if item.is_pack():
                font.setBold(True)
                return font
            elif item.is_simfile() and item.data.is_modified():
                # Make modified simfiles bold
                font.setBold(True)
                return font
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return header data for the given section (column)."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < self.column_count():
                column_order = self.get_column_order()                
                column = column_order[section]
                return self.get_header(column)
        
        return None
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """Sort the tree by the given column."""
        self.layoutAboutToBeChanged.emit()
        
        # Convert column index to TreeColumn enum
        try:
            column_order = self.get_column_order()
            col_enum = column_order[column]
        except ValueError:
            # Invalid column
            self.layoutChanged.emit()
            return
        
        # Get sort key function for this column
        simfile_sort_key_fn = self.get_sort_key_fn(col_enum)
        
        # Define sort keys for each item type
        def get_sort_key(item: TreeItem):
            if item.is_pack():
                # Packs sort by name for title column, empty string otherwise
                if col_enum == TreeColumn.TITLE:
                    return item.data.name.lower()
                else:
                    return ""
            elif item.is_simfile():
                return simfile_sort_key_fn(item.data)
            return ""
        
        # Sort each pack's children (simfiles) and the packs themselves
        reverse = (order == Qt.SortOrder.DescendingOrder)
        
        for pack_item in self.root_item.children:
            if pack_item.child_count() > 0:
                pack_item.children.sort(key=get_sort_key, reverse=reverse)
        
        self.root_item.children.sort(key=get_sort_key, reverse=reverse)
        
        self.layoutChanged.emit()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """
        Return flags indicating what can be done with this item.
        
        We make simfiles selectable and enabled.
        Packs are enabled but we could make them non-selectable if desired.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        # Default flags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
        return flags
    
    # ==================== Helper Methods for GUI ====================
    
    def get_simfile_from_index(self, index: QModelIndex) -> Optional[SimfileMetadata]:
        """
        Get the SimfileMetadata object from a QModelIndex.
        Returns None if the index represents a pack or is invalid.
        """
        if not index.isValid():
            return None
        
        item = index.internalPointer()
        if item.is_simfile():
            return item.data
        
        return None
    
    def get_simfile_id_from_index(self, index: QModelIndex) -> Optional[str]:
        """
        Get the simfile ID from a QModelIndex.
        Returns None if the index represents a pack or is invalid.
        """
        simfile = self.get_simfile_from_index(index)
        if simfile:
            return simfile.id
        return None
    
    def is_pack_index(self, index: QModelIndex) -> bool:
        """Check if an index represents a pack."""
        if not index.isValid():
            return False
        
        item = index.internalPointer()
        return item.is_pack()
    
    def is_simfile_index(self, index: QModelIndex) -> bool:
        """Check if an index represents a simfile."""
        if not index.isValid():
            return False
        
        item = index.internalPointer()
        return item.is_simfile()
    
    def refresh(self):
        """Force a complete refresh of the tree."""
        self._rebuild_tree()