from PyQt6.QtWidgets import (
    QPushButton,
    QStatusBar,
    QProgressBar
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot


class StatusDisplay(QStatusBar):

    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.addPermanentWidget(self.progress_bar)

        self.cancel_load_button = QPushButton("Stop Loading")
        self.cancel_load_button.setVisible(False)
        self.cancel_load_button.setEnabled(False)
        self.cancel_load_button.clicked.connect(self.cancel_requested)
        self.addPermanentWidget(self.cancel_load_button)
    
    @pyqtSlot(int, int, str)
    def show_loading_message(self, current: int, total: int, pack_name: str):
        self.progress_bar.setVisible(True)
        self.cancel_load_button.setVisible(True)
        self.cancel_load_button.setEnabled(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.showMessage(f"Loading pack {current}/{total}: {pack_name}")
    
    def show_loading(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.cancel_load_button.setVisible(True)
        self.cancel_load_button.setEnabled(True)
    def hide_loading(self):
        self.progress_bar.setVisible(False)
        self.cancel_load_button.setVisible(False)
        self.cancel_load_button.setEnabled(False)

