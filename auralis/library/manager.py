# -*- coding: utf-8 -*-

"""
Auralis Library Manager
~~~~~~~~~~~~~~~~~~~~~~

High-level library management and database operations

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import create_engine, func, or_, and_
from sqlalchemy.orm import sessionmaker, Session, selectinload
from sqlalchemy.exc import IntegrityError

from .models import Base, Track, Album, Artist, Genre, Playlist, LibraryStats
from ..utils.logging import info, warning, error, debug


class LibraryManager:
    """
    High-level library management system for Auralis

    Provides API for:
    - Database operations
    - Track/playlist management
    - Search and filtering
    - Statistics and analysis
    - Integration with audio player
    """

    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize library manager

        Args:
            database_path: Path to SQLite database file
        """
        if database_path is None:
            # Default to user's music directory
            music_dir = Path.home() / "Music" / "Auralis"
            music_dir.mkdir(parents=True, exist_ok=True)
            database_path = str(music_dir / "auralis_library.db")

        self.database_path = database_path
        self.engine = create_engine(f"sqlite:///{database_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        info(f"Auralis Library Manager initialized: {database_path}")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def add_track(self, track_info: Dict[str, Any]) -> Optional[Track]:
        """
        Add a track to the library

        Args:
            track_info: Dictionary with track information

        Returns:
            Track object if successful, None if failed
        """
        session = self.get_session()
        try:
            # Check if track already exists
            existing = session.query(Track).filter(Track.filepath == track_info['filepath']).first()
            if existing:
                warning(f"Track already exists: {track_info['filepath']}")
                return existing

            # Get or create artist(s)
            artists = []
            for artist_name in track_info.get('artists', []):
                artist = session.query(Artist).filter(Artist.name == artist_name).first()
                if not artist:
                    artist = Artist(name=artist_name)
                    session.add(artist)
                artists.append(artist)

            # Get or create album
            album = None
            if track_info.get('album'):
                album = session.query(Album).filter(
                    Album.title == track_info['album'],
                    Album.artist_id == artists[0].id if artists else None
                ).first()
                if not album and artists:
                    album = Album(
                        title=track_info['album'],
                        artist_id=artists[0].id,
                        year=track_info.get('year')
                    )
                    session.add(album)

            # Get or create genres
            genres = []
            for genre_name in track_info.get('genres', []):
                genre = session.query(Genre).filter(Genre.name == genre_name).first()
                if not genre:
                    genre = Genre(name=genre_name)
                    session.add(genre)
                genres.append(genre)

            # Create track
            track = Track(
                title=track_info.get('title', 'Unknown'),
                filepath=track_info['filepath'],
                duration=track_info.get('duration'),
                sample_rate=track_info.get('sample_rate'),
                bit_depth=track_info.get('bit_depth'),
                channels=track_info.get('channels'),
                format=track_info.get('format'),
                filesize=track_info.get('filesize'),
                peak_level=track_info.get('peak_level'),
                rms_level=track_info.get('rms_level'),
                dr_rating=track_info.get('dr_rating'),
                lufs_level=track_info.get('lufs_level'),
                album=album,
                track_number=track_info.get('track_number'),
                disc_number=track_info.get('disc_number'),
                year=track_info.get('year'),
                comments=track_info.get('comments'),
            )

            # Add relationships
            track.artists = artists
            track.genres = genres

            session.add(track)
            session.commit()

            info(f"Added track: {track.title}")
            return track

        except Exception as e:
            session.rollback()
            error(f"Failed to add track: {e}")
            return None
        finally:
            session.close()

    def get_track(self, track_id: int) -> Optional[Track]:
        """Get track by ID"""
        session = self.get_session()
        try:
            return session.query(Track).filter(Track.id == track_id).first()
        finally:
            session.close()

    def get_track_by_path(self, filepath: str) -> Optional[Track]:
        """Get track by file path"""
        session = self.get_session()
        try:
            return session.query(Track).filter(Track.filepath == filepath).first()
        finally:
            session.close()

    def search_tracks(self, query: str, limit: int = 50) -> List[Track]:
        """
        Search tracks by title, artist, album, or genre

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching tracks
        """
        session = self.get_session()
        try:
            search_term = f"%{query}%"
            results = session.query(Track).join(Track.artists).join(Track.album, isouter=True).filter(
                or_(
                    Track.title.ilike(search_term),
                    Artist.name.ilike(search_term),
                    Album.title.ilike(search_term)
                )
            ).limit(limit).all()

            return results
        finally:
            session.close()

    def get_tracks_by_genre(self, genre_name: str, limit: int = 100) -> List[Track]:
        """Get tracks by genre"""
        session = self.get_session()
        try:
            genre = session.query(Genre).filter(Genre.name == genre_name).first()
            if not genre:
                return []
            return genre.tracks[:limit]
        finally:
            session.close()

    def get_tracks_by_artist(self, artist_name: str, limit: int = 100) -> List[Track]:
        """Get tracks by artist"""
        session = self.get_session()
        try:
            artist = session.query(Artist).filter(Artist.name == artist_name).first()
            if not artist:
                return []
            return artist.tracks[:limit]
        finally:
            session.close()

    def get_recent_tracks(self, limit: int = 50) -> List[Track]:
        """Get recently added tracks"""
        session = self.get_session()
        try:
            return session.query(Track).order_by(Track.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def get_popular_tracks(self, limit: int = 50) -> List[Track]:
        """Get tracks sorted by play count"""
        session = self.get_session()
        try:
            return session.query(Track).order_by(Track.play_count.desc()).limit(limit).all()
        finally:
            session.close()

    def get_favorite_tracks(self, limit: int = 50) -> List[Track]:
        """Get favorite tracks"""
        session = self.get_session()
        try:
            return session.query(Track).filter(Track.favorite == True).order_by(Track.last_played.desc()).limit(limit).all()
        finally:
            session.close()

    def create_playlist(self, name: str, description: str = "", track_ids: List[int] = None) -> Optional[Playlist]:
        """
        Create a new playlist

        Args:
            name: Playlist name
            description: Playlist description
            track_ids: List of track IDs to add

        Returns:
            Playlist object if successful
        """
        session = self.get_session()
        try:
            playlist = Playlist(name=name, description=description)

            # Add tracks if provided
            if track_ids:
                tracks = session.query(Track).filter(Track.id.in_(track_ids)).all()
                playlist.tracks = tracks

            session.add(playlist)
            session.commit()

            # Get the playlist with eager loading
            playlist = session.query(Playlist).options(
                selectinload(Playlist.tracks).selectinload(Track.artists),
                selectinload(Playlist.tracks).selectinload(Track.genres),
                selectinload(Playlist.tracks).selectinload(Track.album)
            ).filter_by(id=playlist.id).first()

            # Expunge from session to avoid DetachedInstanceError
            session.expunge(playlist)

            info(f"Created playlist: {name}")
            return playlist

        except Exception as e:
            session.rollback()
            error(f"Failed to create playlist: {e}")
            return None
        finally:
            session.close()

    def get_playlist(self, playlist_id: int) -> Optional[Playlist]:
        """Get playlist by ID"""
        session = self.get_session()
        try:
            return session.query(Playlist).filter(Playlist.id == playlist_id).first()
        finally:
            session.close()

    def get_all_playlists(self) -> List[Playlist]:
        """Get all playlists"""
        session = self.get_session()
        try:
            return session.query(Playlist).order_by(Playlist.name).all()
        finally:
            session.close()

    def add_track_to_playlist(self, playlist_id: int, track_id: int) -> bool:
        """Add track to playlist"""
        session = self.get_session()
        try:
            playlist = session.query(Playlist).filter(Playlist.id == playlist_id).first()
            track = session.query(Track).filter(Track.id == track_id).first()

            if not playlist or not track:
                return False

            if track not in playlist.tracks:
                playlist.tracks.append(track)
                session.commit()

            return True

        except Exception as e:
            session.rollback()
            error(f"Failed to add track to playlist: {e}")
            return False
        finally:
            session.close()

    def record_track_play(self, track_id: int):
        """Record that a track was played"""
        session = self.get_session()
        try:
            track = session.query(Track).filter(Track.id == track_id).first()
            if track:
                track.play_count = (track.play_count or 0) + 1
                track.last_played = datetime.utcnow()
                session.commit()
                debug(f"Recorded play for track: {track.title}")

        except Exception as e:
            session.rollback()
            error(f"Failed to record track play: {e}")
        finally:
            session.close()

    def set_track_favorite(self, track_id: int, favorite: bool = True):
        """Set track favorite status"""
        session = self.get_session()
        try:
            track = session.query(Track).filter(Track.id == track_id).first()
            if track:
                track.favorite = favorite
                session.commit()
                debug(f"Set track {track.title} favorite: {favorite}")
                return True
            return False

        except Exception as e:
            session.rollback()
            error(f"Failed to set track favorite: {e}")
            return False
        finally:
            session.close()

    def find_reference_tracks(self, track: Track, limit: int = 5) -> List[Track]:
        """
        Find suitable reference tracks for a given track
        Based on genre, artist, and audio characteristics

        Args:
            track: Target track to find references for
            limit: Maximum number of references to return

        Returns:
            List of suitable reference tracks
        """
        session = self.get_session()
        try:
            # Priority 1: Same genre, different artist, good mastering quality
            references = []

            # Same genre references
            if track.genres:
                genre_tracks = session.query(Track).join(Track.genres).filter(
                    Genre.name.in_([g.name for g in track.genres]),
                    Track.id != track.id,
                    Track.mastering_quality.isnot(None),
                    Track.mastering_quality > 0.7  # Good mastering quality
                ).order_by(Track.mastering_quality.desc()).limit(limit).all()
                references.extend(genre_tracks)

            # Fill remaining slots with high-quality tracks from any genre
            if len(references) < limit:
                remaining = limit - len(references)
                quality_tracks = session.query(Track).filter(
                    Track.id != track.id,
                    Track.mastering_quality.isnot(None),
                    Track.mastering_quality > 0.8
                ).order_by(Track.mastering_quality.desc()).limit(remaining).all()

                # Add tracks not already in references
                for qt in quality_tracks:
                    if qt not in references:
                        references.append(qt)
                        if len(references) >= limit:
                            break

            return references

        finally:
            session.close()

    def get_library_stats(self) -> Dict[str, Any]:
        """Get comprehensive library statistics"""
        session = self.get_session()
        try:
            # Get or create stats record
            stats = session.query(LibraryStats).first()
            if not stats:
                stats = LibraryStats()
                session.add(stats)

            # Update stats
            stats.total_tracks = session.query(Track).count()
            stats.total_artists = session.query(Artist).count()
            stats.total_albums = session.query(Album).count()
            stats.total_genres = session.query(Genre).count()
            stats.total_playlists = session.query(Playlist).count()

            # Calculate totals
            duration_sum = session.query(func.sum(Track.duration)).scalar() or 0
            filesize_sum = session.query(func.sum(Track.filesize)).scalar() or 0
            stats.total_duration = duration_sum
            stats.total_filesize = filesize_sum

            # Calculate averages
            avg_dr = session.query(func.avg(Track.dr_rating)).filter(Track.dr_rating.isnot(None)).scalar()
            avg_lufs = session.query(func.avg(Track.lufs_level)).filter(Track.lufs_level.isnot(None)).scalar()
            avg_quality = session.query(func.avg(Track.mastering_quality)).filter(Track.mastering_quality.isnot(None)).scalar()

            stats.avg_dr_rating = avg_dr
            stats.avg_lufs = avg_lufs
            stats.avg_mastering_quality = avg_quality

            session.commit()
            return stats.to_dict()

        finally:
            session.close()

    def get_recommendations(self, track: Track, limit: int = 10) -> List[Track]:
        """
        Get track recommendations based on listening history and preferences

        Args:
            track: Track to base recommendations on
            limit: Maximum number of recommendations

        Returns:
            List of recommended tracks
        """
        session = self.get_session()
        try:
            recommendations = []

            # Same artist recommendations
            if track.artists:
                artist_tracks = session.query(Track).join(Track.artists).filter(
                    Artist.name.in_([a.name for a in track.artists]),
                    Track.id != track.id
                ).order_by(Track.play_count.desc()).limit(limit // 2).all()
                recommendations.extend(artist_tracks)

            # Same genre recommendations
            if track.genres and len(recommendations) < limit:
                remaining = limit - len(recommendations)
                genre_tracks = session.query(Track).join(Track.genres).filter(
                    Genre.name.in_([g.name for g in track.genres]),
                    Track.id != track.id
                ).order_by(Track.play_count.desc()).limit(remaining).all()

                # Add tracks not already in recommendations
                for gt in genre_tracks:
                    if gt not in recommendations:
                        recommendations.append(gt)
                        if len(recommendations) >= limit:
                            break

            return recommendations[:limit]

        finally:
            session.close()

    def cleanup_library(self):
        """Clean up library by removing tracks with missing files"""
        session = self.get_session()
        try:
            tracks = session.query(Track).all()
            removed_count = 0

            for track in tracks:
                if not os.path.exists(track.filepath):
                    session.delete(track)
                    removed_count += 1

            session.commit()
            info(f"Library cleanup: removed {removed_count} tracks with missing files")
            return removed_count

        except Exception as e:
            session.rollback()
            error(f"Library cleanup failed: {e}")
            return 0
        finally:
            session.close()

    def get_track_by_filepath(self, filepath: str) -> Optional[Track]:
        """
        Get track by file path

        Args:
            filepath: Full path to audio file

        Returns:
            Track object if found, None otherwise
        """
        session = self.get_session()
        try:
            track = session.query(Track).filter_by(filepath=filepath).first()
            return track
        finally:
            session.close()

    def update_track_by_filepath(self, filepath: str, track_info: Dict[str, Any]) -> Optional[Track]:
        """
        Update existing track by filepath

        Args:
            filepath: Path to audio file
            track_info: Updated track information

        Returns:
            Updated Track object if successful, None otherwise
        """
        session = self.get_session()
        try:
            track = session.query(Track).filter_by(filepath=filepath).first()
            if not track:
                return None

            # Update track fields
            for key, value in track_info.items():
                if key == 'artists':
                    # Handle artists separately
                    self._update_track_artists(session, track, value)
                elif key == 'genres':
                    # Handle genres separately
                    self._update_track_genres(session, track, value)
                elif key == 'album':
                    # Handle album separately
                    track.album = self._get_or_create_album(session, value, track_info.get('artists', []))
                elif hasattr(track, key):
                    setattr(track, key, value)

            session.commit()
            info(f"Updated track: {track.title}")
            return track

        except Exception as e:
            session.rollback()
            error(f"Failed to update track {filepath}: {e}")
            return None
        finally:
            session.close()

    def _update_track_artists(self, session: Session, track: Track, artist_names: List[str]):
        """Update track artists"""
        # Clear existing artists
        track.artists.clear()

        # Add new artists
        for artist_name in artist_names:
            artist = self._get_or_create_artist(session, artist_name)
            track.artists.append(artist)

    def _update_track_genres(self, session: Session, track: Track, genre_names: List[str]):
        """Update track genres"""
        # Clear existing genres
        track.genres.clear()

        # Add new genres
        for genre_name in genre_names:
            genre = self._get_or_create_genre(session, genre_name)
            track.genres.append(genre)

    def scan_directories(self, directories: List[str], **kwargs):
        """
        Scan directories for audio files and add to library

        Args:
            directories: List of directory paths to scan
            **kwargs: Additional arguments for scanner

        Returns:
            ScanResult object with scan statistics
        """
        from .scanner import LibraryScanner

        scanner = LibraryScanner(self)
        return scanner.scan_directories(directories, **kwargs)

    def scan_single_directory(self, directory: str, **kwargs):
        """Scan a single directory for audio files"""
        return self.scan_directories([directory], **kwargs)

    def get_all_playlists(self) -> List[Playlist]:
        """
        Get all playlists in the library

        Returns:
            List of Playlist objects
        """
        session = self.get_session()
        try:
            playlists = session.query(Playlist).options(
                selectinload(Playlist.tracks).selectinload(Track.artists),
                selectinload(Playlist.tracks).selectinload(Track.genres),
                selectinload(Playlist.tracks).selectinload(Track.album)
            ).order_by(Playlist.name).all()

            # Expunge all playlists from session to avoid DetachedInstanceError
            for playlist in playlists:
                session.expunge(playlist)
            return playlists
        finally:
            session.close()

    def get_playlist(self, playlist_id: int) -> Optional[Playlist]:
        """
        Get playlist by ID

        Args:
            playlist_id: Playlist ID

        Returns:
            Playlist object if found, None otherwise
        """
        session = self.get_session()
        try:
            playlist = session.query(Playlist).options(
                selectinload(Playlist.tracks).selectinload(Track.artists),
                selectinload(Playlist.tracks).selectinload(Track.genres),
                selectinload(Playlist.tracks).selectinload(Track.album)
            ).filter_by(id=playlist_id).first()

            if playlist:
                # Expunge from session to avoid DetachedInstanceError
                session.expunge(playlist)
            return playlist
        finally:
            session.close()

    def update_playlist(self, playlist_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update playlist information

        Args:
            playlist_id: Playlist ID
            update_data: Dictionary with fields to update

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            if not playlist:
                return False

            # Update fields
            for key, value in update_data.items():
                if hasattr(playlist, key):
                    setattr(playlist, key, value)

            session.commit()
            info(f"Updated playlist: {playlist.name}")
            return True

        except Exception as e:
            session.rollback()
            error(f"Failed to update playlist {playlist_id}: {e}")
            return False
        finally:
            session.close()

    def delete_playlist(self, playlist_id: int) -> bool:
        """
        Delete a playlist

        Args:
            playlist_id: Playlist ID

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            if not playlist:
                return False

            playlist_name = playlist.name
            session.delete(playlist)
            session.commit()
            info(f"Deleted playlist: {playlist_name}")
            return True

        except Exception as e:
            session.rollback()
            error(f"Failed to delete playlist {playlist_id}: {e}")
            return False
        finally:
            session.close()

    def add_track_to_playlist(self, playlist_id: int, track_id: int) -> bool:
        """
        Add a track to a playlist

        Args:
            playlist_id: Playlist ID
            track_id: Track ID

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            track = session.query(Track).filter_by(id=track_id).first()

            if not playlist or not track:
                return False

            # Check if track is already in playlist
            if track not in playlist.tracks:
                playlist.tracks.append(track)
                session.commit()
                info(f"Added track '{track.title}' to playlist '{playlist.name}'")

            return True

        except Exception as e:
            session.rollback()
            error(f"Failed to add track {track_id} to playlist {playlist_id}: {e}")
            return False
        finally:
            session.close()

    def remove_track_from_playlist(self, playlist_id: int, track_id: int) -> bool:
        """
        Remove a track from a playlist

        Args:
            playlist_id: Playlist ID
            track_id: Track ID

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            track = session.query(Track).filter_by(id=track_id).first()

            if not playlist or not track:
                return False

            # Remove track from playlist
            if track in playlist.tracks:
                playlist.tracks.remove(track)
                session.commit()
                info(f"Removed track '{track.title}' from playlist '{playlist.name}'")

            return True

        except Exception as e:
            session.rollback()
            error(f"Failed to remove track {track_id} from playlist {playlist_id}: {e}")
            return False
        finally:
            session.close()

    def clear_playlist(self, playlist_id: int) -> bool:
        """
        Remove all tracks from a playlist

        Args:
            playlist_id: Playlist ID

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            if not playlist:
                return False

            # Clear all tracks
            playlist.tracks.clear()
            session.commit()
            info(f"Cleared all tracks from playlist '{playlist.name}'")
            return True

        except Exception as e:
            session.rollback()
            error(f"Failed to clear playlist {playlist_id}: {e}")
            return False
        finally:
            session.close()