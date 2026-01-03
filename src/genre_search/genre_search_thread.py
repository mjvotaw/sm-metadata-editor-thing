from typing import Set, Tuple
from PyQt6.QtCore import pyqtSignal, QThread
from pathlib import Path
from mutagen import File
from src.models import SimfileMetadata
from src.utils.app_paths import AppPaths
from src.utils.config_manager import ConfigManager, ConfigEnum
from src.utils.sm_utils import strip_common_sm_words
from .genre_pick import pick_genre
from .genre_search import GenreSearch
from .models import SearchOptions
from src.utils.logger import get_logger
from fuzzytrackmatch import GenreTag
from src.models.audio_metadata import AudioMetadata

logger = get_logger(__name__)

class GenreSearchThread(QThread):
    """Background thread for searching genres."""
    
    progress_update = pyqtSignal(int, int, str)  # current, total, title
    genres_found = pyqtSignal(int, list)  # row_index, possible_genres list[list[GenreTag]]
    no_genre_found = pyqtSignal(int) #row_index
    search_complete = pyqtSignal()
    
    def __init__(self, simfiles: list[SimfileMetadata], api_search_sources: list[str], check_audio_files:bool=False):
        super().__init__()
        self.simfiles = simfiles
        self.config = ConfigManager()
        # move animethemes.moe to the end, it's a last resort option
        if "animethemes" in api_search_sources:
            api_search_sources.remove("animethemes")
            api_search_sources.append("animethemes")
        self.search_sources = api_search_sources
        self.check_audio_files = check_audio_files
        self._setup_genre_search()
        self._cancelled = False
    

    def _setup_genre_search(self):
        lastfm_api_key = self.config.get(ConfigEnum.LASTFM_API_KEY)
        discogs_api_key = self.config.get(ConfigEnum.DISCOGS_API_KEY)
        similarity_threshold = self.config.get(ConfigEnum.SIMILARITY_THRESH, default=0.65)
        cache_file = (AppPaths.config_dir() / "genre_cache.json").absolute()

        search_options = SearchOptions(lastfm_api_key=lastfm_api_key, discogs_api_key=discogs_api_key, api_search_order=self.search_sources, cache_file=str(cache_file), similarity_threshold=similarity_threshold)

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
            result = self._do_search_for_simfile(simfile)
            if result is not None:
                self.genres_found.emit(idx, result)
            else:
                self.no_genre_found.emit(idx)
        logger.debug(f"Finished search.")
        self.search_complete.emit()
    
    def _do_search_for_simfile(self, simfile: SimfileMetadata):

        result: list[list[GenreTag]] = []
        artist = simfile.artist
        title = strip_common_sm_words(simfile.title)
        subtitle = strip_common_sm_words(simfile.subtitle)
        normal_results = self._search_genre(artist, title, subtitle)
        if normal_results:
            result += normal_results
        
        # if the simfile has translit title or artist, search with those as well,
        # and merge the results
        if simfile.artisttranslit or simfile.titletranslit:
            artist = strip_common_sm_words(simfile.artisttranslit or simfile.artist)
            title = strip_common_sm_words(simfile.titletranslit or simfile.title)
            subtitle = strip_common_sm_words(simfile.subtitletranslit or simfile.subtitle)
            result_translit = self._search_genre(artist, title, subtitle)

            if result_translit is not None:
                result += result_translit

        # sometimes the audio file has useful tags that we can pull info from
        if self.check_audio_files and simfile.music:
            audio_metadata = AudioMetadata.from_audio_file(simfile.music)

            if audio_metadata is not None:
                if audio_metadata.artist and audio_metadata.title:
                    audio_result = self._search_genre(audio_metadata.artist, audio_metadata.title, "")
                    if audio_result is not None:
                        if result is None:
                            result = audio_result
                        else:
                            result = result + audio_result
                
                if audio_metadata.genre:
                    maybe_genre = self.genre_search.normalize_genre(audio_metadata.genre)
                    if maybe_genre:
                        result += maybe_genre

        if len(result) == 0:
            return None
        return result
    

    def _search_genre(self,artist: str, title: str, subtitle: str) -> list[list[GenreTag]] | None:
        logger.debug(f"starting search for {artist} {title} {subtitle}")
        genres = self.genre_search.get_genres(artist, title, subtitle)
        logger.debug(f"genres for {artist} {title} {subtitle}: {genres}")
        if len(genres) == 0:
            return None
        return genres
    


        