import os
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QFileDialog, QVBoxLayout
from src.field_registry import FieldDefinition, FieldType
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent

class FileDropWidget(QWidget):

    FILE_FORMATS: dict[FieldType, list[str]] = {
        FieldType.IMAGE: [".jpg", ".jpeg", ".png", ".bmp"],
        FieldType.VIDEO: [".mp4", ".mpg", ".avi"],
        FieldType.AUDIO: [".mp3", ".ogg"]
    }
    

    fileSelected = pyqtSignal(str) # filepath

    def __init__(self, field: FieldDefinition, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_name = field.display_name
        self.internal_name = field.internal_name
        self.field_type = field.field_type;
        self.content_widget = None
        self.starting_dir = str(Path.home())
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def set_starting_dir(self, starting_dir: str|None):
        if starting_dir is None:
            self.starting_dir = str(Path.home())
        else:
            self.starting_dir = starting_dir;

    def set_content(self, widget: QWidget):
        layout = self.layout()
        if layout is None:
            return
        
        if self.content_widget is not None:
            layout.removeWidget(self.content_widget)
        self.content_widget = widget
        layout.addWidget(widget)

    def _show_file_picker(self):
        if not self.isEnabled():
            return
            
        file_filter = self._build_file_filter()        
        
        filepath, ok = QFileDialog.getOpenFileName(self, caption=f"Select {self.display_name}", directory=self.starting_dir, filter=file_filter)

        if filepath:
            self.fileSelected.emit(filepath)

    # click handler

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if not ev:
            return
        ev.accept()
        self._show_file_picker()
        
        
    # file drag-and-drop

    def dragEnterEvent(self, event: QDragEnterEvent | None):
        
        if not event:
            return
        mimeData = event.mimeData()
        if mimeData and mimeData.hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent | None) -> None:
        if not event:
            return
        mimeData = event.mimeData()
        if mimeData and mimeData.hasUrls():
            for url in mimeData.urls():
                if not url.isLocalFile():
                    continue
                local_filepath = url.toLocalFile()
                if self._accepts_filetype(local_filepath):
                    self.fileSelected.emit(local_filepath)
                    event.accept()
                return
        event.ignore()
    
    def _accepts_filetype(self, filepath: str):

        ext = os.path.splitext(filepath)[1]
        accepted_filetypes = self._get_filetypes()
        return ext.lower() in accepted_filetypes
    
    
    def _get_filetypes(self):
        if self.field_type in self.FILE_FORMATS:
            return self.FILE_FORMATS[self.field_type]
        elif self.field_type == FieldType.IMAGEORVIDEO:
            return self.FILE_FORMATS[FieldType.IMAGE] + self.FILE_FORMATS[FieldType.VIDEO]
        else:
            return []
    
    def _build_file_filter(self):

        file_filter = []
        file_filter.append(f"{self.field_type.displayName} ({self._exts_to_filter(self._get_filetypes())})")
        filter_str = ";;".join(file_filter)
        return filter_str

    def _exts_to_filter(self, exts: list[str]):
        filter_str = " ".join([f"*{e}" for e in exts])
        return filter_str
