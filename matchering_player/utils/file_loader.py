# -*- coding: utf-8 -*-

"""
Audio File Loader for Matchering Player
Supports WAV, MP3, FLAC and other formats via soundfile and librosa
"""

import os
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import logging

# Try to import audio libraries
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


logger = logging.getLogger(__name__)


class AudioFileInfo:
    """Information about an audio file"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = Path(file_path).name
        self.stem = Path(file_path).stem
        self.suffix = Path(file_path).suffix.lower()
        
        # Audio properties (filled by loader)
        self.sample_rate: Optional[int] = None
        self.channels: Optional[int] = None
        self.frames: Optional[int] = None
        self.duration: Optional[float] = None
        self.format_info: Optional[str] = None
        
    def __str__(self) -> str:
        if self.sample_rate:
            return (f"{self.filename}: {self.duration:.1f}s, "
                   f"{self.sample_rate}Hz, {self.channels}ch, {self.format_info}")
        return f"{self.filename}: (not analyzed)"


class AudioFileLoader:
    """
    Audio file loader with support for multiple formats
    Handles conversion to standard format for processing
    """
    
    # Supported formats
    SOUNDFILE_FORMATS = {'.wav', '.flac', '.aiff', '.aif', '.au', '.snd'}
    LIBROSA_FORMATS = {'.mp3', '.m4a', '.ogg', '.wma'}
    
    def __init__(self, target_sample_rate: int = 44100, target_channels: int = 2):
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels
        
        # Check available libraries
        self.available_loaders = []
        if HAS_SOUNDFILE:
            self.available_loaders.append('soundfile')
        if HAS_LIBROSA:
            self.available_loaders.append('librosa')
            
        if not self.available_loaders:
            raise RuntimeError("No audio loading libraries available. Install soundfile and/or librosa.")
        
        logger.info(f"AudioFileLoader initialized with: {', '.join(self.available_loaders)}")
    
    def get_file_info(self, file_path: str) -> AudioFileInfo:
        """Get information about an audio file without loading it"""
        info = AudioFileInfo(file_path)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        try:
            # Try soundfile first for efficiency
            if HAS_SOUNDFILE and info.suffix in self.SOUNDFILE_FORMATS:
                with sf.SoundFile(file_path, 'r') as f:
                    info.sample_rate = f.samplerate
                    info.channels = f.channels
                    info.frames = f.frames
                    info.duration = f.frames / f.samplerate
                    info.format_info = f"{f.format} {f.subtype}"
                    
            elif HAS_LIBROSA:
                # Use librosa for format info only (don't load audio yet)
                try:
                    duration = librosa.get_duration(filename=file_path)
                    info.duration = duration
                    # We'll get sample rate when we actually load
                    info.format_info = f"Librosa-supported {info.suffix}"
                except Exception as e:
                    logger.warning(f"Could not get duration for {file_path}: {e}")
                    info.format_info = f"Unknown {info.suffix}"
            else:
                raise ValueError(f"Unsupported audio format: {info.suffix}")
                
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            raise
        
        return info
    
    def load_audio_file(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load an audio file and convert to target format
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
            audio_data: shape (samples, channels) as float32
            sample_rate: Always matches target_sample_rate
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        file_info = Path(file_path)
        suffix = file_info.suffix.lower()
        
        logger.info(f"Loading audio file: {file_path}")
        
        # Load audio data
        audio_data, original_sample_rate = self._load_raw_audio(file_path, suffix)
        
        # Convert to standard format
        processed_audio = self._process_audio(audio_data, original_sample_rate)
        
        logger.info(f"Loaded: {processed_audio.shape[0]} samples, "
                   f"{processed_audio.shape[1]} channels, {self.target_sample_rate}Hz")
        
        return processed_audio, self.target_sample_rate
    
    def _load_raw_audio(self, file_path: str, suffix: str) -> Tuple[np.ndarray, int]:
        """Load raw audio data using appropriate library"""
        
        # Try soundfile first (faster and more accurate)
        if HAS_SOUNDFILE and suffix in self.SOUNDFILE_FORMATS:
            try:
                audio_data, sample_rate = sf.read(file_path, dtype='float32')
                logger.debug(f"Loaded with soundfile: {audio_data.shape}, {sample_rate}Hz")
                return audio_data, sample_rate
            except Exception as e:
                logger.warning(f"Soundfile failed for {file_path}: {e}")
                if not HAS_LIBROSA:
                    raise
        
        # Fall back to librosa for other formats
        if HAS_LIBROSA:
            try:
                # Load with librosa (always returns mono by default)
                audio_data, sample_rate = librosa.load(file_path, sr=None, mono=False)
                
                # Librosa returns (channels, samples) - transpose to (samples, channels)
                if audio_data.ndim == 1:
                    audio_data = audio_data.reshape(-1, 1)  # Make mono into (samples, 1)
                else:
                    audio_data = audio_data.T  # Transpose to (samples, channels)
                
                audio_data = audio_data.astype(np.float32)
                logger.debug(f"Loaded with librosa: {audio_data.shape}, {sample_rate}Hz")
                return audio_data, sample_rate
                
            except Exception as e:
                logger.error(f"Librosa failed for {file_path}: {e}")
                raise
        
        raise ValueError(f"No suitable loader found for {file_path}")
    
    def _process_audio(self, audio_data: np.ndarray, original_sample_rate: int) -> np.ndarray:
        """Convert audio to target format (sample rate, channels)"""
        
        # Ensure we have the right shape: (samples, channels)
        if audio_data.ndim == 1:
            audio_data = audio_data.reshape(-1, 1)
        
        # Resample if needed
        if original_sample_rate != self.target_sample_rate:
            if HAS_LIBROSA:
                logger.info(f"Resampling from {original_sample_rate}Hz to {self.target_sample_rate}Hz")
                
                # Resample each channel separately
                resampled_channels = []
                for ch in range(audio_data.shape[1]):
                    resampled = librosa.resample(
                        audio_data[:, ch], 
                        orig_sr=original_sample_rate,
                        target_sr=self.target_sample_rate
                    )
                    resampled_channels.append(resampled)
                
                audio_data = np.column_stack(resampled_channels)
            else:
                logger.warning(f"Cannot resample without librosa. "
                             f"Audio will remain at {original_sample_rate}Hz")
        
        # Convert channel count
        current_channels = audio_data.shape[1]
        
        if current_channels == self.target_channels:
            # Perfect match
            pass
        elif current_channels == 1 and self.target_channels == 2:
            # Mono to stereo: duplicate channel
            logger.info("Converting mono to stereo")
            audio_data = np.repeat(audio_data, 2, axis=1)
        elif current_channels == 2 and self.target_channels == 1:
            # Stereo to mono: average channels
            logger.info("Converting stereo to mono")
            audio_data = np.mean(audio_data, axis=1, keepdims=True)
        elif current_channels > 2 and self.target_channels == 2:
            # Multi-channel to stereo: take first two channels
            logger.info(f"Converting {current_channels}-channel to stereo (using first 2 channels)")
            audio_data = audio_data[:, :2]
        else:
            logger.warning(f"Unusual channel conversion: {current_channels} -> {self.target_channels}")
            # For unusual cases, just take what we need or pad with zeros
            if current_channels < self.target_channels:
                # Pad with zeros
                padding = np.zeros((audio_data.shape[0], self.target_channels - current_channels))
                audio_data = np.concatenate([audio_data, padding], axis=1)
            else:
                # Truncate
                audio_data = audio_data[:, :self.target_channels]
        
        # Ensure float32 dtype
        audio_data = audio_data.astype(np.float32)
        
        # Clip to prevent issues
        audio_data = np.clip(audio_data, -1.0, 1.0)
        
        return audio_data
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if a file format is supported"""
        suffix = Path(file_path).suffix.lower()
        return (suffix in self.SOUNDFILE_FORMATS or 
                suffix in self.LIBROSA_FORMATS)
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get list of supported formats by loader"""
        formats = {}
        if HAS_SOUNDFILE:
            formats['soundfile'] = list(self.SOUNDFILE_FORMATS)
        if HAS_LIBROSA:
            formats['librosa'] = list(self.LIBROSA_FORMATS)
        return formats


def load_audio_file(file_path: str, target_sample_rate: int = 44100, 
                   target_channels: int = 2) -> Tuple[np.ndarray, int]:
    """
    Convenience function to load an audio file
    
    Args:
        file_path: Path to audio file
        target_sample_rate: Desired sample rate (default: 44100)
        target_channels: Desired channel count (default: 2)
        
    Returns:
        Tuple of (audio_data, sample_rate)
        audio_data: shape (samples, channels) as float32
    """
    loader = AudioFileLoader(target_sample_rate, target_channels)
    return loader.load_audio_file(file_path)


def get_audio_file_info(file_path: str) -> AudioFileInfo:
    """
    Convenience function to get audio file information
    
    Args:
        file_path: Path to audio file
        
    Returns:
        AudioFileInfo object with file details
    """
    loader = AudioFileLoader()
    return loader.get_file_info(file_path)
