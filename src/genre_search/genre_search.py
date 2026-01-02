from .models import SearchOptions
from fuzzytrackmatch import LastFMSearch, DiscogsSearch, BaseGenreSearch
from .last_fm_scraper import LastFmScraper
from .anime_themes_search import AnimeThemesSearch
import json
from pathlib import Path
from dataclasses import asdict
from src.utils.logger import get_logger

logger = get_logger(__name__)
class GenreSearch:

  def __init__(self, options: SearchOptions):
    self.options = options
    self.cache:dict[str, dict[str,list[list[str]]]] = {}
    self.cache_file = options.cache_file
    self.search_order: list[str] = []
    self.searchers:dict[str, BaseGenreSearch] = {}

    self._load_cache()
    
    self._setup_searchers(options)
    

  def get_genres(self, artist: str, title: str, subtitle: str|None):
    # Create a cache key from the search parameters
    cache_key = f"{artist}|{title}|{subtitle or ''}"
    
    # Search through available searchers
    for search_option in self.search_order:
      cached_genres = self._get_from_cache(cache_key, search_option)
      if cached_genres is not None:
        if len(cached_genres) > 0:
          return cached_genres
        else:
          continue

      searcher = self.searchers[search_option]
      track_and_genres = searcher.fetch_track_genres(artist, title, subtitle)
      if track_and_genres:
        logger.debug(f"{search_option}| track returned for {artist} {title} {subtitle}: {track_and_genres.track}")
        # Cache the result
        genres = track_and_genres.canonicalized_genres
        if search_option == "animethemes":
          # animethemes doesn't really return a "canonical" genre, so use whatever GenreTag was returned
          genres = [[track_and_genres.genres[0].name]]
        
        self._add_to_cache(cache_key, genres, search_option)
        self._save_cache()
        return genres
      else:
        logger.debug(f"{search_option}| no track returned for {artist} {title} {subtitle}")
        self._add_to_cache(cache_key, [], search_option)
    self._save_cache()
    return []


  def _setup_searchers(self, options: SearchOptions):
    self.search_order = options.api_search_order or ["lastfm", "discogs"]
    for search in self.search_order:
      if search == "lastfm":
        if options.lastfm_api_key:
          self.searchers["lastfm"] = LastFmScraper(api_key=options.lastfm_api_key)
      elif search == "discogs":
        if options.discogs_api_key:
          self.searchers["discogs"] = DiscogsSearch(api_key=options.discogs_api_key)
      elif search == "animethemes":
        self.searchers["animethemes"] = AnimeThemesSearch()


  def _get_from_cache(self, cache_key: str, source: str):
    
    if cache_key in self.cache and source in self.cache[cache_key]:
      return self.cache[cache_key][source]
    return None
  
  def _add_to_cache(self, cache_key: str, genres: list[list[str]], source: str):
    if cache_key not in self.cache:
      self.cache[cache_key] = {}
    
    self.cache[cache_key][source] = genres

  def _load_cache(self):
    if self.cache_file:
      cache_path = Path(self.cache_file)
      if cache_path.exists():
        try:
          with open(cache_path) as f:
            self.cache = json.load(f)
        except Exception as e:
          print(f"Warning: Failed to load cache file {self.cache_file}: {e}")

  def _save_cache(self):
    """Save the cache to disk if a cache file is configured."""
    if self.cache_file:
      try:
        cache_path = Path(self.cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
          json.dump(self.cache, f, indent=2)
      except Exception as e:
        print(f"Warning: Failed to save cache file {self.cache_file}: {e}")
      
