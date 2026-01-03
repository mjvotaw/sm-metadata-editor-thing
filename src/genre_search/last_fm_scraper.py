import requests
from bs4 import BeautifulSoup
import pylast
from fuzzytrackmatch import LastFMSearch
from fuzzytrackmatch.base_genre_search import GenreTag

class LastFmScraper(LastFMSearch):

  def _fetch_genres(self, lastfm_obj:pylast._Taggable):
    tags = super()._fetch_genres(lastfm_obj)

    if len(tags) == 0:
      if isinstance(lastfm_obj, pylast.Track) or isinstance(lastfm_obj, pylast.Artist):
        url = lastfm_obj.get_url()
        scraped_tags = self.scrape_tags(url)
        return scraped_tags
    return tags
  
  def scrape_tags(self, last_fm_url: str):
    response = requests.get(last_fm_url)

    soup = BeautifulSoup(response.content, 'html.parser')

    section = soup.find("section", class_="catalogue-tags")
    if section:
      tags = section.find_all("li")
      tag_texts: list[GenreTag] = [GenreTag(name=tag.text.strip(), score=1) for tag in tags]
      return tag_texts
    
    return []