from dataclasses import dataclass
from pathlib import Path

@dataclass
class SearchOptions:
  lastfm_api_key: str|None
  discogs_api_key: str|None
  api_search_order: list[str]|None
  cache_file:str|None

@dataclass
class Options:
  sm_dir: str
  verbose: bool
  dry_run: bool
  ignore_sm_genre: bool
  no_translit: bool
  search_options: SearchOptions

@dataclass
class SimfileResult:
  filepath: Path
  artist:str|None
  title:str|None
  subtitle:str|None
  original_genre: str|None
  new_genre:str|None