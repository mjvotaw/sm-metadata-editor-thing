from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Anime:
  """Represents an anime production with opening/ending sequences."""

  id: int
  name: str
  slug: str
  year: Optional[int] = None
  season: Optional[str] = None
  media_format: Optional[str] = None
  synopsis: Optional[str] = None
  created_at: Optional[str] = None
  updated_at: Optional[str] = None
  deleted_at: Optional[str] = None
  animesynonyms: Optional[list["AnimeSynonym"]] = None
  animethemes: Optional[list["AnimeTheme"]] = None

  @classmethod
  def from_dict(cls, data: dict) -> "Anime":
    return cls(
      id=data["id"],
      name=data["name"],
      slug=data["slug"],
      year=data.get("year"),
      season=data.get("season"),
      media_format=data.get("media_format"),
      synopsis=data.get("synopsis"),
      created_at=data.get("created_at"),
      updated_at=data.get("updated_at"),
      deleted_at=data.get("deleted_at"),
      animesynonyms=[AnimeSynonym.from_dict(s) for s in data["animesynonyms"]] if data.get("animesynonyms") else None,
      animethemes=[AnimeTheme.from_dict(t) for t in data["animethemes"]] if data.get("animethemes") else None,
    )


@dataclass
class AnimeSynonym:
  id: int
  text: str
  type: str

  @classmethod
  def from_dict(cls, data: dict) -> "AnimeSynonym":
    return cls(
      id=data["id"],
      text=data["text"],
      type=data["type"],
    )


@dataclass
class AnimeTheme:
  """Represents an opening or ending theme for an anime."""

  id: int
  type: Optional[str] = None
  sequence: Optional[int] = None
  group: Optional[str] = None
  slug: Optional[str] = None
  created_at: Optional[str] = None
  updated_at: Optional[str] = None
  deleted_at: Optional[str] = None
  song: Optional["Song"] = None
  anime: Optional["Anime"] = None

  @classmethod
  def from_dict(cls, data: dict) -> "AnimeTheme":
    return cls(
      id=data["id"],
      type=data.get("type"),
      sequence=data.get("sequence"),
      group=data.get("group"),
      slug=data.get("slug"),
      created_at=data.get("created_at"),
      updated_at=data.get("updated_at"),
      deleted_at=data.get("deleted_at"),
      song=Song.from_dict(data["song"]) if data.get("song") else None,
      anime=Anime.from_dict(data["anime"]) if data.get("anime") else None,
    )


@dataclass
class Artist:
  """Represents a musical performer of anime sequences."""

  id: int
  name: str
  slug: str
  created_at: Optional[str] = None
  updated_at: Optional[str] = None
  deleted_at: Optional[str] = None

  @classmethod
  def from_dict(cls, data: dict) -> "Artist":
    return cls(
      id=data["id"],
      name=data["name"],
      slug=data["slug"],
      created_at=data.get("created_at"),
      updated_at=data.get("updated_at"),
      deleted_at=data.get("deleted_at"),
    )


@dataclass
class Playlist:
  """Represents an ordered list of tracks for continuous playback."""

  id: str
  name: str
  description: Optional[str] = None
  visibility: Optional[str] = None
  created_at: Optional[str] = None
  updated_at: Optional[str] = None
  deleted_at: Optional[str] = None

  @classmethod
  def from_dict(cls, data: dict) -> "Playlist":
    return cls(
      id=data["id"],
      name=data["name"],
      description=data.get("description"),
      visibility=data.get("visibility"),
      created_at=data.get("created_at"),
      updated_at=data.get("updated_at"),
      deleted_at=data.get("deleted_at"),
    )


@dataclass
class Series:
  """Represents a collection of related anime."""

  id: int
  name: str
  slug: str
  created_at: Optional[str] = None
  updated_at: Optional[str] = None
  deleted_at: Optional[str] = None

  @classmethod
  def from_dict(cls, data: dict) -> "Series":
    return cls(
      id=data["id"],
      name=data["name"],
      slug=data["slug"],
      created_at=data.get("created_at"),
      updated_at=data.get("updated_at"),
      deleted_at=data.get("deleted_at"),
    )


@dataclass
class Song:
  """Represents a composition that accompanies an AnimeTheme."""

  id: int
  title: Optional[str] = None
  created_at: Optional[str] = None
  updated_at: Optional[str] = None
  deleted_at: Optional[str] = None
  artists: Optional[list[Artist]] = None

  @classmethod
  def from_dict(cls, data: dict) -> "Song":
    return cls(
      id=data["id"],
      title=data.get("title"),
      created_at=data.get("created_at"),
      updated_at=data.get("updated_at"),
      deleted_at=data.get("deleted_at"),
      artists=[Artist.from_dict(a) for a in data["artists"]] if data.get("artists") else None,
    )


@dataclass
class Video:
  """Represents a WebM file of an anime theme."""

  id: int
  basename: str
  filename: str
  path: str
  size: int
  mimetype: str
  nc: bool
  subbed: bool
  lyrics: bool
  uncen: bool
  overlap: str
  created_at: str
  updated_at: str
  resolution: Optional[int] = None
  source: Optional[str] = None
  tags: Optional[str] = None
  link: Optional[str] = None
  deleted_at: Optional[str] = None

  @classmethod
  def from_dict(cls, data: dict) -> "Video":
    return cls(
      id=data["id"],
      basename=data["basename"],
      filename=data["filename"],
      path=data["path"],
      size=data["size"],
      mimetype=data["mimetype"],
      nc=data["nc"],
      subbed=data["subbed"],
      lyrics=data["lyrics"],
      uncen=data["uncen"],
      overlap=data["overlap"],
      created_at=data["created_at"],
      updated_at=data["updated_at"],
      resolution=data.get("resolution"),
      source=data.get("source"),
      tags=data.get("tags"),
      link=data.get("link"),
      deleted_at=data.get("deleted_at"),
    )


@dataclass
class SearchResult:
  """Represents the complete response from a search query."""

  anime: list[Anime]
  animethemes: list[AnimeTheme]
  artists: list[Artist]
  playlists: list[Playlist]
  series: list[Series]
  songs: list[Song]
  videos: list[Video]

  @classmethod
  def from_dict(cls, data: dict) -> "SearchResult":
    return cls(
      anime=[Anime.from_dict(a) for a in data.get("anime", [])],
      animethemes=[AnimeTheme.from_dict(t) for t in data.get("animethemes", [])],
      artists=[Artist.from_dict(a) for a in data.get("artists", [])],
      playlists=[Playlist.from_dict(p) for p in data.get("playlists", [])],
      series=[Series.from_dict(s) for s in data.get("series", [])],
      songs=[Song.from_dict(s) for s in data.get("songs", [])],
      videos=[Video.from_dict(v) for v in data.get("videos", [])],
    )