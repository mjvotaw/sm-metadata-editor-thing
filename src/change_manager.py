from typing import List, Optional
from dataclasses import dataclass
from src.models import SimfileChange


@dataclass
class ChangeCommand:
    description: str
    changes: List[SimfileChange]
    
    def invert(self) -> 'ChangeCommand':
        """Create the inverse command for undo."""
        return ChangeCommand(
            description=f"Undo: {self.description}",
            changes=[change.invert() for change in reversed(self.changes)]
        )


class ChangeManager:
    """
    Manages the history of changes for undo/redo functionality.
    """
    
    def __init__(self, max_history: int = 100):
        self._undo_stack: List[ChangeCommand] = []
        self._redo_stack: List[ChangeCommand] = []
        self._max_history = max_history
    
    def add_command(self, command: ChangeCommand):
        self._undo_stack.append(command)
        self._redo_stack.clear()
        
        # Limit history size
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)
    
    def can_undo(self) -> bool:
        """Check if there are any changes to undo."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if there are any changes to redo."""
        return len(self._redo_stack) > 0
    
    def undo(self) -> Optional[ChangeCommand]:
        """
        Undo the most recent command.
        Returns the inverted command to apply, or None if nothing to undo.
        """
        if not self.can_undo():
            return None
        
        command = self._undo_stack.pop()
        self._redo_stack.append(command)
        return command.invert()
    
    def redo(self) -> Optional[ChangeCommand]:
        """
        Redo the most recently undone command.
        Returns the command to reapply, or None if nothing to redo.
        """
        if not self.can_redo():
            return None
        
        command = self._redo_stack.pop()
        self._undo_stack.append(command)
        return command
    
    def clear(self):
        """Clear all history. Useful after saving changes to disk."""
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of the next undoable action."""
        if self.can_undo():
            return self._undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of the next redoable action."""
        if self.can_redo():
            return self._redo_stack[-1].description
        return None
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are any unsaved changes in the undo stack."""
        return len(self._undo_stack) > 0
