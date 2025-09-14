"""
Audio file metadata reader module.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
import audioread
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.aiff import AIFF

class MetadataReader:
    """Audio file metadata reader."""
    
    SUPPORTED_FORMATS = {
        '.mp3': MP3,
        '.flac': FLAC,
        '.wav': WAVE,
        '.aiff': AIFF
    }
    
    @classmethod
    def read_metadata(cls, filepath: str) -> Dict[str, Any]:
        """Read metadata from audio file.
        
        Args:
            filepath: Path to audio file
            
        Returns:
            Dictionary containing metadata
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        # Get basic file info
        metadata = {
            'filepath': str(path.absolute()),
            'filename': path.name,
            'format': path.suffix.lower()[1:],
            'filesize': path.stat().st_size
        }
        
        # Read audio properties
        try:
            with audioread.audio_open(str(path)) as audio:
                metadata.update({
                    'duration': audio.duration,
                    'channels': audio.channels,
                    'sample_rate': audio.samplerate
                })
        except Exception as e:
            print(f"Warning: Could not read audio properties from {path.name}: {e}")
        
        # Read tag metadata
        try:
            format_class = cls.SUPPORTED_FORMATS.get(path.suffix.lower())
            if format_class:
                audio = format_class(str(path))
                
                # Handle MP3 files with ID3 tags
                if isinstance(audio, MP3):
                    if audio.tags is None:
                        audio.add_tags()
                    id3 = EasyID3(str(path))
                    metadata.update(cls._parse_id3_tags(id3))
                else:
                    metadata.update(cls._parse_general_tags(audio))
                
                # Add audio format specific info
                if hasattr(audio.info, 'bits_per_sample'):
                    metadata['bit_depth'] = audio.info.bits_per_sample
                
        except Exception as e:
            print(f"Warning: Could not read metadata tags from {path.name}: {e}")
        
        return metadata
    
    @staticmethod
    def _parse_id3_tags(tags: EasyID3) -> Dict[str, Any]:
        """Parse ID3 tags from MP3 file.
        
        Args:
            tags: EasyID3 tags object
            
        Returns:
            Dictionary of parsed tags
        """
        metadata = {}
        
        # Basic tags
        if 'title' in tags:
            metadata['title'] = tags['title'][0]
        if 'artist' in tags:
            metadata['artists'] = tags['artist']
        if 'album' in tags:
            metadata['album'] = tags['album'][0]
        if 'genre' in tags:
            metadata['genres'] = tags['genre']
        if 'date' in tags:
            try:
                metadata['year'] = int(tags['date'][0].split('-')[0])
            except (ValueError, IndexError):
                pass
        
        # Track numbers
        if 'tracknumber' in tags:
            try:
                track_info = tags['tracknumber'][0].split('/')
                metadata['track_number'] = int(track_info[0])
                if len(track_info) > 1:
                    metadata['total_tracks'] = int(track_info[1])
            except (ValueError, IndexError):
                pass
        
        # Disc numbers
        if 'discnumber' in tags:
            try:
                disc_info = tags['discnumber'][0].split('/')
                metadata['disc_number'] = int(disc_info[0])
                if len(disc_info) > 1:
                    metadata['total_discs'] = int(disc_info[1])
            except (ValueError, IndexError):
                pass
        
        return metadata
    
    @staticmethod
    def _parse_general_tags(audio: mutagen.FileType) -> Dict[str, Any]:
        """Parse tags from general audio file.
        
        Args:
            audio: Mutagen FileType object
            
        Returns:
            Dictionary of parsed tags
        """
        metadata = {}
        
        # Map common tag names
        tag_mapping = {
            'title': ['title', 'TITLE'],
            'artists': ['artist', 'ARTIST', 'ARTISTS'],
            'album': ['album', 'ALBUM'],
            'genres': ['genre', 'GENRE'],
            'year': ['year', 'YEAR', 'DATE'],
            'track_number': ['tracknumber', 'TRACKNUMBER'],
            'total_tracks': ['tracktotal', 'TRACKTOTAL'],
            'disc_number': ['discnumber', 'DISCNUMBER'],
            'total_discs': ['disctotal', 'DISCTOTAL']
        }
        
        for meta_key, tag_keys in tag_mapping.items():
            for tag_key in tag_keys:
                if tag_key in audio.tags:
                    value = audio.tags[tag_key][0]
                    
                    # Handle different tag types
                    if meta_key in ['artists', 'genres']:
                        if isinstance(value, str):
                            metadata[meta_key] = [v.strip() for v in value.split(';')]
                        else:
                            metadata[meta_key] = [str(value)]
                    elif meta_key in ['year', 'track_number', 'total_tracks', 'disc_number', 'total_discs']:
                        try:
                            metadata[meta_key] = int(str(value).split('-')[0])
                        except (ValueError, IndexError):
                            pass
                    else:
                        metadata[meta_key] = str(value)
                    
                    break
        
        return metadata