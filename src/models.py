"""
Core data models for simfile editing
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

from src.field_registry import FieldType, FieldRegistry

@dataclass
class SimfileChange:
    """Represents a single change to a simfile field."""
    simfile_id: str
    field_name: str
    old_value: Any
    new_value: Any
    field_type: FieldType = FieldType.TEXT
    
    def invert(self) -> 'SimfileChange':
        """Create the inverse of this change for undo functionality."""
        return SimfileChange(
            simfile_id=self.simfile_id,
            field_name=self.field_name,
            old_value=self.new_value,
            new_value=self.old_value,
            field_type=self.field_type
        )


@dataclass
class SimfileMetadata:
    """
    Represents the current state of a simfile with all editable fields.
    This is our working copy that tracks modifications.
    """
    
    id: str
    pack_name: str
    file_path: Path
    
    # Editable text fields
    title: str = ""
    subtitle: str = ""
    artist: str = ""
    titletranslit: str = ""
    subtitletranslit: str = ""
    artisttranslit: str = ""
    genre: str = ""
    credit: str = ""
    origin: str = ""
    version: str = ""
    
    # Image paths
    banner: Optional[str] = None
    background: Optional[str] = None
    cdtitle: Optional[str] = None
    jacket: Optional[str] = None
    
    # song, sample info
    music: Optional[str] = None # audio filepath
    samplestart: Optional[str] = None
    samplelength: Optional[str] = None

    # Read-only calculated fields
    num_charts: int = 0
    file_type: str = ""
    
    # Internal tracking
    _modified: bool = field(default=False, repr=False)
    _original_data: dict = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        """Store original values for change detection."""
        if not self._original_data:
            # Use field registry to get all editable fields
            self._original_data = {
                field_name: getattr(self, field_name)
                for field_name in FieldRegistry.get_internal_names()
            }
    
    def is_modified(self) -> bool:
        """Check if any field has been modified from original."""
        return self._modified
    
    def mark_modified(self):
        """Mark this simfile as having unsaved changes."""
        self._modified = True
    
    def get_original_value(self, field_name: str) -> Any:
        """Get the original value of a field before any edits."""
        return self._original_data.get(field_name)
    
    def reset_to_original(self):
        """Revert all fields to their original values."""
        for field_name, original_value in self._original_data.items():
            setattr(self, field_name, original_value)
        self._modified = False
    
    def get_file_format(self) -> str:
        """Get the file format extension (.sm, .ssc, etc)."""
        return self.file_path.suffix.lower().lstrip('.')
    
    def is_field_editable(self, field_name: str) -> bool:
        """Check if a field is editable for this simfile's format."""
        return FieldRegistry.is_field_editable(field_name, str(self.file_path))


@dataclass
class PackInfo:
    """Represents a pack (folder) containing multiple simfiles."""
    name: str
    path: Path
    simfile_ids: list[str] = field(default_factory=list)
    
    def add_simfile(self, simfile_id: str):
        """Add a simfile to this pack."""
        if simfile_id not in self.simfile_ids:
            self.simfile_ids.append(simfile_id)
    
    def remove_simfile(self, simfile_id: str):
        """Remove a simfile from this pack."""
        if simfile_id in self.simfile_ids:
            self.simfile_ids.remove(simfile_id)