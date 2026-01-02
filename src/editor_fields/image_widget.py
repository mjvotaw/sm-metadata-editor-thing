from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
class ImageWidget(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)

    def load_image(self, filepath: str) -> bool:
        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            return False
        self.setPixmap(pixmap)
        return True
    
    def pixmap_dimensions(self):
        if self.pixmap():
            return (self.pixmap().width(), self.pixmap().height())
        return (None, None)

    def hasHeightForWidth(self):
        return self.pixmap() is not None and self.pixmap().width() > 0

    def heightForWidth(self, w):
        if self.pixmap() and self.pixmap().width() != 0:
            return int(w * (self.pixmap().height() / self.pixmap().width()))
        else:
            return 0
        
