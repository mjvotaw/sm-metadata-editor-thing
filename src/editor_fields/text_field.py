from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy, QLineEdit
from .base_field_widget import BaseFieldWidget
from src.field_registry import FieldDefinition
class TextFieldWidget(BaseFieldWidget):

    def __init__(self, field: FieldDefinition, *args, **kwargs) -> None:
        super().__init__(field, *args, **kwargs)

    
    def setup_ui(self, field_def: FieldDefinition):
        label = QLabel(field_def.display_name + ":")
        if field_def.description:
            label.setToolTip(field_def.description)
        
        widget = QLineEdit()
        if field_def.placeholder:
            widget.setPlaceholderText(field_def.placeholder)
        if field_def.description:
            widget.setToolTip(field_def.description)

        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        widget.textEdited.connect(
            lambda text, fname=field_def.internal_name: self.valueChanged.emit(fname, text)
        )

        self.text_field_widget = widget
        self.text_field_label = label
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(widget)
        self.setLayout(layout)

    def set_value(self, value: str):
        self.text_field_widget.setText(value)

    def set_placeholder(self, placeholder: str):
        self.text_field_widget.setPlaceholderText(placeholder)

    def setEnabled(self, is_enabled: bool) -> None:
        font = self.text_field_label.font()
        font.setItalic(not is_enabled)
        self.text_field_label.setFont(font)
        self.text_field_widget.setEnabled(is_enabled)
        self.text_field_label.setEnabled(is_enabled)
        return super().setEnabled(is_enabled)
        
        
        

