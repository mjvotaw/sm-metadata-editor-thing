from .models import SearchOptions
from fuzzytrackmatch import LastFMSearch, DiscogsSearch, BaseGenreSearch, GenreTag
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
        self.cache: dict[str, dict[str, list[list[GenreTag]]]] = {}
        self.cache_file = options.cache_file
        self.search_order: list[str] = []
        self.searchers: dict[str, BaseGenreSearch] = {}

        self._load_cache()

        self._setup_searchers(options)

    def get_genres(self, artist: str, title: str, subtitle: str | None) -> list[list[GenreTag]]:
        # Create a cache key from the search parameters
        cache_key = f"{artist}|{title}|{subtitle or ''}"
        genres: list[list[GenreTag]] = []
        # Search through available searchers
        for search_option in self.search_order:
            # for animethemes.moe, skip it if we've already got results from a previous
            # search option (animethemes.moe is kind of a last resort)
            if search_option == "animethemes" and len(genres) > 0:
                continue

            logger.debug(f"{search_option}| starting search")
            cached_genres = self._get_from_cache(cache_key, search_option)
            if cached_genres is not None:
                logger.debug(f"{search_option}| found cached data for {artist} {title} {subtitle}: {cached_genres}")
                if len(cached_genres) > 0:
                    genres += cached_genres
                continue

            searcher = self.searchers[search_option]
            
            try:
                track_and_genres = searcher.fetch_track_genres(
                    artist, title, subtitle)
                if track_and_genres:
                    logger.debug(
                        f"{search_option}| track returned for {artist} {title} {subtitle}: {track_and_genres.track}")
                    
                    if track_and_genres.track.match_score < self.options.similarity_threshold:
                        logger.debug(f"{search_option}| skipping result, match_score {track_and_genres.track.match_score} < threshold {self.options.similarity_threshold}")
                        continue
                    # Cache the result

                    returned_genres = track_and_genres.canonicalized_genres
                    if search_option == "animethemes" and len(track_and_genres.genres) > 0:
                        # animethemes doesn't really return a "canonical" genre, so use whatever GenreTag was returned
                        returned_genres = [[track_and_genres.genres[0]]]

                    self._add_to_cache(cache_key, returned_genres, search_option)
                    self._save_cache()
                    genres += returned_genres
                else:
                    logger.debug(
                        f"{search_option}| no track returned for {artist} {title} {subtitle}")
                    self._add_to_cache(cache_key, [], search_option)
            except Exception as e:
                logger.debug(
                    f"{search_option}| error thrown while trying to get genre data for {artist} {title} {subtitle}: {e}")

        self._save_cache()
        return genres

    def _setup_searchers(self, options: SearchOptions):
        self.search_order = options.api_search_order or ["lastfm", "discogs"]
        for search in self.search_order:
            if search == "lastfm":
                if options.lastfm_api_key:
                    self.searchers["lastfm"] = LastFmScraper(
                        api_key=options.lastfm_api_key)
            elif search == "discogs":
                if options.discogs_api_key:
                    self.searchers["discogs"] = DiscogsSearch(
                        api_key=options.discogs_api_key)
            elif search == "animethemes":
                self.searchers["animethemes"] = AnimeThemesSearch()

    def _get_from_cache(self, cache_key: str, source: str):

        if cache_key in self.cache and source in self.cache[cache_key]:
            return self.cache[cache_key][source]
        return None

    def _add_to_cache(self, cache_key: str, genres: list[list[GenreTag]], source: str):
        if cache_key not in self.cache:
            self.cache[cache_key] = {}
        self.cache[cache_key][source] = genres.copy()

    def _load_cache(self):
        if self.cache_file:
            cache_path = Path(self.cache_file)
            if cache_path.exists():
                try:
                    with open(cache_path) as f:
                        loaded_cache = json.load(f)
                        rebuilt_cache: dict[str, dict[str,
                                                      list[list[GenreTag]]]] = {}

                        for cache_key, obj in loaded_cache.items():
                            rebuilt_cache[cache_key] = {}
                            for source, genre_groups in obj.items():
                                rebuilt_cache[cache_key][source] = []
                                for genres in genre_groups:
                                    genre_tags = [
                                        GenreTag.from_dict(g) for g in genres]
                                    rebuilt_cache[cache_key][source].append(
                                        genre_tags)

                        self.cache = rebuilt_cache
                except Exception as e:
                    print(
                        f"Warning: Failed to load cache file {self.cache_file}: {e}")

    def _cache_as_dicts(self, cache: dict[str, dict[str, list[list[GenreTag]]]]):
        cache_as_dicts: dict[str, dict[str, list[list[dict]]]] = {}
        for cache_key, obj in cache.items():
            cache_as_dicts[cache_key] = {}
            for source, genre_groups in obj.items():
                cache_as_dicts[cache_key][source] = []
                for genres in genre_groups:
                    genre_tags = [g.__dict__ for g in genres]
                    cache_as_dicts[cache_key][source].append(genre_tags)
        
        return cache_as_dicts

    def _save_cache(self):
        """Save the cache to disk if a cache file is configured."""
        if self.cache_file:
            try:
                cache_path = Path(self.cache_file)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_path, 'w') as f:
                    cache_as_dicts = self._cache_as_dicts(self.cache)
                    json.dump(cache_as_dicts, f, indent=2)
            except Exception as e:
                print(
                    f"Warning: Failed to save cache file '{self.cache_file}': {e}")
