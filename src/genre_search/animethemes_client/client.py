"""
AnimeThemes API client for searching resources.

This module provides a simple interface to the AnimeThemes search endpoint.
"""

import requests
from typing import Optional
from urllib.parse import urlencode
import json

from .models import (
  Anime,
  AnimeTheme,
  Artist,
  Playlist,
  Series,
  Song,
  Video,
  SearchResult,
)


class AnimeThemesClient:
  """Client for interacting with the AnimeThemes API."""

  BASE_URL = "https://api.animethemes.moe"

  def __init__(self, timeout: int = 30):
    """
    Initialize the AnimeThemes API client.

    Args:
      timeout: Request timeout in seconds (default: 30)
    """
    self.timeout = timeout
    self.session = requests.Session()

  def search(
    self,
    query: str,
    limit: Optional[int] = None,
    include: Optional[dict[str, str]] = None,
    fields: Optional[dict[str, str]] = None,
    filters: Optional[dict[str, str]] = None,
    sort: Optional[dict[str, str]] = None,
  ) -> SearchResult:
    """
    Search for resources matching the given query.

    Args:
      query: The search query (required)
      limit: Maximum number of results per resource type
      include: Dict of resource types and what to include (e.g., {"anime": "resources"})
      fields: Dict of resource types and sparse fields (e.g., {"anime": "id,name"})
      filters: Dict of filter parameters
      sort: Dict of sort parameters by type

    Returns:
      SearchResult containing lists of matched resources

    Raises:
      ValueError: If query is empty
      requests.RequestException: If the API request fails
    """
    if not query or not query.strip():
      raise ValueError("Search query cannot be empty")

    params = self._build_params(query, limit, include, fields, filters, sort)

    response = self.session.get(
      f"{self.BASE_URL}/search",
      params=params,
      timeout=self.timeout,
    )
    response.raise_for_status()

    return self._parse_response(response.json())

  def _build_params(
    self,
    query: str,
    limit: Optional[int],
    include: Optional[dict[str, str]],
    fields: Optional[dict[str, str]],
    filters: Optional[dict[str, str]],
    sort: Optional[dict[str, str]],
  ) -> dict:
    """Build query parameters for the search request."""
    params:dict = {"q": query}

    if limit is not None:
      params["page[limit]"] = limit

    if include:
      for resource_type, include_fields in include.items():
        params[f"include[{resource_type}]"] = include_fields

    if fields:
      for resource_type, field_list in fields.items():
        params[f"fields[{resource_type}]"] = field_list

    if filters:
      params.update(filters)

    if sort:
      for resource_type, sort_fields in sort.items():
        params[f"sort[{resource_type}]"] = sort_fields

    return params

  def _parse_response(self, data: dict) -> SearchResult:
    """Parse the API response into SearchResult object."""
    search_data = data.get("search", {})

    # Handle case where search_data might be a list (legacy API format)
    if isinstance(search_data, list):
      # If it's a list, it's likely empty or malformed, return empty results
      search_data = {}

    return SearchResult(
      anime=[Anime.from_dict(item) for item in search_data.get("anime", [])],
      animethemes=[
        AnimeTheme.from_dict(item) for item in search_data.get("animethemes", [])
      ],
      artists=[Artist.from_dict(item) for item in search_data.get("artists", [])],
      playlists=[Playlist.from_dict(item) for item in search_data.get("playlists", [])],
      series=[Series.from_dict(item) for item in search_data.get("series", [])],
      songs=[Song.from_dict(item) for item in search_data.get("songs", [])],
      videos=[Video.from_dict(item) for item in search_data.get("videos", [])],
    )

  def get_raw_response(self, query: str) -> dict:
    """Get the raw API response for debugging purposes.
    
    Args:
      query: The search query
      
    Returns:
      The raw JSON response from the API
    """
    if not query or not query.strip():
      raise ValueError("Search query cannot be empty")

    params = {"q": query}
    response = self.session.get(
      f"{self.BASE_URL}/search",
      params=params,
      timeout=self.timeout,
    )
    response.raise_for_status()
    
    return response.json()

  def close(self):
    """Close the session."""
    self.session.close()

  def __enter__(self):
    """Context manager entry."""
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit."""
    self.close()
