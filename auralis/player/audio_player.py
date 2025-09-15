# -*- coding: utf-8 -*-

"""
Auralis Audio Player
~~~~~~~~~~~~~~~~~~~

Real-time audio player with live mastering capabilities

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Integrated from Matchering Player components
"""

import numpy as np
from .config import PlayerConfig
from ..core.processor import process as core_process
from ..utils.logging import debug, info


class AudioPlayer:
    """Real-time audio player with integrated mastering"""

    def __init__(self, config: PlayerConfig = None):
        if config is None:
            config = PlayerConfig()
        self.config = config
        self.is_playing = False
        self.current_file = None
        self.reference_file = None
        self.audio_data = None
        self.reference_data = None
        self.position = 0

        debug("AudioPlayer initialized")

    def load_file(self, file_path: str) -> bool:
        """
        Load an audio file for playback

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if successful
        """
        try:
            from ..io.loader import load
            self.audio_data, sample_rate = load(file_path, "target")
            self.current_file = file_path
            self.position = 0

            info(f"Loaded audio file: {file_path}")
            return True

        except Exception as e:
            debug(f"Failed to load file: {e}")
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
            from ..io.loader import load
            self.reference_data, sample_rate = load(file_path, "reference")
            self.reference_file = file_path

            info(f"Loaded reference file: {file_path}")
            return True

        except Exception as e:
            debug(f"Failed to load reference: {e}")
            return False

    def play(self):
        """Start playback"""
        if self.audio_data is not None:
            self.is_playing = True
            debug("Playback started")

    def pause(self):
        """Pause playback"""
        self.is_playing = False
        debug("Playback paused")

    def stop(self):
        """Stop playback"""
        self.is_playing = False
        self.position = 0
        debug("Playback stopped")

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

        if self.audio_data is None or not self.is_playing:
            return np.zeros((chunk_size, 2), dtype=np.float32)

        # Get raw audio chunk
        start = self.position
        end = min(start + chunk_size, len(self.audio_data))
        chunk = self.audio_data[start:end]

        # Pad if necessary
        if len(chunk) < chunk_size:
            padding = np.zeros((chunk_size - len(chunk), 2), dtype=np.float32)
            chunk = np.vstack([chunk, padding])

        # Apply real-time processing if reference is loaded
        if self.reference_data is not None and self.config.enable_level_matching:
            chunk = self._apply_real_time_mastering(chunk)

        # Update position
        self.position = end
        if self.position >= len(self.audio_data):
            self.is_playing = False  # End of track

        return chunk

    def _apply_real_time_mastering(self, chunk: np.ndarray) -> np.ndarray:
        """
        Apply real-time mastering to audio chunk

        Args:
            chunk: Raw audio chunk

        Returns:
            Processed audio chunk
        """
        # Simple real-time level matching
        # TODO: Implement more sophisticated real-time processing
        from ..dsp.basic import rms, amplify

        chunk_rms = rms(chunk)
        ref_rms = rms(self.reference_data)

        if chunk_rms > 0:
            gain_db = 20 * np.log10(ref_rms / chunk_rms)
            # Limit gain change for smooth real-time processing
            gain_db = np.clip(gain_db, -6, 6)
            chunk = amplify(chunk, gain_db)

        return chunk

    def get_playback_info(self) -> dict:
        """
        Get current playback information

        Returns:
            dict: Playback status and statistics
        """
        info = {
            'is_playing': self.is_playing,
            'position': self.position,
            'total_samples': len(self.audio_data) if self.audio_data is not None else 0,
            'current_file': self.current_file,
            'reference_file': self.reference_file,
        }

        if self.audio_data is not None:
            info['duration_seconds'] = len(self.audio_data) / self.config.sample_rate
            info['position_seconds'] = self.position / self.config.sample_rate

        return info