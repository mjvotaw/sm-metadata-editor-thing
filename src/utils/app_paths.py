from platformdirs import user_data_dir
from pathlib import Path

class AppPaths:

    APP_NAME = "smMetadataEditorThing"
    DEV_MODE = False
    @classmethod
    def log_dir(cls):
        return cls.ensure_app_data_subdir("logs")
    
    @classmethod
    def config_dir(cls):
        return cls.ensure_app_data_subdir("config")

    @classmethod
    def config_file(cls):
        config_dir = cls.config_dir()
        config_filepath = (config_dir / "config.json")
        return config_filepath
    
    @classmethod
    def base_app_data_path(cls):
        if cls.DEV_MODE:
            path = (Path.cwd() / cls.APP_NAME).resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
        else:
            path = Path(user_data_dir(cls.APP_NAME, appauthor=False, ensure_exists=True))
            return path

    @classmethod
    def ensure_app_data_subdir(cls, subdir: str|Path):
        basepath = cls.base_app_data_path()
        sub_path = (basepath / subdir).resolve()
        sub_path.mkdir(parents=True, exist_ok=True)
        return sub_path
    

    
