from typing import Any, Dict, Optional
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QTextEdit, QLineEdit, QComboBox, QCheckBox, QScrollArea, QSpinBox, QWidget, QDialogButtonBox
)

from src.utils.config_manager import ConfigManager, ConfigEnum

class SettingsDialog(QDialog):

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.fields: dict[str, QWidget] = {}
        self.setWindowTitle("Application Settings")

        self.setup_ui()
    

    def setup_ui(self):  

        main_layout = QVBoxLayout(self)

        
        scroll_area = self._create_scroll_area()
        form_widget, form_layout = self._create_form()

        self._create_form_fields(form_layout)

        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area, 1)


        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _create_scroll_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        return scroll

    def _create_form(self):
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        return form_widget, form_layout

    def _create_form_fields(self, form_layout: QFormLayout):
        
        log_level_field = QComboBox()
        log_level_field.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        form_layout.addRow("Log Level", log_level_field)

        self.fields[ConfigEnum.LOG_LEVEL] = log_level_field

        lastfm_api_key_field = QLineEdit()
        form_layout.addRow("Last.fm API key", lastfm_api_key_field)
        self.fields[ConfigEnum.LASTFM_API_KEY] = lastfm_api_key_field

        discogs_api_key_field = QLineEdit()
        form_layout.addRow("Discogs API key", discogs_api_key_field)
        self.fields[ConfigEnum.DISCOGS_API_KEY] = discogs_api_key_field
        
        self.set_values(self.config.get_values())

    def get_values(self) -> Dict[str, Any]:
        """
        Get all form values as a dictionary.
        
        Returns:
            Dictionary mapping field names to their current values
        """
        values = {}
        
        for name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QTextEdit):
                values[name] = widget.toPlainText()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QComboBox):
                values[name] = widget.currentText()
        
        return values
    
    def set_values(self, values: Dict[str, Any]):
        """
        Set form values from a dictionary.
        
        Args:
            values: Dictionary mapping field names to values
        """
        for name, value in values.items():
            if name not in self.fields:
                continue
            
            widget = self.fields[name]
            
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(str(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)

    @pyqtSlot()
    def accept(self) -> None:

        config_values: dict[str, Any] = self.get_values()

        self.config.bulk_update(config_values)

        return super().accept()