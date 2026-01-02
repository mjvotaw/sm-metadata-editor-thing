import os
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QSizePolicy, QFileDialog, QStackedWidget
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent

from typing import Optional
from .base_field_widget import BaseFieldWidget
from src.field_registry import FieldDefinition, FieldType
from .video_widget import VideoWidget
from .image_widget import ImageWidget
from .file_drop import FileDropWidget

class ImageDisplayWidget(BaseFieldWidget):
    
    VIDEO_FORMATS = [".mp4", ".mpg", ".avi"]

    IDX_PLACEHOLDER = 0
    IDX_IMAGE = 1
    IDX_VIDEO = 2
    def __init__(self, field: FieldDefinition, *args, **kwargs) -> None:
        self.filepath: Optional[str] = None
        self.field_type = field.field_type

        self.is_video = False
        super().__init__(field, *args, **kwargs)
        # self.setAcceptDrops(True)
        self.show_placeholder()


    # BaseFileWidget overrides

    def setup_ui(self, field_def: FieldDefinition):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(field_def.display_name + ":")

        self.file_drop = FileDropWidget(field_def)
        self.file_drop.fileSelected.connect(lambda filepath, field_name=self.internal_name: self.valueChanged.emit(field_name, filepath))
        self.media_container = QStackedWidget()
        self.placeholder_widget = self._setup_placeholder_widget()
        self.image_holder = self._setup_image_holder()
        self.video_widget = self._setup_video_widget()

        self.media_container.addWidget(self.placeholder_widget)
        self.media_container.addWidget(self.image_holder)
        self.media_container.addWidget(self.video_widget)
        
        self.filename_label = QLabel(self)
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        # Dimensions label - fixed size
        self.dimensions_label = QLabel(self)
        self.dimensions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dimensions_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )
        
        layout.addWidget(self.label)

        self.file_drop.set_content(self.media_container)
        layout.addWidget(self.file_drop, 0)
        layout.addWidget(self.filename_label, 0)
        layout.addWidget(self.dimensions_label, 0)
        
        self.setLayout(layout)
    
    def set_value(self, value: str):
        self._display_media(value)
    
    
    def clear(self):
        """Clear the current image and show placeholder."""
        self.show_placeholder()

    def _setup_image_holder(self):
        
        image_holder = ImageWidget(self)
        image_holder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_holder.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        image_holder.setMinimumSize(100, 150)
        image_holder.setMaximumSize(16777215, 16777215)

        return image_holder
    
    def _setup_video_widget(self):
        video_widget = VideoWidget(self)
        video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        video_widget.setMinimumSize(100, 100)
        video_widget.dimensionsChanged.connect(self._show_dimensions)
        return video_widget
    
    def _setup_placeholder_widget(self):
        placeholder_widget = QLabel(self)
        placeholder_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_widget.setText("Drag file to add,\nor click to select")
        placeholder_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        placeholder_widget.setMinimumSize(100, 100)
        placeholder_widget.setMaximumHeight(100)
        placeholder_widget.setStyleSheet("""
            QLabel {
                background-color: #E0E0E0;
                border: 2px dashed #999999;
                border-radius: 8px;
            }
        """)
        return placeholder_widget


    def show_placeholder(self, placeholder: str | None=None):
        """Show a placeholder when no image is loaded."""
        self.filepath = None

        self.media_container.setCurrentIndex(self.IDX_PLACEHOLDER)
        self.image_holder.clear()
        self.video_widget.clear()
        
        placeholder = placeholder or "No image"
        self.filename_label.setText(placeholder)
        self._clear_dimensions()

        self.media_container.adjustSize()
        self.media_container.updateGeometry()
    
    def _display_media(self, filepath: str):
        """Load and display an image from the given filepath."""
        if not filepath:
            self.show_placeholder()
            self.file_drop.set_starting_dir(None)
            return
        
        filepath = str(os.path.abspath(filepath))
        parent_dir = str(Path(filepath).parent)
        filename = str(os.path.basename(filepath))

        self.file_drop.set_starting_dir(parent_dir)

        if not os.path.exists(filepath):
            self.show_placeholder("File not found")
            return
        
        self.filepath = filepath
        self.is_video = self._is_video_file(filepath)
        
        if self.is_video:
            self.media_container.setCurrentIndex(self.IDX_VIDEO)
            self.image_holder.clear()
            if self.video_widget.load_video(filepath):
                self.filename_label.setText(filename)
                self.dimensions_label.setText("loading...")
            else:
                self.show_placeholder("Failed to load video")
            pass
        else:
            self.media_container.setCurrentIndex(self.IDX_IMAGE)
            self.video_widget.clear()
            if self.image_holder.load_image(filepath):
                self.filename_label.setText(filename)
                width, height = self.image_holder.pixmap_dimensions()
                if width is not None and height is not None:
                    self._show_dimensions(width, height)
            else:
                self.show_placeholder("Failed to load image")
                return
    
    @pyqtSlot(int, int)
    def _show_dimensions(self, width:int, height: int):
        self.dimensions_label.setText(f"{width} × {height}")
        self.dimensions_label.setStyleSheet("")

    def _clear_dimensions(self):
        self.dimensions_label.setText("")
        self.dimensions_label.setStyleSheet("color: #666666; font-style: italic;")
    
    def _is_video_file(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.VIDEO_FORMATS
    