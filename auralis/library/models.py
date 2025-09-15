# -*- coding: utf-8 -*-

"""
Auralis Library Database Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Database models for music library management
Integrated from existing library infrastructure

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Table, Boolean, func, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pathlib import Path

Base = declarative_base()

# Association tables for many-to-many relationships
track_artist = Table(
    'track_artist', Base.metadata,
    Column('track_id', Integer, ForeignKey('tracks.id')),
    Column('artist_id', Integer, ForeignKey('artists.id'))
)

track_genre = Table(
    'track_genre', Base.metadata,
    Column('track_id', Integer, ForeignKey('tracks.id')),
    Column('genre_id', Integer, ForeignKey('genres.id'))
)

track_playlist = Table(
    'track_playlist', Base.metadata,
    Column('track_id', Integer, ForeignKey('tracks.id')),
    Column('playlist_id', Integer, ForeignKey('playlists.id'))
)


class TimestampMixin:
    """Mixin to add creation and modification timestamps."""
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Track(Base, TimestampMixin):
    """Model for audio tracks."""
    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    filepath = Column(String, nullable=False, unique=True)
    duration = Column(Float)
    sample_rate = Column(Integer)
    bit_depth = Column(Integer)
    channels = Column(Integer)
    format = Column(String)
    filesize = Column(Integer)

    # Audio analysis data
    peak_level = Column(Float)
    rms_level = Column(Float)
    dr_rating = Column(Float)  # Dynamic Range rating
    lufs_level = Column(Float)  # LUFS loudness

    # Auralis-specific analysis
    mastering_quality = Column(Float)  # Quality score 0-1
    recommended_reference = Column(String)  # Best reference track path
    processing_profile = Column(String)  # Optimal mastering profile

    # Metadata
    album_id = Column(Integer, ForeignKey('albums.id'))
    track_number = Column(Integer)
    disc_number = Column(Integer)
    year = Column(Integer)
    comments = Column(Text)

    # Playback statistics
    play_count = Column(Integer, default=0)
    last_played = Column(DateTime)
    skip_count = Column(Integer, default=0)
    favorite = Column(Boolean, default=False)

    # Relationships
    album = relationship("Album", back_populates="tracks")
    artists = relationship("Artist", secondary=track_artist, back_populates="tracks")
    genres = relationship("Genre", secondary=track_genre, back_populates="tracks")
    playlists = relationship("Playlist", secondary=track_playlist, back_populates="tracks")

    def to_dict(self) -> dict:
        """Convert track to dictionary for API/GUI use"""
        try:
            # Safe access to relationship attributes
            album_title = None
            try:
                album_title = self.album.title if self.album else None
            except:
                album_title = None

            artist_names = []
            try:
                artist_names = [artist.name for artist in self.artists]
            except:
                artist_names = []

            genre_names = []
            try:
                genre_names = [genre.name for genre in self.genres]
            except:
                genre_names = []

            return {
                'id': self.id,
                'title': self.title,
                'filepath': self.filepath,
                'duration': self.duration,
                'sample_rate': self.sample_rate,
                'bit_depth': self.bit_depth,
                'channels': self.channels,
                'format': self.format,
                'filesize': self.filesize,
                'peak_level': self.peak_level,
                'rms_level': self.rms_level,
                'dr_rating': self.dr_rating,
                'lufs_level': self.lufs_level,
                'mastering_quality': self.mastering_quality,
                'recommended_reference': self.recommended_reference,
                'processing_profile': self.processing_profile,
                'album_id': self.album_id,
                'track_number': self.track_number,
                'disc_number': self.disc_number,
                'year': self.year,
                'comments': self.comments,
                'play_count': self.play_count,
                'last_played': self.last_played.isoformat() if self.last_played else None,
                'skip_count': self.skip_count,
                'favorite': self.favorite,
                'album': album_title,
                'artists': artist_names,
                'genres': genre_names,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            }
        except Exception as e:
            # Fallback for detached objects
            return {
                'id': getattr(self, 'id', None),
                'title': getattr(self, 'title', 'Unknown'),
                'filepath': getattr(self, 'filepath', ''),
                'duration': getattr(self, 'duration', 0),
                'sample_rate': getattr(self, 'sample_rate', 0),
                'channels': getattr(self, 'channels', 0),
                'format': getattr(self, 'format', 'Unknown'),
                'play_count': getattr(self, 'play_count', 0),
                'favorite': getattr(self, 'favorite', False),
                'album': None,
                'artists': [],
                'genres': [],
            }


class Album(Base, TimestampMixin):
    """Model for albums."""
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    artist_id = Column(Integer, ForeignKey('artists.id'))
    year = Column(Integer)
    total_tracks = Column(Integer)
    total_discs = Column(Integer)

    # Album-level analysis
    avg_dr_rating = Column(Float)
    avg_lufs = Column(Float)
    mastering_consistency = Column(Float)  # How consistent the mastering is across tracks

    # Relationships
    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")

    def to_dict(self) -> dict:
        """Convert album to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'artist_id': self.artist_id,
            'year': self.year,
            'total_tracks': self.total_tracks,
            'total_discs': self.total_discs,
            'avg_dr_rating': self.avg_dr_rating,
            'avg_lufs': self.avg_lufs,
            'mastering_consistency': self.mastering_consistency,
            'artist': self.artist.name if self.artist else None,
            'track_count': len(self.tracks),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Artist(Base, TimestampMixin):
    """Model for artists."""
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    # Artist statistics
    total_plays = Column(Integer, default=0)
    avg_mastering_quality = Column(Float)

    # Relationships
    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", secondary=track_artist, back_populates="artists")

    def to_dict(self) -> dict:
        """Convert artist to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'total_plays': self.total_plays,
            'avg_mastering_quality': self.avg_mastering_quality,
            'album_count': len(self.albums),
            'track_count': len(self.tracks),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Genre(Base, TimestampMixin):
    """Model for music genres."""
    __tablename__ = 'genres'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    # Genre characteristics for auto-mastering
    preferred_profile = Column(String, default='balanced')  # warm, bright, punchy, balanced
    typical_dr_range = Column(String)  # "8-12" for example
    typical_lufs_range = Column(String)  # "-14 to -10" for example

    # Relationships
    tracks = relationship("Track", secondary=track_genre, back_populates="genres")

    def to_dict(self) -> dict:
        """Convert genre to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'preferred_profile': self.preferred_profile,
            'typical_dr_range': self.typical_dr_range,
            'typical_lufs_range': self.typical_lufs_range,
            'track_count': len(self.tracks),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Playlist(Base, TimestampMixin):
    """Model for playlists."""
    __tablename__ = 'playlists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_smart = Column(Boolean, default=False)
    smart_criteria = Column(Text)  # JSON string for smart playlist rules

    # Playlist-level mastering settings
    auto_master_enabled = Column(Boolean, default=True)
    mastering_profile = Column(String, default='balanced')
    normalize_levels = Column(Boolean, default=True)

    # Relationships
    tracks = relationship("Track", secondary=track_playlist, back_populates="playlists")

    def to_dict(self) -> dict:
        """Convert playlist to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_smart': self.is_smart,
            'smart_criteria': self.smart_criteria,
            'auto_master_enabled': self.auto_master_enabled,
            'mastering_profile': self.mastering_profile,
            'normalize_levels': self.normalize_levels,
            'track_count': len(self.tracks),
            'total_duration': sum(track.duration for track in self.tracks if track.duration),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class LibraryStats(Base, TimestampMixin):
    """Model for library-wide statistics."""
    __tablename__ = 'library_stats'

    id = Column(Integer, primary_key=True)
    total_tracks = Column(Integer, default=0)
    total_artists = Column(Integer, default=0)
    total_albums = Column(Integer, default=0)
    total_genres = Column(Integer, default=0)
    total_playlists = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)  # Total duration in seconds
    total_filesize = Column(Integer, default=0)  # Total filesize in bytes

    # Quality statistics
    avg_dr_rating = Column(Float)
    avg_lufs = Column(Float)
    avg_mastering_quality = Column(Float)

    # Last scan information
    last_scan_date = Column(DateTime)
    last_scan_duration = Column(Float)  # Scan duration in seconds
    files_scanned = Column(Integer, default=0)
    new_files_found = Column(Integer, default=0)

    def to_dict(self) -> dict:
        """Convert stats to dictionary"""
        return {
            'id': self.id,
            'total_tracks': self.total_tracks,
            'total_artists': self.total_artists,
            'total_albums': self.total_albums,
            'total_genres': self.total_genres,
            'total_playlists': self.total_playlists,
            'total_duration': self.total_duration,
            'total_duration_formatted': f"{self.total_duration // 3600:.0f}h {(self.total_duration % 3600) // 60:.0f}m",
            'total_filesize': self.total_filesize,
            'total_filesize_gb': self.total_filesize / (1024**3) if self.total_filesize else 0,
            'avg_dr_rating': self.avg_dr_rating,
            'avg_lufs': self.avg_lufs,
            'avg_mastering_quality': self.avg_mastering_quality,
            'last_scan_date': self.last_scan_date.isoformat() if self.last_scan_date else None,
            'last_scan_duration': self.last_scan_duration,
            'files_scanned': self.files_scanned,
            'new_files_found': self.new_files_found,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }