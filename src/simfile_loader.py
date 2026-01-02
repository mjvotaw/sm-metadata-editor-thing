import os
from pathlib import Path
from typing import List, Optional, Tuple
import shutil
import simfile
from simfile.types import Simfile

from src.models import SimfileMetadata, PackInfo
from src.field_registry import FieldRegistry, FieldType
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SimfileLoader:
    """
    Handles loading and parsing of simfiles using the simfile package.
    """
    
    SIMFILE_EXTENSIONS = ['.sm', '.ssc']
    
    @staticmethod
    def find_simfiles_in_directory(root_path: Path) -> List[Tuple[Path, str]]:
        """
        Recursively find all simfiles in a directory.
        Returns list of tuples: (simfile_path, pack_name)
        """
        simfiles = []
        
        for path in root_path.rglob('*'):
            if path.suffix.lower() in SimfileLoader.SIMFILE_EXTENSIONS:
                # Determine pack name from directory structure
                # Typically the immediate parent directory is the song folder,
                # and its parent is the pack folder
                song_dir = path.parent
                pack_dir = song_dir.parent if song_dir.parent != root_path else root_path
                pack_name = pack_dir.name if pack_dir != root_path else "Default Pack"
                
                simfiles.append((path, pack_name))
        
        logger.debug(f"Found {len(simfiles)} simfiles")
        return simfiles
    
    @staticmethod
    def load_simfile(file_path: Path) -> Optional[Simfile]:
        """
        Load and parse a simfile from disk.
        Returns None if loading fails.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return simfile.load(f)
        except Exception as e:
            print(f"Error loading simfile {file_path}: {e}")
            return None
    
    @staticmethod
    def simfile_to_metadata(
        parsed_simfile: Simfile,
        file_path: Path,
        pack_name: str
    ) -> SimfileMetadata:
        """
        Convert a parsed Simfile object to our SimfileMetadata model.
        Uses the field registry to dynamically extract all fields.
        """
        simfile_id = str(file_path.absolute())
        extension = os.path.splitext(file_path)[1]

        # Build metadata kwargs from field registry
        metadata_kwargs = {
            'id': simfile_id,
            'pack_name': pack_name,
            'file_path': file_path,
            'file_type': extension,
        }
        

        # Extract all fields defined in the registry
        for field_def in FieldRegistry.get_all_fields():
            # Get value from parsed simfile (simfile package uses lowercase)
            value = getattr(parsed_simfile, field_def.internal_name.lower(), "")
            
            
            if value != "" and value is not None:
                if field_def.field_type.isFilePath():
                    value = SimfileLoader._get_absolute_filepath(value, file_path)
            else:
                value = field_def.default_value
            
            
            metadata_kwargs[field_def.internal_name] = value
        
        # Count charts
        num_charts = len(parsed_simfile.charts) if hasattr(parsed_simfile, 'charts') else 0
        metadata_kwargs['num_charts'] = num_charts
        
        metadata = SimfileMetadata(**metadata_kwargs)
        
        return metadata
    
    @staticmethod
    def save_simfile(metadata: SimfileMetadata, parsed_simfile: Simfile) -> bool:
        """
        Save changes from metadata back to the simfile and write to disk.
        Returns True if successful.
        Uses the field registry to dynamically save all fields.
        """
        try:
            for field_def in FieldRegistry.get_all_fields():
                if not metadata.is_field_editable(field_def.internal_name):
                    continue
                
                value = getattr(metadata, field_def.internal_name, "")
                if field_def.field_type.isFilePath() and value != "":
                    prev_value = metadata.get_original_value(field_def.internal_name)
                    if prev_value is not None:
                        # TODO: ask if we want to delete/overwrite this file
                        pass
                    
                    value = SimfileLoader._ensure_relative_filepath(value, metadata.file_path)
                    if value is None:
                        continue
                setattr(parsed_simfile, field_def.internal_name.lower(), value)
            
            with open(metadata.file_path, 'w', encoding='utf-8') as f:
                parsed_simfile.serialize(f)
            
            return True
        except Exception as e:
            print(f"Error saving simfile {metadata.file_path}: {e}")
            return False
    
    @staticmethod
    def _get_absolute_filepath(relative_filepath: str, simfile_filepath: Path):
        simfile_dir = simfile_filepath.parent
        absolute_filepath = str((simfile_dir / relative_filepath).resolve())
        return absolute_filepath
    
    @staticmethod
    def _ensure_relative_filepath(asset_filepath: str, simfile_filepath: Path):
        """
        Checks if the given asset_filepath is relative to simfile_filepath
        or 
        """
        simfile_dir = simfile_filepath.parent
        asset_path = Path(asset_filepath)

        # is the asset already within the simfile_dir?
        if asset_path.parent == simfile_dir:
            relative_asset_filepath = str(asset_path.relative_to(simfile_dir))
            return relative_asset_filepath
        # or is it within the simfile pack dir?
        elif asset_path.parent == simfile_dir.parent:
            relative_asset_filepath = str(asset_path.relative_to(simfile_dir, walk_up=True))
            return relative_asset_filepath
        
        # if not, then we need to copy it to the simfile_dir
        else:
            try:
                asset_basename = os.path.basename(asset_filepath)
                new_asset_path = Path(simfile_dir, asset_basename)
                shutil.copyfile(asset_path, new_asset_path)
                relative_asset_filepath = str(new_asset_path.relative_to(simfile_dir))
                return relative_asset_filepath
            except Exception as e:
                return None

            