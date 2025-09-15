# -*- coding: utf-8 -*-

"""
Enhanced Auralis Audio Player
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Real-time audio player with advanced DSP processing and library integration

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Integrates advanced capabilities from Matchering Player POC
"""

import os
import numpy as np
import threading
import time
from enum import Enum
from typing import Optional, Dict, Any, List, Callable

from .config import PlayerConfig
from .realtime_processor import RealtimeProcessor
from ..core.processor import process as core_process
from ..io.loader import load
from ..library.manager import LibraryManager
from ..library.models import Track
from ..utils.logging import debug, info, warning, error


class PlaybackState(Enum):
    """Playback state enumeration"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class QueueManager:
    """Simple queue management for track playback"""

    def __init__(self):
        self.tracks: List[Dict[str, Any]] = []
        self.current_index = -1
        self.shuffle_enabled = False
        self.repeat_enabled = False

    def add_track(self, track_info: Dict[str, Any]):
        """Add a track to the queue"""
        self.tracks.append(track_info)

    def add_tracks(self, track_list: List[Dict[str, Any]]):
        """Add multiple tracks to the queue"""
        self.tracks.extend(track_list)

    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Get current track info"""
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None

    def next_track(self) -> Optional[Dict[str, Any]]:
        """Move to next track"""
        if not self.tracks:
            return None

        if self.current_index < len(self.tracks) - 1:
            self.current_index += 1
        elif self.repeat_enabled:
            self.current_index = 0
        else:
            return None

        return self.get_current_track()

    def previous_track(self) -> Optional[Dict[str, Any]]:
        """Move to previous track"""
        if not self.tracks:
            return None

        if self.current_index > 0:
            self.current_index -= 1
        elif self.repeat_enabled:
            self.current_index = len(self.tracks) - 1
        else:
            return None

        return self.get_current_track()

    def clear(self):
        """Clear the queue"""
        self.tracks.clear()
        self.current_index = -1


class EnhancedAudioPlayer:
    """
    Enhanced real-time audio player with advanced DSP and library integration

    Features:
    - Advanced real-time DSP processing
    - Automatic mastering with multiple profiles
    - Queue management and playlist support
    - Performance monitoring and adaptive quality
    - Library integration ready
    """

    def __init__(self, config: PlayerConfig = None, library_manager: LibraryManager = None):
        if config is None:
            config = PlayerConfig()

        self.config = config
        self.state = PlaybackState.STOPPED

        # Library integration
        self.library = library_manager or LibraryManager()

        # Audio data and playback
        self.current_file = None
        self.current_track = None  # Current Track object from library
        self.reference_file = None
        self.audio_data = None
        self.reference_data = None
        self.position = 0
        self.sample_rate = config.sample_rate

        # Advanced processing
        self.processor = RealtimeProcessor(config)

        # Queue management
        self.queue = QueueManager()
        self.auto_reference_selection = True  # Automatically select reference tracks

        # Threading for real-time updates
        self.update_lock = threading.Lock()
        self.callbacks: List[Callable] = []
        self.auto_advance = True  # Auto-advance to next track

        # Statistics
        self.tracks_played = 0
        self.total_play_time = 0.0
        self.session_start_time = time.time()

        info("Enhanced AudioPlayer initialized with library integration and advanced DSP capabilities")

    def add_callback(self, callback: Callable):
        """Add callback for state updates"""
        self.callbacks.append(callback)

    def _notify_callbacks(self):
        """Notify all callbacks of state changes"""
        for callback in self.callbacks:
            try:
                callback(self.get_playback_info())
            except Exception as e:
                debug(f"Callback error: {e}")

    def load_track_from_library(self, track_id: int) -> bool:
        """
        Load a track from the library by ID

        Args:
            track_id: Database ID of the track to load

        Returns:
            bool: True if successful
        """
        try:
            track = self.library.get_track(track_id)
            if not track:
                error(f"Track not found in library: {track_id}")
                return False

            # Load the audio file
            success = self.load_file(track.filepath)
            if success:
                self.current_track = track

                # Record play count
                self.library.record_track_play(track_id)

                # Auto-select reference if enabled
                if self.auto_reference_selection:
                    self._auto_select_reference(track)

                info(f"Loaded track from library: {track.title}")
                return True

            return False

        except Exception as e:
            error(f"Failed to load track from library: {e}")
            return False

    def _auto_select_reference(self, track: Track):
        """Automatically select a suitable reference track"""
        try:
            if track.recommended_reference and os.path.exists(track.recommended_reference):
                # Use pre-analyzed recommended reference
                if self.load_reference(track.recommended_reference):
                    info(f"Using recommended reference: {track.recommended_reference}")
                    return

            # Find suitable reference tracks
            references = self.library.find_reference_tracks(track, limit=3)
            for ref_track in references:
                if os.path.exists(ref_track.filepath):
                    if self.load_reference(ref_track.filepath):
                        info(f"Auto-selected reference: {ref_track.title} by {ref_track.artists[0].name if ref_track.artists else 'Unknown'}")
                        return

            warning(f"No suitable reference found for track: {track.title}")

        except Exception as e:
            warning(f"Auto reference selection failed: {e}")

    def load_file(self, file_path: str) -> bool:
        """
        Load an audio file for playback

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if successful
        """
        try:
            self.state = PlaybackState.LOADING
            self._notify_callbacks()

            # Load audio using Auralis loader
            self.audio_data, self.sample_rate = load(file_path, "target")
            self.current_file = file_path
            self.position = 0
            self.state = PlaybackState.STOPPED

            info(f"Loaded audio file: {file_path}")
            info(f"Duration: {len(self.audio_data) / self.sample_rate:.1f}s")
            info(f"Sample rate: {self.sample_rate} Hz")
            info(f"Channels: {self.audio_data.shape[1] if len(self.audio_data.shape) > 1 else 1}")

            self._notify_callbacks()
            return True

        except Exception as e:
            error(f"Failed to load file {file_path}: {e}")
            self.state = PlaybackState.ERROR
            self._notify_callbacks()
            return False

    def load_reference(self, file_path: str) -> bool:
        """
        Load a reference file for real-time mastering

        Args:
            file_path: Path to the reference audio file

        Returns:
            bool: True if successful
        """
        try:
            # Load reference audio
            self.reference_data, ref_sample_rate = load(file_path, "reference")
            self.reference_file = file_path

            # Set reference for real-time processor
            success = self.processor.set_reference_audio(self.reference_data)

            if success:
                info(f"Reference loaded: {file_path}")
                info(f"Reference duration: {len(self.reference_data) / ref_sample_rate:.1f}s")
                self._notify_callbacks()
                return True
            else:
                warning("Failed to set reference in processor")
                return False

        except Exception as e:
            error(f"Failed to load reference {file_path}: {e}")
            return False

    def play(self) -> bool:
        """Start playback"""
        if self.audio_data is None:
            warning("No audio file loaded")
            return False

        if self.state == PlaybackState.PAUSED:
            self.state = PlaybackState.PLAYING
            info("Playback resumed")
        else:
            self.state = PlaybackState.PLAYING
            info("Playback started")

        self._notify_callbacks()
        return True

    def pause(self) -> bool:
        """Pause playback"""
        if self.state == PlaybackState.PLAYING:
            self.state = PlaybackState.PAUSED
            info("Playback paused")
            self._notify_callbacks()
            return True
        return False

    def stop(self) -> bool:
        """Stop playback"""
        if self.state in [PlaybackState.PLAYING, PlaybackState.PAUSED]:
            self.state = PlaybackState.STOPPED
            self.position = 0
            info("Playback stopped")
            self._notify_callbacks()
            return True
        return False

    def seek(self, position_seconds: float) -> bool:
        """
        Seek to a position in the current track

        Args:
            position_seconds: Position in seconds

        Returns:
            bool: True if successful
        """
        if self.audio_data is None:
            return False

        max_position = len(self.audio_data) / self.sample_rate
        position_seconds = max(0.0, min(position_seconds, max_position))
        self.position = int(position_seconds * self.sample_rate)

        debug(f"Seeked to {position_seconds:.1f}s")
        self._notify_callbacks()
        return True

    def next_track(self) -> bool:
        """Skip to next track in queue"""
        next_track = self.queue.next_track()
        if next_track:
            file_path = next_track.get('file_path') or next_track.get('path')
            if file_path and self.load_file(file_path):
                if self.state == PlaybackState.PLAYING:
                    self.play()  # Continue playing
                self.tracks_played += 1
                info(f"Advanced to next track: {file_path}")
                return True

        # No next track, stop playback
        self.stop()
        return False

    def previous_track(self) -> bool:
        """Skip to previous track in queue"""
        prev_track = self.queue.previous_track()
        if prev_track:
            file_path = prev_track.get('file_path') or prev_track.get('path')
            if file_path and self.load_file(file_path):
                if self.state == PlaybackState.PLAYING:
                    self.play()  # Continue playing
                info(f"Moved to previous track: {file_path}")
                return True
        return False

    def get_audio_chunk(self, chunk_size: int = None) -> np.ndarray:
        """
        Get a chunk of processed audio for playback

        Args:
            chunk_size: Size of audio chunk to return

        Returns:
            Processed audio chunk
        """
        if chunk_size is None:
            chunk_size = self.config.buffer_size

        # Return silence if not playing
        if self.audio_data is None or self.state != PlaybackState.PLAYING:
            return np.zeros((chunk_size, 2), dtype=np.float32)

        # Get raw audio chunk
        start = self.position
        end = min(start + chunk_size, len(self.audio_data))

        if start >= len(self.audio_data):
            # End of track - handle auto-advance
            if self.auto_advance and self.queue.tracks:
                if self.next_track():
                    return self.get_audio_chunk(chunk_size)
            else:
                self.stop()
            return np.zeros((chunk_size, 2), dtype=np.float32)

        chunk = self.audio_data[start:end].copy()

        # Ensure stereo format
        if len(chunk.shape) == 1:
            chunk = np.column_stack([chunk, chunk])
        elif chunk.shape[1] == 1:
            chunk = np.column_stack([chunk[:, 0], chunk[:, 0]])

        # Pad if necessary
        if len(chunk) < chunk_size:
            padding = np.zeros((chunk_size - len(chunk), 2), dtype=np.float32)
            chunk = np.vstack([chunk, padding])

        # Apply advanced real-time processing
        processed_chunk = self.processor.process_chunk(chunk)

        # Update position
        self.position = end

        # Check for end of track
        if self.position >= len(self.audio_data):
            if self.auto_advance and self.queue.tracks:
                # Auto-advance to next track
                threading.Thread(target=self._auto_advance_delayed, daemon=True).start()

        return processed_chunk

    def _auto_advance_delayed(self):
        """Delayed auto-advance to next track"""
        time.sleep(0.1)  # Small delay to avoid race conditions
        with self.update_lock:
            if self.state == PlaybackState.PLAYING:
                self.next_track()

    def set_effect_enabled(self, effect_name: str, enabled: bool):
        """Enable/disable specific DSP effects"""
        self.processor.set_effect_enabled(effect_name, enabled)
        self._notify_callbacks()

    def set_auto_master_profile(self, profile: str):
        """Set auto-mastering profile"""
        self.processor.set_auto_master_profile(profile)
        self._notify_callbacks()

    def load_playlist(self, playlist_id: int, start_index: int = 0) -> bool:
        """
        Load a playlist from the library

        Args:
            playlist_id: Database ID of the playlist
            start_index: Index of track to start playing

        Returns:
            bool: True if successful
        """
        try:
            playlist = self.library.get_playlist(playlist_id)
            if not playlist:
                error(f"Playlist not found: {playlist_id}")
                return False

            # Clear current queue
            self.queue.clear()

            # Add all playlist tracks to queue
            for track in playlist.tracks:
                track_info = track.to_dict()
                self.queue.add_track(track_info)

            if self.queue.tracks:
                # Set starting index
                self.queue.current_index = min(start_index, len(self.queue.tracks) - 1)

                # Load first track
                first_track = self.queue.get_current_track()
                if first_track:
                    track_id = first_track.get('id')
                    if track_id and self.load_track_from_library(track_id):
                        info(f"Loaded playlist: {playlist.name} ({len(playlist.tracks)} tracks)")
                        return True

            warning(f"Failed to load playlist: {playlist.name}")
            return False

        except Exception as e:
            error(f"Failed to load playlist: {e}")
            return False

    def add_to_queue(self, track_info: Dict[str, Any]):
        """Add a track to the playback queue"""
        self.queue.add_track(track_info)

        # If nothing is loaded, load this track
        if self.current_file is None:
            file_path = track_info.get('file_path') or track_info.get('filepath')
            track_id = track_info.get('id')

            if track_id:
                # Load from library if we have an ID
                self.queue.current_index = len(self.queue.tracks) - 1
                self.load_track_from_library(track_id)
            elif file_path:
                # Load from file path
                self.queue.current_index = len(self.queue.tracks) - 1
                self.load_file(file_path)

    def add_track_to_queue(self, track_id: int):
        """Add a track from the library to the queue"""
        try:
            track = self.library.get_track(track_id)
            if track:
                self.add_to_queue(track.to_dict())
                return True
            return False
        except Exception as e:
            error(f"Failed to add track to queue: {e}")
            return False

    def search_and_add_to_queue(self, query: str, limit: int = 10):
        """Search library and add results to queue"""
        try:
            tracks = self.library.search_tracks(query, limit)
            for track in tracks:
                self.add_to_queue(track.to_dict())
            info(f"Added {len(tracks)} tracks to queue from search: {query}")
            return len(tracks)
        except Exception as e:
            error(f"Failed to search and add to queue: {e}")
            return 0

    def clear_queue(self):
        """Clear the playback queue"""
        self.queue.clear()

    def get_playback_info(self) -> Dict[str, Any]:
        """
        Get comprehensive playback information

        Returns:
            dict: Complete playback status and statistics
        """
        # Basic playback info
        info = {
            'state': self.state.value,
            'position_seconds': self.position / self.sample_rate if self.audio_data is not None else 0.0,
            'duration_seconds': len(self.audio_data) / self.sample_rate if self.audio_data is not None else 0.0,
            'current_file': self.current_file,
            'reference_file': self.reference_file,
            'is_playing': self.state == PlaybackState.PLAYING,
        }

        # Queue information
        current_track = self.queue.get_current_track()
        info.update({
            'queue': {
                'current_track': current_track,
                'track_count': len(self.queue.tracks),
                'current_index': self.queue.current_index,
                'has_next': self.queue.current_index < len(self.queue.tracks) - 1,
                'has_previous': self.queue.current_index > 0,
            }
        })

        # Library information
        info.update({
            'library': {
                'current_track_data': self.current_track.to_dict() if self.current_track else None,
                'auto_reference_selection': self.auto_reference_selection,
                'database_path': self.library.database_path,
            }
        })

        # Processing information
        processing_info = self.processor.get_processing_info()
        info.update({
            'processing': processing_info,
            'dsp': processing_info  # Compatibility with existing GUI
        })

        # Session statistics
        session_time = time.time() - self.session_start_time
        info.update({
            'session': {
                'tracks_played': self.tracks_played,
                'session_duration': session_time,
                'total_play_time': self.total_play_time,
            }
        })

        return info

    def get_queue_info(self) -> Dict[str, Any]:
        """Get detailed queue information"""
        return {
            'tracks': self.queue.tracks.copy(),
            'current_index': self.queue.current_index,
            'shuffle_enabled': self.queue.shuffle_enabled,
            'repeat_enabled': self.queue.repeat_enabled,
            'auto_advance': self.auto_advance,
        }

    def set_shuffle(self, enabled: bool):
        """Enable/disable shuffle mode"""
        self.queue.shuffle_enabled = enabled
        info(f"Shuffle {'enabled' if enabled else 'disabled'}")

    def set_repeat(self, enabled: bool):
        """Enable/disable repeat mode"""
        self.queue.repeat_enabled = enabled
        info(f"Repeat {'enabled' if enabled else 'disabled'}")

    def cleanup(self):
        """Clean up resources"""
        self.stop()
        self.processor.reset_all_effects()
        info("AudioPlayer cleanup completed")