from typing import Set, Tuple
from PyQt6.QtCore import pyqtSignal, QThread
from src.models import SimfileMetadata
from src.utils.app_paths import AppPaths
from src.utils.config_manager import ConfigManager, ConfigEnum
from src.utils.sm_utils import strip_common_sm_words
from .genre_pick import pick_genre
from .genre_search import GenreSearch
from .models import SearchOptions
from src.utils.logger import get_logger
from fuzzytrackmatch import GenreTag

logger = get_logger(__name__)

class GenreSearchThread(QThread):
    """Background thread for searching genres."""
    
    progress_update = pyqtSignal(int, int, str)  # current, total, title
    genre_found = pyqtSignal(int, list)  # row_index, possible_genres list[list[GenreTag]]
    no_genre_found = pyqtSignal(int) #row_index
    search_complete = pyqtSignal()
    
    def __init__(self, simfiles: list[SimfileMetadata], search_sources: list[str]):
        super().__init__()
        self.simfiles = simfiles
        self.config = ConfigManager()
        # move animethemes.moe to the end, it's a last resort option
        if "animethemes" in search_sources:
            search_sources.remove("animethemes")
            search_sources.append("animethemes")
        self.search_sources = search_sources
        self._setup_genre_search()
        self._cancelled = False
    

    def _setup_genre_search(self):
        lastfm_api_key = self.config.get(ConfigEnum.LASTFM_API_KEY)
        discogs_api_key = self.config.get(ConfigEnum.DISCOGS_API_KEY)
        cache_file = (AppPaths.config_dir() / "genre_cache.json").absolute()

        search_options = SearchOptions(lastfm_api_key=lastfm_api_key, discogs_api_key=discogs_api_key, api_search_order=self.search_sources, cache_file=str(cache_file))

        self.genre_search = GenreSearch(search_options)

    def cancel(self):
        self._cancelled = True
    
    def run(self):
        total = len(self.simfiles)
        
        for idx, simfile in enumerate(self.simfiles):
            if self._cancelled:
                logger.debug("search cancelled, breaking out of loop")
                break
            
            self.progress_update.emit(idx + 1, total, simfile.title)
            
            artist = simfile.artist
            title = strip_common_sm_words(simfile.title)
            subtitle = strip_common_sm_words(simfile.subtitle)
            result = self._search_genre(artist, title, subtitle)
            
            if result is not None:
                self.genre_found.emit(idx, result)
            else:
                self.no_genre_found.emit(idx)
        logger.debug(f"Finished search.")
        self.search_complete.emit()
    
    def _search_genre(self,artist: str, title: str, subtitle: str) -> list[list[GenreTag]] | None:
        logger.debug(f"starting search for {artist} {title} {subtitle}")
        genres = self.genre_search.get_genres(artist, title, subtitle)
        logger.debug(f"genres for {artist} {title} {subtitle}: {genres}")
        if len(genres) == 0:
            return None
        return genres

        