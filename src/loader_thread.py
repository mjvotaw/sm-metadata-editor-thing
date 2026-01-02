from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from src.controller import SimfileController

class LoaderThread(QThread):
    """
    Background thread for loading simfiles asynchronously.
    
    Emits progress signals as packs are loaded.
    """
    # Signals for progress updates
    progress_update = pyqtSignal(int, int, str)  # (current, total, pack_name)
    loading_complete = pyqtSignal(int, int)  # total_simfiles_loaded, failed_count
    pack_loaded = pyqtSignal(str)  # pack_name (for incremental UI updates)
    
    def __init__(self, controller: SimfileController, directory: Path):
        super().__init__()
        self.controller = controller
        self.directory = directory
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation of the loading process."""
        self._cancelled = True
    
    def run(self):
        """Main loading logic - runs in background thread."""
        from src.simfile_loader import SimfileLoader
        from collections import defaultdict
        
        if not self.directory.exists() or not self.directory.is_dir():
            self.loading_complete.emit(0, 0)
            return
        
        # Find all simfiles and group by pack
        all_simfiles = SimfileLoader.find_simfiles_in_directory(self.directory)
        
        # Group by pack name
        packs_dict = defaultdict(list)
        for file_path, pack_name in all_simfiles:
            packs_dict[pack_name].append(file_path)
        
        # Get pack names and count
        pack_names = sorted(packs_dict.keys())
        total_packs = len(pack_names)
        total_loaded = 0
        failed_count = 0
        # Load pack by pack
        for pack_idx, pack_name in enumerate(pack_names, 1):
            if self._cancelled:
                break
            
            # Emit progress for this pack
            self.progress_update.emit(pack_idx, total_packs, pack_name)
            
            # Load all simfiles in this pack
            pack_files = packs_dict[pack_name]
            for file_path in pack_files:
                if self._cancelled:
                    break
                
                if self.controller._load_from_file_path(file_path, pack_name):
                    total_loaded += 1
                else:
                    failed_count += 1
            
            # Notify that this pack is complete (for incremental UI updates)
            self.pack_loaded.emit(pack_name)
        
        self.loading_complete.emit(total_loaded, failed_count)
