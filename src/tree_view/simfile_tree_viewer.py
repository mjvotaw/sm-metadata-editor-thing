from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSlot, QPoint, QModelIndex
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QHeaderView, QMenu, QTreeView, QApplication, QMessageBox
from src.controller import SimfileController
from src.tree_view.simfile_tree_model import SimfileTreeModel, TreeColumn
from src.tree_view.filter_proxy_model import SimfileFilterProxyModel
from src.utils.config_manager import ConfigEnum, ConfigManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SimfileTree(QTreeView):


    def __init__(self, controller: SimfileController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.config = ConfigManager()

        self._initialize_column_order()
        self._setup_ui()

    def refresh(self):
        self.tree_model.refresh()

    def _initialize_column_order(self):
        column_widths: dict[TreeColumn, int] = self.config.get(ConfigEnum.COLUMN_WIDTHS)
        self.column_widths = column_widths

    def _setup_ui(self):
        self._setup_tree_view(self.controller)
        self._setup_header()
        self._setup_selection_change()
        self._setup_context_menu()

    def _setup_tree_view(self, controller:SimfileController):
        self.tree_model = SimfileTreeModel(controller)
        self.proxy_model = SimfileFilterProxyModel()
        self.proxy_model.setSourceModel(self.tree_model)
        
        self.setModel(self.proxy_model)
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    
    def _setup_header(self):
        header = self.header()
        if header is not None:
            for index, column in enumerate(self.tree_model.get_column_order()):
                
                if SimfileTreeModel.COLUMN_CONFIG[column].resizable:
                    header.setSectionResizeMode(index, QHeaderView.ResizeMode.Interactive)
                else:
                    header.setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)
                
                default_width = SimfileTreeModel.COLUMN_CONFIG[column].default_width
                if self.column_widths and column in self.column_widths:
                        header.resizeSection(index, self.column_widths[column])
                elif default_width:
                    header.resizeSection(index, default_width)

            header.setStretchLastSection(False)
    
    def _setup_selection_change(self):
        selection_model = self.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self.on_tree_selection_changed)

    def _setup_context_menu(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_tree_contexts_menu)

    @pyqtSlot()
    def on_tree_selection_changed(self):
        indexes = self.selectedIndexes()
        
        simfile_ids = set()
        for index in indexes:
            if index.column() == 0:

                simfile_id = self.proxy_model.get_simfile_id_from_index(index)
                if simfile_id:
                    simfile_ids.add(simfile_id)
        
        self.controller.set_selection(simfile_ids)

    @pyqtSlot(QPoint)
    def on_tree_contexts_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return

        is_simfile = self.proxy_model.is_simfile_index(index)

        menu = None
        if is_simfile:
            menu = self._build_simfile_context_menu(index)

        if menu is not None:
            viewport = self.viewport()
            if viewport is not None:
                menu.exec(viewport.mapToGlobal(position))

    def _build_simfile_context_menu(self, index: QModelIndex):
        simfile = self.proxy_model.get_simfile_from_index(index)
        if simfile is None:
            return None
        
        menu = QMenu(self)
        open_folder_action = QAction("Open Containing Folder", self)
        open_folder_action.triggered.connect(
            lambda: self.open_folder(simfile.file_path.parent)
        )
        menu.addAction(open_folder_action)
        
        # Copy path action
        copy_path_action = QAction("Copy File Path", self)
        copy_path_action.triggered.connect(
            lambda: self.copy_filepath(str(simfile.file_path))
        )
        menu.addAction(copy_path_action)
        
        menu.addSeparator()
        
        # Edit actions
        if simfile.is_modified():
            revert_action = QAction("Revert Changes", self)
            revert_action.triggered.connect(
                lambda: self.revert_simfile(simfile.id)
            )
            menu.addAction(revert_action)
        return menu

    def open_folder(self, folder_path:Path):
        import os
        import platform
        import subprocess
        
        logger.debug(f"Opening directory {folder_path}")

        system = platform.system()
        if system == "Windows":
            # os.startfile(folder_path)
            pass
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)])
        else:  # Linux
            subprocess.run(["xdg-open", str(folder_path)])

    def revert_simfile(self, simfile_id: str):
        reply = QMessageBox.question(
            self,
            "Revert Changes",
            "Discard all changes to this file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
    
        if reply == QMessageBox.StandardButton.Yes:
            simfile = self.controller.get_simfile(simfile_id)
            if simfile:
                logger.debug(f"Reverting all changes to simfile {simfile.title}")
                simfile.reset_to_original()
                self.tree_model.on_simfiles_changed([simfile_id])

    def copy_filepath(self, filepath: str):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(filepath)