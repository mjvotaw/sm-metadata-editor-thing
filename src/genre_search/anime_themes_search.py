from fuzzytrackmatch.base_genre_search import BasicArtistInfo, BasicTrackInfo, GenreTag
from fuzzytrackmatch import BaseGenreSearch
from .animethemes_client.client import AnimeThemesClient
from .animethemes_client.models import Anime, AnimeTheme, Artist, SearchResult


class AnimeThemesSearch(BaseGenreSearch[AnimeTheme, Artist]):

  def __init__(self, title_cutoff=0.6, artist_cutoff=0.7):
    super().__init__(title_cutoff, artist_cutoff)
    self.client = AnimeThemesClient()

  def _perform_artist_search(self, artists: list[str]) -> list[BasicArtistInfo[Artist]]:
    return []
  
  def _perform_track_search(self, artist: list[str], title: str) -> list[BasicTrackInfo[AnimeTheme]]:
    query = f"{title} {artist[0]}"
    result = self._search_for_anime_themes(query)
    track_infos = self._find_matching_anime_themes(artist, title, result)
    return track_infos
  
  def _get_genre_tags_from_artist(self, artist: BasicArtistInfo) -> list[GenreTag]:
    return [GenreTag(name="Anime", score=0)]
  
  def _get_genre_tags_from_track(self, track: BasicTrackInfo) -> list[GenreTag]:
    return [GenreTag(name="Anime", score=0)]

  def _search_for_anime_themes(self, q:str):

    return self.client.search(q, limit=10, fields={"search":"anime,animethemes"}, include={"anime":"animethemes.song,animethemes.song.artists,animesynonyms","animetheme":"song,song.artists,anime"})
  

  def _find_matching_anime_themes(self, artist: list[str], title: str, result:SearchResult):
    
    theme_infos: list[BasicTrackInfo[AnimeTheme]] = []
    
    # first, get themes from returned animes
    for anime in result.anime:
      anime_track_info = self._make_track_info_for_anime(anime, artist, title)
      if anime_track_info is not None:
        theme_infos.append(anime_track_info)
    
    already_added_theme_ids = [t.raw_object.id for t in theme_infos]
    # then, get any remaining themes that weren't already added by the anime
    for theme in result.animethemes:
      if theme.id not in already_added_theme_ids:
        theme_track_info = self._make_track_info_for_theme(theme)
        if theme_track_info is not None:
          theme_infos.append(theme_track_info)
          already_added_theme_ids.append(theme.id)

    return theme_infos


  def _make_track_info_for_anime(self, anime: Anime, artists: list[str], title: str):
    anime_names = [anime.name]
    if anime.animesynonyms is not None:
      anime_names += [s.text for s in anime.animesynonyms]

    # find whichever of this anime's names best matches our title
    best_matching_name = self.get_best_matching_title(title, anime_names)
    
    if best_matching_name is None:
      return None
    
    if anime.animethemes is not None:
      best_matching_theme = self._get_best_matching_theme_artists(anime.animethemes, artists)

      if best_matching_theme is not None:
        theme_artists = self._get_artists_from_anime_theme(best_matching_theme)
        if theme_artists is not None:
          source_url = f"https://animethemes.moe/anime/{anime.slug}"
          track_info = BasicTrackInfo(title=best_matching_name, artists=theme_artists, source_url=source_url, raw_object=best_matching_theme)
          return track_info
    
    return None
  
  def _make_track_info_for_theme(self, theme: AnimeTheme):
    if theme.anime is not None and theme.song is not None and theme.song.artists is not None:
      theme_title = theme.song.title
      theme_artists = self._get_artists_from_anime_theme(theme)
      source_url = f"https://animethemes.moe/anime/{theme.anime.slug}"
      if theme_title is not None and theme_artists is not None:
        track_info = BasicTrackInfo(title=theme_title, artists=theme_artists,source_url=source_url,raw_object=theme)
        return track_info
    
    return None


  
  def _get_best_matching_theme_artists(self, themes: list[AnimeTheme], searched_artists: list[str]):

    best_match = None
    best_score = 0

    for theme in themes:
      theme_artists = self._get_artists_from_anime_theme(theme)
      if theme_artists is not None:
        score = self._score_artist(theme_artists, searched_artists)
        if score > best_score:
          best_match = theme
          best_score = score
    
    return best_match

  def _get_artists_from_anime_theme(self, theme: AnimeTheme):
    
    if theme.song is not None and theme.song.artists is not None:
      return [a.name for a in theme.song.artists]
  
    return None

