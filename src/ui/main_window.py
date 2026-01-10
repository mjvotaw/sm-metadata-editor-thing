from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QMessageBox, QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QMoveEvent, QResizeEvent

from src.utils.config_manager import ConfigManager, ConfigEnum
from src.utils.logger import LogHandler, setup_logging, teardown_logging, get_logger
from src.utils.app_paths import AppPaths

from src.controller import SimfileController
from src.ui.simfile_editor_panel import SimfileEditorPanel
from src.tree_view.tree_view_container import TreeViewContainer
from src.loader_thread import LoaderThread

from src.ui.log_viewer import LogViewerDialog
from src.ui.settings_dialog import SettingsDialog

from src.ui.status_display import StatusDisplay

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()

        self.config = ConfigManager()
        self.setup_logging()

        logger.info("Application started")
        self.setWindowTitle("SM Metadata Editor Thing")
        
        self.controller = SimfileController()
        self.controller.register_change_callback(self.on_data_changed)
        self.loader_thread = None
        
        self.create_menu_actions()
        self.setup_ui()
        self.update_action_states()
        self.restore_window_state()
    
    def setup_logging(self):
        self.log_handler = LogHandler()
        log_level = self.config.get(ConfigEnum.LOG_LEVEL, 'INFO')
        setup_logging(AppPaths.log_dir(), log_level=log_level, gui_handler=self.log_handler)
    
    def teardown_logging(self):
        if self.log_handler:
            teardown_logging(self.log_handler)
            self.log_handler = None


    def restore_window_state(self):
        width, height = self.config.get(ConfigEnum.WINDOW_SIZE, [1000, 800])
        self.resize(width, height)

        position = self.config.get(ConfigEnum.WINDOW_POSITION)
        if position:
            self.move(position[0], position[1])

    def setup_ui(self):
        """Set up the UI."""

        self.create_menus()
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)

        central.setLayout(main_layout)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setContentsMargins(0,0,0,0)
        self.tree_view = TreeViewContainer(self.controller)
        splitter.addWidget(self.tree_view)

        self.editor_panel = SimfileEditorPanel(self.controller)
        splitter.addWidget(self.editor_panel)
        splitter.setSizes([700,300])
        main_layout.addWidget(splitter)

        self.status_bar =  StatusDisplay(self)
        self.status_bar.cancel_requested.connect(self.on_cancel_loading)
        self.setStatusBar(self.status_bar)
    
        self.showStatusMessage("Ready")
    
    def create_menu_actions(self):
        """Create all QAction objects for menus."""
        # File menu actions
        self.load_action = QAction("&Load Directory...", self)
        self.load_action.setShortcut("Ctrl+O")
        self.load_action.triggered.connect(self.on_load_clicked)
        
        self.save_action = QAction("&Save Changes", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.on_save_clicked)
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # Edit menu actions
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.on_undo_clicked)
        
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.on_redo_clicked)

        self.find_action = QAction("&Find...", self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.triggered.connect(self.on_show_find)

        # View menu actions
        self.view_logs_action = QAction("View &Logs", self)
        self.view_logs_action.setShortcut("Ctrl+L")
        self.view_logs_action.triggered.connect(self.on_view_logs)

        self.view_settings_action = QAction("Settings", self)
        self.view_settings_action.triggered.connect(self.on_view_settings)

        # Action menu actions

        self.normalize_genre_action = QAction("Search/Normalize Genres", self)
        self.normalize_genre_action.triggered.connect(self.on_normalize_genres)

    
    def create_menus(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        if menubar is not None:
            menubar.setNativeMenuBar(False)
            file_menu = menubar.addMenu("&File")
            if file_menu is not None:
                file_menu.addAction(self.load_action)
                file_menu.addAction(self.save_action)
                file_menu.addSeparator()
                file_menu.addAction(self.exit_action)
            
            edit_menu = menubar.addMenu("&Edit")
            if edit_menu is not None:
                edit_menu.addAction(self.undo_action)
                edit_menu.addAction(self.redo_action)
                edit_menu.addAction(self.find_action)
            
            view_menu = menubar.addMenu("&View")
            if view_menu:
                view_menu.addAction(self.view_logs_action)
                view_menu.addAction(self.view_settings_action)
            
            actions_menu = menubar.addMenu("Actions")
            if actions_menu:
                actions_menu.addAction(self.normalize_genre_action)

    @pyqtSlot()
    def on_load_clicked(self):
        """Handle load directory button."""

        starting_dir = self.config.get(ConfigEnum.LAST_DIR, None) or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Songs Directory",
            starting_dir
        )
        
        if directory:
            self.config.set(ConfigEnum.LAST_DIR, directory)
            self.load_directory(Path(directory))
    
    @pyqtSlot()
    def on_cancel_loading(self):
        """Handle cancel loading button."""
        if self.loader_thread and self.loader_thread.isRunning():
            self.showStatusMessage("Cancelling load...")
            self.status_bar.hide_loading()
            self.loader_thread.cancel()
    
    @pyqtSlot(int, int, str)
    def on_loading_progress(self, current: int, total: int, pack_name: str):
        
        self.status_bar.show_loading_message(current, total, pack_name)
        
    
    @pyqtSlot(str)
    def on_pack_loaded(self, pack_name: str):
        """
        Called when a pack finishes loading.
        We can incrementally update the tree here for better perceived performance.
        """
        
        self.tree_view.refresh()
    
    @pyqtSlot(int, int)
    def on_loading_complete(self, total_loaded: int, failed_count: int):
        """Called when all loading is complete."""

        was_cancelled = self.loader_thread and self.loader_thread._cancelled
        
        self.status_bar.hide_loading()

        self.load_action.setEnabled(True)
        self.tree_view.refresh()
        
        failed_msg = f" ({failed_count} failed)" if failed_count > 0 else ""

        if was_cancelled:
            self.showStatusMessage(f"Loading cancelled - loaded {total_loaded} simfiles{failed_msg}")
        else:
            self.showStatusMessage(f"Loaded {total_loaded} simfiles{failed_msg}")
        
        self.update_action_states()
        
        if self.loader_thread:
            self.loader_thread.wait()
            self.loader_thread = None
    
    def load_directory(self, directory: Path):
        """Load simfiles from a directory asynchronously."""

        self.load_action.setEnabled(False)
        self.status_bar.show_loading()
        self.showStatusMessage("Preparing to load...")
        
        self.loader_thread = LoaderThread(self.controller, directory)
        self.loader_thread.progress_update.connect(self.on_loading_progress)
        self.loader_thread.pack_loaded.connect(self.on_pack_loaded)
        self.loader_thread.loading_complete.connect(self.on_loading_complete)
        
        self.loader_thread.start()
    
    
    @pyqtSlot()
    def on_save_clicked(self):
        """Handle save button."""
        if not self.controller.has_unsaved_changes():
            QMessageBox.information(self, "Save", "No unsaved changes")
            return
        
        # Confirm
        modified_count = len(self.controller.get_modified_simfiles())
        reply = QMessageBox.question(
            self,
            "Save Changes",
            f"Save changes to {modified_count} simfile(s)?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel
        )
        
        if reply != QMessageBox.StandardButton.Save:
            return
        
        # Save
        self.showStatusMessage("Saving...")
        QApplication.processEvents()
        
        results = self.controller.save_changes()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            QMessageBox.information(
                self,
                "Save Complete",
                f"Successfully saved {success_count} file(s)"
            )
            self.showStatusMessage(f"Saved {success_count} files")
        else:
            QMessageBox.warning(
                self,
                "Save Incomplete",
                f"Saved {success_count}/{total_count} files. Some saves failed."
            )
            self.showStatusMessage(f"Saved {success_count}/{total_count} files")
        
        self.update_action_states()
    
    @pyqtSlot()
    def on_undo_clicked(self):
        """Handle undo button."""
        if self.controller.undo():
            self.update_action_states()
    
    @pyqtSlot()
    def on_redo_clicked(self):
        """Handle redo button."""
        if self.controller.redo():
            self.update_action_states()

    @pyqtSlot()
    def on_view_logs(self):
        if self.log_handler:
            dialog = LogViewerDialog(self.log_handler, self)
            dialog.show()
    
    @pyqtSlot()
    def on_view_settings(self):
        dialog = SettingsDialog(self.config, self)
        dialog.exec()

    @pyqtSlot()
    def on_normalize_genres(self):
        from src.genre_search.genre_normalize_window import GenreNormalizationDialog

        dialog = GenreNormalizationDialog(self.controller, self)
        dialog.exec()
    
    def on_data_changed(self, affected_ids):
        """Called when simfile data changes."""
        self.update_action_states()
    
    def update_action_states(self):
        """Update enabled state and tooltips of actions."""
        # Undo/redo
        can_undo = self.controller.can_undo()
        can_redo = self.controller.can_redo()
        
        self.undo_action.setEnabled(can_undo)
        self.redo_action.setEnabled(can_redo)
        
        if can_undo:
            undo_text = self.controller.get_undo_text()
            self.undo_action.setStatusTip(f"Undo: {undo_text}")
        else:
            self.undo_action.setStatusTip("Nothing to undo")
        
        if can_redo:
            redo_text = self.controller.get_redo_text()
            self.redo_action.setStatusTip(f"Redo: {redo_text}")
        else:
            self.redo_action.setStatusTip("Nothing to redo")
        
        # Save
        has_changes = self.controller.has_unsaved_changes()
        self.save_action.setEnabled(has_changes)
        
        if has_changes:
            count = len(self.controller.get_modified_simfiles())
            self.save_action.setStatusTip(f"Save {count} file(s) with unsaved changes")
        else:
            self.save_action.setStatusTip("No unsaved changes")
    
    def closeEvent(self, event):
        """Handle window close."""
        # Cancel any active loading
        if self.loader_thread and self.loader_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Loading in Progress",
                "Simfiles are still loading. Cancel and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.loader_thread.cancel()
                self.loader_thread.wait()
            else:
                event.ignore()
                return
        
        # Check for unsaved changes
        if self.controller.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Exit anyway?",
                QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            
            if reply != QMessageBox.StandardButton.Discard:
                event.ignore()
                return
        
        # perform final teardown

        self.teardown_logging()
        event.accept()

    def resizeEvent(self, event: QResizeEvent | None):

        self.config.set(ConfigEnum.WINDOW_SIZE, (self.geometry().width(), self.geometry().height()))
        super().resizeEvent(event)

    def moveEvent(self, event: QMoveEvent | None):
        self.config.set(ConfigEnum.WINDOW_POSITION, ( self.geometry().top(), self.geometry().left()))
        super().moveEvent(event)

    def showStatusMessage(self, msg):
        logger.info(msg)
        self.status_bar.showMessage(msg)

    # find toolbar methods
    @pyqtSlot()
    def on_show_find(self):
        """Show the find toolbar."""
        self.tree_view.show_find()
