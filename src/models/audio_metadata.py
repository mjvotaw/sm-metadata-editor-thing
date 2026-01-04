from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from mutagen._file import File

@dataclass
class AudioMetadata:

    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    genres: Optional[list[str]]

    @staticmethod
    def from_audio_file(audio_filepath: str):
        audio_path = Path(audio_filepath)
        if not audio_path.exists() or not audio_path.is_file():
            return None
        
        audio = File(audio_path)
        if not audio:
            return None
        
        title:str|None = audio.get('TITLE',[None])[0] if 'TITLE' in audio else None
        artist:str|None = audio.get('ARTIST',[None])[0] if 'ARTIST' in audio else None
        album:str|None = audio.get('ALBUM',[None])[0] if 'ALBUM' in audio else None
        genre:list[str]|None = audio.get('GENRE',[None]) if 'GENRE' in audio else None

        if not title and not artist and not album and not genre:
            return None

        # Some common approaches to multiple genres include
        # separating with "/" or ";;", so split
        genres:list[str] = []
        if genre is not None:
            for g in genre:
                if "/" in g:
                    genres += g.split("/")
                elif ";" in genre:
                    genres += g.split(";")
                else:
                    genres.append(g)

        genres = [g.strip() for g in genres if g]


        audio_metadata = AudioMetadata(title=title, artist=artist, album=album, genres=genres)
        return audio_metadata

        
