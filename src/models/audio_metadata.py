from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from mutagen import File

@dataclass
class AudioMetadata:

    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    genre: Optional[str]

    @staticmethod
    def from_audio_file(audio_filepath: str):
        audio_path = Path(audio_filepath)
        if not audio_path.exists() or not audio_path.is_file():
            return None
        
        audio = File(audio_path)
        if not audio:
            return None
        
        title = audio.get('TITLE',[None])[0] if 'TITLE' in audio else None
        artist = audio.get('ARTIST',[None])[0] if 'ARTIST' in audio else None
        album = audio.get('ALBUM',[None])[0] if 'ALBUM' in audio else None
        genre = audio.get('GENRE',[None])[0] if 'GENRE' in audio else None

        if not title and not artist and not album and not genre:
            return None
        
        audio_metadata = AudioMetadata(title=title, artist=artist, album=album, genre=genre)
        return audio_metadata

        
