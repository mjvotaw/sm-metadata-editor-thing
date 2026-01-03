from enum import Enum
import json
from typing import Any, Dict, Optional
from typing_extensions import Self
from .app_paths import AppPaths

class ConfigEnum:
    VERSION = "version"
    LAST_DIR = "last_directory"
    LOG_LEVEL = "log_level"

    WINDOW_SIZE = 'window_size'
    WINDOW_POSITION = 'window_position'

    # Genre search options
    LASTFM_API_KEY = 'lastfm_api_key'
    DISCOGS_API_KEY = 'discogs_api_key'
    SIMILARITY_THRESH = 'similarity_threshold'

    # Save options

    SAVE_BACKUP = 'save_backup'
    
class ConfigManager(object):
    """
    Singleton class that manages loading/saving application configuration settings
    """
    
    DEFAULT_CONFIG = {
        ConfigEnum.VERSION: '0.1',
        ConfigEnum.LAST_DIR: '',
        ConfigEnum.LOG_LEVEL: 'INFO',
        ConfigEnum.SIMILARITY_THRESH: 0.65,
        ConfigEnum.SAVE_BACKUP: True,
    }

    def __new__(cls) -> Self:
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConfigManager, cls).__new__(cls)
        return cls.instance
        
    def __init__(self):
        self.config_filepath = AppPaths.config_file()
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if not self.config_filepath.exists():
            return False
        
        try:
            with open(self.config_filepath, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
                self.config = {**self.DEFAULT_CONFIG, **loaded_config}
            return True
            
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False

    def save(self):
        try:
            self.config_filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any=None):
        return self.config.get(key, default)
    
    def get_values(self):
        return self.config.copy()
    
    def set(self, key: str, value: Any, auto_save: bool=True):
        self.config[key] = value
        if auto_save:
            self.save()
    
    def bulk_update(self, updates: Dict[str, Any], auto_save: bool = True):
        self.config.update(updates)
        if auto_save:
            self.save()

    
    def reset_to_defaults(self) -> None:
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
