from typing import Dict
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QScrollArea)
from PyQt6.QtCore import QTimer

from src.controller import SimfileController
from src.field_registry import FieldDefinition, FieldRegistry, FieldType, FieldGroup
from src.models import SimfileMetadata

from src.editor_fields.base_field_widget import BaseFieldWidget
from src.editor_fields.text_field import TextFieldWidget
from src.editor_fields.image_display import ImageDisplayWidget
from src.editor_fields.audio_preview import AudioPreviewWidget

class SimfileEditorPanel(QWidget):
    
    DEBOUNCE_DELAY = 350
    
    def __init__(self, controller: SimfileController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.current_selection = set()
        self.updating_from_selection = False
        

        self.field_widgets: Dict[str, BaseFieldWidget] = {}
        self.debounce_timers: Dict[str, QTimer] = {}
        # Track pending changes: map field name to new value
        self.pending_changes: Dict[str, str] = {}
        
        self.setup_ui()
        self.controller.register_selection_callback(self.on_selection_changed)
        self.controller.register_change_callback(self.on_data_changed)
        self.clear_fields()
    
    def setup_ui(self):
        """Build the UI dynamically from the field registry."""
        layout = QVBoxLayout()
        
        scroll, scroll_layout = self._create_scroll_area()
        
        for field_group in FieldRegistry.FIELD_GROUPS:
            group_box = self._create_field_group(field_group)
            scroll_layout.addWidget(group_box)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def _create_scroll_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        return scroll, scroll_layout


    def _create_field_group(self, field_group: FieldGroup):
        group_box = QGroupBox(field_group.display_name)
        group_layout = QVBoxLayout()
        group_layout.setSpacing(0)

        for field_def in field_group.fields:
            widget = self._setup_field(field_def)
            group_layout.addWidget(widget)
        
        group_box.setLayout(group_layout)
        return group_box

    
    def _setup_field(self, field_def: FieldDefinition):

        if field_def.field_type == FieldType.TEXT:
            widget = TextFieldWidget(field_def)
        elif field_def.field_type == FieldType.NUMERIC:
            widget = TextFieldWidget(field_def)
        elif field_def.field_type == FieldType.IMAGE or field_def.field_type == FieldType.IMAGEORVIDEO:
            widget = ImageDisplayWidget(field_def)
        elif field_def.field_type == FieldType.SONGPREVIEW:
            widget = AudioPreviewWidget(field_def)
        
        widget.valueChanged.connect(
            lambda field_name, value, : self._on_field_edited(field_name, value)
        )
            
        self._setup_debounce_timer(field_def.internal_name)
        self.field_widgets[field_def.internal_name] = widget
        return widget
    
    def _setup_debounce_timer(self, field_name: str):
        """Create and configure a debounce timer for a field."""
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._apply_debounced_change(field_name))
        self.debounce_timers[field_name] = timer
    
    def _on_field_edited(self, field_name: str, new_value: str):
        """
        Handle user editing a field (called on every keystroke).
        This starts/restarts the debounce timer instead of immediately applying.
        """
        if self.updating_from_selection:
            return
        
        if not self.current_selection:
            return
        
        # Store the pending change
        self.pending_changes[field_name] = new_value
        
        # Restart the debounce timer
        timer = self.debounce_timers.get(field_name)
        if timer:
            timer.stop()
            timer.start(self.DEBOUNCE_DELAY)
    
    def _apply_debounced_change(self, field_name: str):
        """
        Apply the pending change after the debounce delay has elapsed.
        This creates a single ChangeCommand for the edit session.
        """
        if field_name not in self.pending_changes:
            return
        
        new_value = self.pending_changes.pop(field_name)

        self.controller.set_field_bulk(
            list(self.current_selection),
            field_name,
            new_value
        )
    
    def _flush_pending_changes(self):
        """
        Immediately apply all pending changes.
        """
        for field_name, timer in self.debounce_timers.items():
            if timer.isActive():
                timer.stop()
                if field_name in self.pending_changes:
                    self._apply_debounced_change(field_name)
    
    def on_selection_changed(self):
        """Called when the selection changes."""
        self._flush_pending_changes()
        
        selected = self.controller.get_selected_simfiles()
        self.current_selection = {s.id for s in selected}
        
        if len(selected) == 0:
            self.clear_fields()
        elif len(selected) == 1:
            self.load_single_simfile(selected[0])
        else:
            self.load_multiple_simfiles(selected)
    
    def on_data_changed(self, affected_ids: list[str]):
        """
        Called when simfile data changes (e.g., from undo/redo).
        Refresh the editor fields if any of the currently selected simfiles were affected.
        """
        # Check if any affected simfiles are in our current selection
        if self.current_selection and any(sid in self.current_selection for sid in affected_ids):
            # Refresh the display without flushing pending changes
            # (since the change came from outside, not from user editing)
            selected = self.controller.get_selected_simfiles()
            
            if len(selected) == 0:
                self.clear_fields()
            elif len(selected) == 1:
                self.load_single_simfile(selected[0])
            else:
                self.load_multiple_simfiles(selected)
    
    def clear_fields(self):
        """Clear all fields and disable editing."""
        self.updating_from_selection = True
        
        for field_name, widget in self.field_widgets.items():
            widget.clear()
            widget.set_placeholder("No selection")
            widget.setEnabled(False)
        
        self.updating_from_selection = False
    
    def load_single_simfile(self, simfile: SimfileMetadata):
        """Load a single simfile's data and enable/disable fields based on format."""
        self.updating_from_selection = True
        
        for field_def in FieldRegistry.get_all_fields():
            field_name = field_def.internal_name
            
            value = getattr(simfile, field_name) or ""
            
            is_supported = simfile.is_field_editable(field_name)
            placeholder = field_def.placeholder or ""
            if not is_supported:
                placeholder = f"Not supported in .{simfile.get_file_format()} files"
            
            if field_def.field_type == FieldType.SONGPREVIEW:
                self._set_audio_field(field_name, value, simfile, is_supported)
            else:
                self._set_field(field_name, value, placeholder, is_supported)

        
        self.updating_from_selection = False
    
    def load_multiple_simfiles(self, simfiles: list[SimfileMetadata]):
        """Load multiple simfiles (bulk edit mode)."""
        self.updating_from_selection = True
                
        for field_def in FieldRegistry.get_all_fields():
            field_name = field_def.internal_name
            
            all_support = all(sf.is_field_editable(field_name) for sf in simfiles)
            
            if all_support:    
                values = set(getattr(s, field_name) or "" for s in simfiles)
                placeholder = field_def.placeholder or ""
                if len(values) == 1:
                    value = list(values)[0]
                    placeholder = field_def.placeholder or ""
                else:
                    value = ""
                    placeholder = f"<{len(simfiles)} files, mixed values>"
                
                self._set_field(field_name, value, placeholder, True)
            else:
                num_incompatible = sum(1 for sf in simfiles if not sf.is_field_editable(field_name))
                placeholder = f"Not supported by {num_incompatible}/{len(simfiles)} files"
                self._set_field(field_name, "", placeholder, False)
        
        self.updating_from_selection = False
    
    def _set_field(self, field_name: str, value: str, placeholder: str, enabled: bool):
        widget = self.field_widgets[field_name]
        
        if enabled:
            widget.set_value(value)
        else:
            widget.clear()

        widget.setEnabled(enabled)
        widget.set_placeholder(placeholder)


    def _set_audio_field(self, field_name: str, audio_path: str, simfile:SimfileMetadata,  enabled: bool):
        sample_start = float(getattr(simfile, 'samplestart', 0))
        sample_length = float(getattr(simfile, 'samplelength', 15))

        widget = self.field_widgets[field_name]
        if widget:
            widget.setEnabled(enabled)
            if enabled:
                widget.set_value(audio_path, sample_start=sample_start, sample_length=sample_length)
            else:
                widget.clear()
    
    def closeEvent(self, event):
        """Handle widget close - flush pending changes."""
        self._flush_pending_changes()
        super().closeEvent(event)