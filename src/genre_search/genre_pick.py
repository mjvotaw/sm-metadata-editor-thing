from fuzzytrackmatch import GenreTag

def pick_genre(canonicalized_genres: list[list[GenreTag]]):
  """Do a bunch of stuff to figure out the most appropriate
  genre. This is a pretty subjective job.
  """
  # first, look through all of the canonicalized_genres
  # for some specific pop genres
  for g in canonicalized_genres:
    regional_pop = get_regional_pop(g)
    if regional_pop:
      return regional_pop
    just_pop = get_pop(g)
    if just_pop:
      return just_pop
    
  # then, look for a dance genre
  for g in canonicalized_genres:
    dance_genre = get_dance_genre(g)
    if dance_genre:
      return dance_genre
    
  # then, uh, just return whatever genre is the most specific?
  longest_genre = max(canonicalized_genres, key=len)
  return longest_genre[0]
    

def get_pop(canonicalized_genre: list[str]):
  if 'Pop' in canonicalized_genre:
    return 'Pop'

def get_regional_pop(canonicalized_genre: list[str]):
  """
  If canonicalized_genre contains a pop genre that represents
  a specific region, return it.
  """
  # list of pop sub-genres pulled from genres-tree.yaml
  regional_pop_genres = [
'Arab Pop',
'Austropop',
'Balkan Pop',
'French Pop',
'Latin Pop',
'Nederpop',
'Russian Pop',
'Iranian Pop',
'Mexican Pop',
'Turkish Pop',
'Europop',
'Vispop',
'J-Pop',
'K-Pop',
'C-Pop',]
  
  for reg in regional_pop_genres:
    if reg in canonicalized_genre:

      return reg
  
  return None

def get_dance_genre(canonicalized_genre: list[str]):
  """"
  If `canonicalized_genre` is a dance genre, return a sub-genre
  that isn't too specific, but more specific than 'dance', since
  that represents, like, a ton of music.
  """

  if 'Dance' in canonicalized_genre:
    # nobody knows what "uk garage" is, so remove it
    if "Uk Garage" in canonicalized_genre:
        canonicalized_genre = canonicalized_genre.copy()
        canonicalized_genre.remove("Uk Garage")
    if len(canonicalized_genre) > 1:
      

      return canonicalized_genre[-2]
    else:
      return canonicalized_genre[-1]
  return None