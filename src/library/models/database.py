"""
Database models for the music library.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Table, Boolean, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.declarative import declared_attr
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
    filepath = Column(String, nullable=False)
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
    
    # Metadata
    album_id = Column(Integer, ForeignKey('albums.id'))
    track_number = Column(Integer)
    disc_number = Column(Integer)
    year = Column(Integer)
    comments = Column(String)
    
    # Relationships
    album = relationship("Album", back_populates="tracks")
    artists = relationship("Artist", secondary=track_artist, back_populates="tracks")
    genres = relationship("Genre", secondary=track_genre, back_populates="tracks")
    playlists = relationship("Playlist", secondary=track_playlist, back_populates="tracks")

class Album(Base, TimestampMixin):
    """Model for albums."""
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    artist_id = Column(Integer, ForeignKey('artists.id'))
    year = Column(Integer)
    total_tracks = Column(Integer)
    total_discs = Column(Integer)
    
    # Relationships
    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")

class Artist(Base, TimestampMixin):
    """Model for artists."""
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", secondary=track_artist, back_populates="artists")

class Genre(Base, TimestampMixin):
    """Model for music genres."""
    __tablename__ = 'genres'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    tracks = relationship("Track", secondary=track_genre, back_populates="genres")

class Playlist(Base, TimestampMixin):
    """Model for playlists."""
    __tablename__ = 'playlists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    is_smart = Column(Boolean, default=False)
    smart_rules = Column(String)  # JSON string for smart playlist rules
    
    # Relationships
    tracks = relationship("Track", secondary=track_playlist, back_populates="playlists")

class LibraryStatistics(Base):
    """Model for library statistics."""
    __tablename__ = 'library_statistics'

    id = Column(Integer, primary_key=True)
    total_tracks = Column(Integer, default=0)
    total_albums = Column(Integer, default=0)
    total_artists = Column(Integer, default=0)
    total_playlists = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)  # In seconds
    total_size = Column(Integer, default=0)  # In bytes
    last_scan = Column(DateTime)

class Database:
    """Database management class."""
    
    def __init__(self, db_path: str = "library.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get a new database session."""
        return self.Session()
        
    def initialize(self):
        """Initialize the database."""
        self.create_tables()
        
        # Create initial statistics record
        session = self.get_session()
        if not session.query(LibraryStatistics).first():
            session.add(LibraryStatistics())
            session.commit()
        session.close()

class LibraryManager:
    """High-level library management class."""
    
    def __init__(self, db_path: str = "library.db"):
        """Initialize library manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db = Database(db_path)
        self.db.initialize()
        
    def add_track(self, filepath: str, metadata: dict) -> Track:
        """Add a track to the library.
        
        Args:
            filepath: Path to audio file
            metadata: Track metadata dictionary
            
        Returns:
            Created Track instance
        """
        session = self.db.get_session()
        
        try:
            # Create or get artists
            artists = []
            for artist_name in metadata.get('artists', []):
                artist = session.query(Artist).filter_by(name=artist_name).first()
                if not artist:
                    artist = Artist(name=artist_name)
                    session.add(artist)
                artists.append(artist)
            
            # Create or get album
            album = None
            if 'album' in metadata:
                album = session.query(Album).filter_by(
                    title=metadata['album'],
                    artist_id=artists[0].id if artists else None
                ).first()
                if not album:
                    album = Album(
                        title=metadata['album'],
                        artist=artists[0] if artists else None,
                        year=metadata.get('year'),
                        total_tracks=metadata.get('total_tracks'),
                        total_discs=metadata.get('total_discs')
                    )
                    session.add(album)
            
            # Create or get genres
            genres = []
            for genre_name in metadata.get('genres', []):
                genre = session.query(Genre).filter_by(name=genre_name).first()
                if not genre:
                    genre = Genre(name=genre_name)
                    session.add(genre)
                genres.append(genre)
            
            # Create track
            track = Track(
                title=metadata.get('title', Path(filepath).stem),
                filepath=str(Path(filepath).absolute()),
                duration=metadata.get('duration'),
                sample_rate=metadata.get('sample_rate'),
                bit_depth=metadata.get('bit_depth'),
                channels=metadata.get('channels'),
                format=metadata.get('format'),
                filesize=metadata.get('filesize'),
                album=album,
                track_number=metadata.get('track_number'),
                disc_number=metadata.get('disc_number'),
                year=metadata.get('year'),
                artists=artists,
                genres=genres
            )
            
            session.add(track)
            session.commit()
            
            # Explicitly load relationships before detaching
            session.refresh(track)
            # Access each relationship to ensure they're loaded
            track.artists
            track.genres
            track.album
            
            # Now detach the fully-loaded instance
            session.expunge(track)
            return track
            
        finally:
            session.close()
            
    def remove_track(self, track_id: int):
        """Remove a track from the library.
        
        Args:
            track_id: Track ID to remove
        """
        session = self.db.get_session()
        try:
            track = session.query(Track).get(track_id)
            if track:
                session.delete(track)
                session.commit()
        finally:
            session.close()
            
    def update_statistics(self):
        """Update library statistics."""
        session = self.db.get_session()
        try:
            stats = session.query(LibraryStatistics).first()
            if not stats:
                stats = LibraryStatistics()
                session.add(stats)
            
            stats.total_tracks = session.query(Track).count()
            stats.total_albums = session.query(Album).count()
            stats.total_artists = session.query(Artist).count()
            stats.total_playlists = session.query(Playlist).count()
            
            # Calculate total duration and size
            duration_size = session.query(
                func.sum(Track.duration),
                func.sum(Track.filesize)
            ).first()
            
            stats.total_duration = duration_size[0] or 0.0
            stats.total_size = duration_size[1] or 0
            stats.last_scan = datetime.utcnow()
            
            session.commit()
            
        finally:
            session.close()