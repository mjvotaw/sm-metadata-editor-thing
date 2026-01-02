"""
Main controller for simfile editing operations.
This is the primary interface between the GUI and the business logic.
"""

from typing import Any, Dict, List, Optional, Set, Callable
from pathlib import Path
from collections import defaultdict

from src.models import SimfileMetadata, PackInfo, SimfileChange
from src.field_registry import FieldType, FieldRegistry
from src.change_manager import ChangeManager, ChangeCommand
from src.simfile_loader import SimfileLoader


class SimfileController:
    """
    Central controller for managing simfile data and operations.
    
    It manages the in-memory state of all loaded simfiles and coordinates
    changes, undo/redo, and persistence.
    """
    
    def __init__(self):
        # Core data storage
        self._simfiles: Dict[str, SimfileMetadata] = {}
        self._packs: Dict[str, PackInfo] = {}
        
        # Keep references to parsed simfile objects for saving later
        self._parsed_simfiles: Dict[str, Any] = {}  # simfile_id -> Simfile object
        
        self._change_manager = ChangeManager()
        
        # Selection state (useful for bulk operations)
        self._selected_ids: Set[str] = set()
        
        # Callbacks for GUI updates
        self._change_callbacks: List[Callable] = []
        self._selection_callbacks: List[Callable] = []
    
    # ==================== Loading and Initialization ====================
    
    def load_from_directory(self, directory: Path) -> int:
        """
        Load all simfiles from a directory structure.
        Returns the number of simfiles loaded.
        """
        if not directory.exists() or not directory.is_dir():
            return 0
        
        # Find all simfiles
        simfile_paths = SimfileLoader.find_simfiles_in_directory(directory)
        
        loaded_count = 0
        for file_path, pack_name in simfile_paths:
            if self._load_from_file_path(file_path, pack_name):
                loaded_count += 1
        
        return loaded_count
    
    def _load_from_file_path(self, file_path: Path, pack_name: str):
        parsed_simfile = SimfileLoader.load_simfile(file_path)
        if not parsed_simfile:
            return False
        
        # Convert to our metadata model
        metadata = SimfileLoader.simfile_to_metadata(
            parsed_simfile, file_path, pack_name
        )
        
        # Store both metadata and parsed simfile
        simfile_id = metadata.id
        self._simfiles[simfile_id] = metadata
        self._parsed_simfiles[simfile_id] = parsed_simfile

        # Add to pack
        if pack_name not in self._packs:
            # Determine pack path (parent of song directory)
            pack_path = file_path.parent.parent
            self._packs[pack_name] = PackInfo(name=pack_name, path=pack_path)
        
        self._packs[pack_name].add_simfile(simfile_id)
        return True
        
    # ==================== Data Access ====================
    
    def get_simfile(self, simfile_id: str) -> Optional[SimfileMetadata]:
        """Get a simfile by its ID."""
        return self._simfiles.get(simfile_id)
    
    def get_all_simfiles(self) -> List[SimfileMetadata]:
        """Get all loaded simfiles."""
        return list(self._simfiles.values())
    
    def get_simfiles_in_pack(self, pack_name: str) -> List[SimfileMetadata]:
        """Get all simfiles in a specific pack."""
        pack = self._packs.get(pack_name)
        if not pack:
            return []
        return [self._simfiles[sid] for sid in pack.simfile_ids if sid in self._simfiles]
    
    def get_all_packs(self) -> List[PackInfo]:
        """Get all packs."""
        return list(self._packs.values())
    
    def get_modified_simfiles(self) -> List[SimfileMetadata]:
        """Get all simfiles that have unsaved changes."""
        return [sf for sf in self._simfiles.values() if sf.is_modified()]
    
    # ==================== Editing Operations ====================
    
    def set_field(self, simfile_id: str, field_name: str, new_value: Any) -> bool:
        """
        Set a field value for a single simfile.
        Returns True if successful, False otherwise.
        """
        return self.set_field_bulk([simfile_id], field_name, new_value)
    
    def set_field_bulk(self, simfile_ids: List[str], field_name: str, new_value: Any) -> bool:
        """
        Set a field value for multiple simfiles at once.
        This creates a single undo/redo command for the entire operation.
        Returns True if successful, False otherwise.
        
        Note: Only simfiles that support this field (based on format) will be updated.
        """
        # Check if field exists
        field_def = FieldRegistry.get_field(field_name)
        if not field_def:
            return False
        
        changes = []
        
        for simfile_id in simfile_ids:
            simfile = self._simfiles.get(simfile_id)
            if not simfile:
                continue
            
            # Check if this field is supported for this simfile's format
            if not simfile.is_field_editable(field_name):
                continue
            
            old_value = getattr(simfile, field_name)
            if old_value == new_value:
                continue
            
            change = SimfileChange(
                simfile_id=simfile_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                field_type=field_def.field_type
            )
            changes.append(change)
        
        if not changes:
            return False
        
        self._apply_changes(changes)
        
        num_files = len(simfile_ids)
        description = f"Edit {field_def.display_name} for {num_files} file{'s' if num_files > 1 else ''}"
        command = ChangeCommand(description=description, changes=changes)
        self._change_manager.add_command(command)
        
        self._notify_changes(simfile_ids)
        
        return True
    
    def _apply_changes(self, changes: List[SimfileChange]):
        """Apply a list of changes to the simfiles."""
        for change in changes:
            simfile = self._simfiles.get(change.simfile_id)
            if simfile:
                setattr(simfile, change.field_name, change.new_value)
                simfile.mark_modified()
    
    # ==================== Undo/Redo ====================
    
    def undo(self) -> bool:
        """Undo the last change. Returns True if successful."""
        command = self._change_manager.undo()
        if not command:
            return False
        self._apply_change_command(command)
        return True
    
    def redo(self) -> bool:
        """Redo the last undone change. Returns True if successful."""
        command = self._change_manager.redo()
        if not command:
            return False
        self._apply_change_command(command)
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._change_manager.can_undo()
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._change_manager.can_redo()
    
    def get_undo_text(self) -> Optional[str]:
        """Get description of next undoable action."""
        return self._change_manager.get_undo_description()
    
    def get_redo_text(self) -> Optional[str]:
        """Get description of next redoable action."""
        return self._change_manager.get_redo_description()
    
    def _apply_change_command(self, command: ChangeCommand):
        self._apply_changes(command.changes)
        affected_ids = [c.simfile_id for c in command.changes]
        self._notify_changes(affected_ids)
    
    # ==================== Selection Management ====================
    
    def set_selection(self, simfile_ids: Set[str]):
        """Set the current selection."""
        self._selected_ids = simfile_ids.copy()
        self._notify_selection()
    
    def get_selection(self) -> Set[str]:
        """Get the current selection."""
        return self._selected_ids.copy()
    
    def get_selected_simfiles(self) -> List[SimfileMetadata]:
        """Get SimfileMetadata objects for all selected simfiles."""
        return [self._simfiles[sid] for sid in self._selected_ids if sid in self._simfiles]
    
    # ==================== Persistence ====================
    
    def save_changes(self) -> Dict[str, bool]:
        """
        Save all modified simfiles to disk.
        Returns a dict mapping simfile_id to success status.
        """
        results = {}
        modified = self.get_modified_simfiles()
        
        for simfile in modified:
            try:
                parsed_simfile = self._parsed_simfiles.get(simfile.id)
                if not parsed_simfile:
                    results[simfile.id] = False
                    continue
                
                success = SimfileLoader.save_simfile(simfile, parsed_simfile)
                results[simfile.id] = success
                
                if success:
                    # Reset modification state
                    simfile._modified = False
                    # Update original values to current values
                    simfile._original_data = {
                        field: getattr(simfile, field)
                        for field in FieldRegistry.get_internal_names()
                    }
            except Exception as e:
                print(f"Error saving {simfile.file_path}: {e}")
                results[simfile.id] = False
        
        # Clear undo/redo history after successful save
        if all(results.values()):
            self._change_manager.clear()
        
        return results
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are any unsaved changes."""
        return any(sf.is_modified() for sf in self._simfiles.values())
    
    def revert_all_changes(self):
        """Revert all simfiles to their original state (lose all changes)."""
        for simfile in self._simfiles.values():
            simfile.reset_to_original()
        
        self._change_manager.clear()
        self._notify_changes(list(self._simfiles.keys()))
    
    # ==================== Observer Pattern for GUI Updates ====================
    
    def register_change_callback(self, callback: Callable[[List[str]], None]):
        """
        Register a callback to be notified when simfiles change.
        Callback receives a list of affected simfile IDs.
        """
        self._change_callbacks.append(callback)
    
    def register_selection_callback(self, callback: Callable[[], None]):
        """Register a callback to be notified when selection changes."""
        self._selection_callbacks.append(callback)
    
    def _notify_changes(self, affected_ids: List[str]):
        """Notify all registered callbacks about changes."""
        for callback in self._change_callbacks:
            callback(affected_ids)
    
    def _notify_selection(self):
        """Notify all registered callbacks about selection changes."""
        for callback in self._selection_callbacks:
            callback()