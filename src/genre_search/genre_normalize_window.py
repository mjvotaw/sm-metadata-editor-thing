from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QProgressBar, QComboBox,
    QGroupBox, QCheckBox, QLabel, QHeaderView, QMessageBox,
    QStyleFactory
)

from fuzzytrackmatch import GenreTag

from src.controller import SimfileController
from src.utils.config_manager import ConfigManager, ConfigEnum
from .genre_search_thread import GenreSearchThread
from src.ignore_wheel_filter import IgnoreWheelFilter

class GenreNormalizationDialog(QDialog):

    def __init__(self, controller: SimfileController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config = ConfigManager()
        self.simfiles = controller.get_selected_simfiles()
        self.simfiles = sorted(self.simfiles, key=lambda s: s.title.lower())
        self.setWindowTitle("Search/Normalize Genres")
        self.resize(800, 600)
        
        self.ignore_wheel_filter = IgnoreWheelFilter(self)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Options section at top
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        
        # Table showing simfiles and genre changes
        self.table = self._create_simfile_table()
        layout.addWidget(self.table, 1)  # Stretch factor for table
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyle(QStyleFactory.create('Fusion'))


        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons at bottom
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_options_group(self):
        group = QGroupBox("Search Options")
        layout = QVBoxLayout()
        
        self.replace_existing_checkbox = QCheckBox(
            "Replace existing genre values"
        )
        self.replace_existing_checkbox.setToolTip(
            "If unchecked, only simfiles with empty/missing genres will be updated"
        )
        self.replace_existing_checkbox.setChecked(True)
        layout.addWidget(self.replace_existing_checkbox)
        
        
        source_label = QLabel("Search sources:")
        layout.addWidget(source_label)
        
        self.search_options = self._setup_search_api_options()
        for k, option in self.search_options.items():
            layout.addWidget(option)
        
        group.setLayout(layout)
        return group
    
    def _setup_search_api_options(self):
        search_options: dict[str, QCheckBox] = {}

        lastfm_checkbox = QCheckBox("Last.fm")
        has_lastfm_key = self.config.get(ConfigEnum.LASTFM_API_KEY, "") != ""
        lastfm_checkbox.setEnabled(has_lastfm_key)
        lastfm_checkbox.setChecked(has_lastfm_key)
        if has_lastfm_key == False:
            lastfm_checkbox.setText("Last.fm (api key required)")
        search_options["lastfm"] = lastfm_checkbox

        discogs_checkbox = QCheckBox("Discogs")
        has_discogs_key = self.config.get(ConfigEnum.DISCOGS_API_KEY, "") != ""
        discogs_checkbox.setEnabled(has_discogs_key)
        discogs_checkbox.setChecked(has_discogs_key)
        if has_discogs_key == False:
            discogs_checkbox.setText("Discogs (api key required)")
        search_options["discogs"] = discogs_checkbox

        animethemes_checkbox = QCheckBox("animethemes.moe")
        animethemes_checkbox.setChecked(True)
        search_options["animethemes"] = animethemes_checkbox

        return search_options

    def _create_simfile_table(self):
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            "Title", "Artist", "Current Genre", "New Genre"
        ])
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        # table.setSortingEnabled(True)
        
        # Populate with simfiles
        table.setRowCount(len(self.simfiles))
        for row, simfile in enumerate(self.simfiles):
            # Title
            table.setItem(row, 0, QTableWidgetItem(simfile.title))
            
            # Artist
            table.setItem(row, 1, QTableWidgetItem(simfile.artist))
            
            # Current genre
            current_genre = simfile.genre or "(empty)"
            table.setItem(row, 2, QTableWidgetItem(current_genre))
            
            # New genre - this will be a dropdown
            genre_combo = QComboBox()
            genre_combo.installEventFilter(self.ignore_wheel_filter)
            genre_combo.addItem("(searching...)")
            genre_combo.setEnabled(False)
            table.setCellWidget(row, 3, genre_combo)
        
        # Resize columns
        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        
        return table
    
    def _create_button_layout(self):
        layout = QHBoxLayout()
        layout.addStretch()
        
        self.search_button = QPushButton("Search for Genres")
        self.search_button.clicked.connect(self.on_search_clicked)
        layout.addWidget(self.search_button)
        
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self.on_apply_clicked)
        self.apply_button.setEnabled(False)  # Disabled until search completes
        layout.addWidget(self.apply_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel)
        layout.addWidget(self.cancel_button)
        
        return layout
    
    @pyqtSlot()
    def on_cancel(self):
        self.search_thread.cancel()
        self.reject()
    # Genre Search

    @pyqtSlot()
    def on_search_clicked(self):
        """Handle search button click."""
        # Disable controls during search
        self.search_button.setEnabled(False)
        self.replace_existing_checkbox.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Determine which sources to use
        sources = []
        for k, opt in self.search_options.items():
            if opt.isChecked():
                sources.append(k)
        
        # Create and start search thread
        self.search_thread = GenreSearchThread(self.simfiles, sources)
        self.search_thread.progress_update.connect(self.on_search_progress)
        self.search_thread.genres_found.connect(self.on_genre_found)
        self.search_thread.no_genre_found.connect(self.on_no_genre_found)
        self.search_thread.search_complete.connect(self.on_search_complete)
        self.search_thread.start()

    def on_search_progress(self, current: int, total: int, title: str):
        """Update progress bar."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"Searching: {title} ({current}/{total})")

    def on_genre_found(self, row: int, genres: list[list[GenreTag]]):
        """Update table when genres are found for a row."""

        initial_selection = self._get_initial_genres_selection(genres)
        self.update_genre_options_for_row(row, genres, initial_selection)
    
    def on_no_genre_found(self, row: int):
        self.show_no_results_for_row(row)

    def on_search_complete(self):
        """Handle search completion."""
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)
        self.replace_existing_checkbox.setEnabled(True)
        self.apply_button.setEnabled(True)  # Now allow applying changes

    def _get_initial_genres_selection(self, genres: list[list[GenreTag]]) -> GenreTag|None:
        # find the most specific genre with the highest score
        best_genre = None
        best_score = 0
        best_depth = 0
        for group in genres:
            group_reversed = group.copy()
            group_reversed.reverse()
            depth = 0
            for genre in group_reversed:
                # nobody wants "Dance" as a genre, that's basically useless
                if genre.name == "Dance":
                    continue
                depth += 1
                if genre.score > best_score or (genre.score == best_score and depth >= best_depth):
                    best_score = genre.score
                    best_genre = genre
                    best_depth = depth
        
        return best_genre
    # 
    @pyqtSlot()
    def on_apply_clicked(self):
        """Apply selected genre changes to simfiles."""
        changes_to_apply = []
        
        for row in range(self.table.rowCount()):
            genre_combo = self.table.cellWidget(row, 3)
            if not isinstance(genre_combo, QComboBox):
                continue
            
            selected_genre = genre_combo.currentData(Qt.ItemDataRole.UserRole)
            
            # Skip if no change or special values
            if selected_genre is None:
                continue
            
            current_genre = self.simfiles[row].genre or ""
            
            # Check replace_existing option
            if not self.replace_existing_checkbox.isChecked() and current_genre:
                continue
            
            if selected_genre != current_genre:
                changes_to_apply.append((self.simfiles[row].id, selected_genre))
        
        if not changes_to_apply:
            QMessageBox.information(self, "No Changes", "No genre changes to apply")
            return
        
        # Apply via controller
        for simfile_id, new_genre in changes_to_apply:
            self.controller.set_field(simfile_id, 'genre', new_genre)
        
        # Close dialog
        self.accept()

    def update_genre_options_for_row(self, row: int, possible_genres: list[list[GenreTag]], initial_selection: GenreTag|None):
        """
        Update the dropdown for a specific row with search results.
        
        Args:
            row: The table row index
            possible_genres: List of genre options found from search
        """
        genre_combo = self.table.cellWidget(row, 3)
        if not isinstance(genre_combo, QComboBox):
            return
        
        genre_combo.clear()
        genre_combo.setEnabled(True)
        
        if not possible_genres:
            genre_combo.addItem("(no results found)", userData=None)
            genre_combo.setEnabled(False)
            return
        

        tree = self.build_genre_tree(possible_genres)
        items = self.flatten_tree_for_display(tree)
        idx = 0
        for display_text, actual_value, depth in items:
            genre_combo.addItem(display_text, userData=actual_value)
            if initial_selection is not None and initial_selection.name == actual_value:
                
                genre_combo.setCurrentIndex(idx)
            idx = idx + 1
        
        current_genre = self.simfiles[row].genre
        if current_genre:
            genre_combo.addItem(f"(keep: {current_genre})", userData=None)

    def show_no_results_for_row(self, row: int):
        genre_combo = self.table.cellWidget(row, 3)
        if not isinstance(genre_combo, QComboBox):
            return
        genre_combo.clear()
        genre_combo.setEnabled(False)
        genre_combo.addItem("(no results found)")

    
    def build_genre_tree(self, genre_paths: list[list[GenreTag]]) -> dict:
        """Build tree structure from genre paths."""
        tree = {}
        for path in genre_paths:
            current_level = tree
            path.reverse()
            for genre in path:
                if genre.name not in current_level:
                    current_level[genre.name] = {}
                current_level = current_level[genre.name]
        return tree

    def flatten_tree_for_display(self, tree: dict, depth: int = 0) -> list[tuple[str, str, int]]:
        """Flatten tree into (display_text, actual_value, depth) tuples."""
        items = []
        for genre, subtree in tree.items():
            if depth == 0:
                display_text = genre
            else:
                indent = "  " * (depth - 1)
                display_text = f"{indent} ├ {genre}"
            
            items.append((display_text, genre, depth))
            
            if subtree:
                items.extend(self.flatten_tree_for_display(subtree, depth + 1))
        
        return items