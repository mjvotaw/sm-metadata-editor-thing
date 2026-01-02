import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget
from src.field_registry import FieldDefinition

class BaseFieldWidget(QWidget):

    valueChanged = pyqtSignal(str, str) # field_name, value

    def __init__(self, field: FieldDefinition, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.internal_name = field.internal_name
        self.display_name = field.display_name
        self.placeholder = field.placeholder or ""
        self.description = field.description or ""

        self.setup_ui(field)
        self.set_value(field.default_value or "")
        
    def setup_ui(self, field: FieldDefinition):
        pass

    def set_value(self, value: str, **kwargs):
        pass

    def set_placeholder(self, placeholder: str):
        pass


    def clear(self):
        pass
