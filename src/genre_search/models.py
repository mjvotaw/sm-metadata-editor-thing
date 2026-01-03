from dataclasses import dataclass
from pathlib import Path

@dataclass
class SearchOptions:
  lastfm_api_key: str|None
  discogs_api_key: str|None
  api_search_order: list[str]|None
  cache_file:str|None
  similarity_threshold:float

