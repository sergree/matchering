"""
Audio format handling system.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, BinaryIO
import numpy as np
import soundfile as sf
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.aiff import AIFF
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4

class AudioFormatError(Exception):
    """Audio format error."""
    pass

class AudioFormat:
    """Audio format handler base class."""
    
    def __init__(self, path: str):
        """Initialize format handler.
        
        Args:
            path: Path to audio file
        """
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        self.info = None
        self.metadata = {}
        self._file = None
        self._load_info()
        
    def _load_info(self):
        """Load audio file information."""
        raise NotImplementedError
        
    def read(self, start: int = 0, frames: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """Read audio data.
        
        Args:
            start: Start frame
            frames: Number of frames to read (None for all)
            
        Returns:
            Tuple of (audio data, sample rate)
        """
        raise NotImplementedError
        
    def write(self, path: str, data: np.ndarray, sample_rate: int):
        """Write audio data to file.
        
        Args:
            path: Output file path
            data: Audio data
            sample_rate: Sample rate in Hz
        """
        raise NotImplementedError
        
    def close(self):
        """Close audio file."""
        if self._file is not None:
            self._file.close()
            self._file = None


class SoundFileFormat(AudioFormat):
    """Format handler using soundfile."""
    
    def _load_info(self):
        """Load audio file information."""
        self._file = sf.SoundFile(self.path)
        self.info = {
            'sample_rate': self._file.samplerate,
            'channels': self._file.channels,
            'frames': self._file.frames,
            'format': self._file.format,
            'subtype': self._file.subtype,
            'duration': float(self._file.frames) / self._file.samplerate
        }
        
    def read(self, start: int = 0, frames: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """Read audio data.
        
        Args:
            start: Start frame
            frames: Number of frames to read (None for all)
            
        Returns:
            Tuple of (audio data, sample rate)
        """
        if self._file is None:
            raise AudioFormatError("File is not open")
            
        self._file.seek(start)
        data = self._file.read(frames)
        return data, self._file.samplerate
        
    def write(self, path: str, data: np.ndarray, sample_rate: int):
        """Write audio data to file.
        
        Args:
            path: Output file path
            data: Audio data
            sample_rate: Sample rate in Hz
        """
        sf.write(path, data, sample_rate)


class MP3Format(AudioFormat):
    """MP3 format handler."""
    
    def _load_info(self):
        """Load audio file information."""
        # Use mutagen for metadata
        mp3 = MP3(self.path)
        self.info = {
            'sample_rate': mp3.info.sample_rate,
            'channels': mp3.info.channels,
            'duration': mp3.info.length,
            'bitrate': mp3.info.bitrate,
            'encoder_info': mp3.info.encoder_info
        }
        
        # Load ID3 tags if available
        if mp3.tags is not None:
            try:
                id3 = EasyID3(self.path)
                self.metadata = dict(id3)
            except mutagen.id3.ID3NoHeaderError:
                pass
                
        # Use soundfile for actual audio data
        self._file = sf.SoundFile(self.path)
        
    def read(self, start: int = 0, frames: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """Read audio data.
        
        Args:
            start: Start frame
            frames: Number of frames to read (None for all)
            
        Returns:
            Tuple of (audio data, sample rate)
        """
        if self._file is None:
            raise AudioFormatError("File is not open")
            
        self._file.seek(start)
        data = self._file.read(frames)
        return data, self._file.samplerate
        
    def write(self, path: str, data: np.ndarray, sample_rate: int):
        """Write audio data to file.
        
        Args:
            path: Output file path
            data: Audio data
            sample_rate: Sample rate in Hz
        """
        import soundfile as sf
        temp_path = path + '.temp.wav'
        try:
            # Write to temporary WAV file
            sf.write(temp_path, data, sample_rate, subtype='PCM_16')
            
            # Convert to MP3 using ffmpeg
            import subprocess
            subprocess.run([
                'ffmpeg', '-y',
                '-i', temp_path,
                '-codec:a', 'libmp3lame',
                '-qscale:a', '2',  # High quality VBR
                path
            ], check=True)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class FLACFormat(AudioFormat):
    """FLAC format handler."""
    
    def _load_info(self):
        """Load audio file information."""
        flac = FLAC(self.path)
        self.info = {
            'sample_rate': flac.info.sample_rate,
            'channels': flac.info.channels,
            'duration': flac.info.length,
            'bits_per_sample': flac.info.bits_per_sample
        }
        self.metadata = dict(flac.tags)
        
        # Use soundfile for actual audio data
        self._file = sf.SoundFile(self.path)
        
    def read(self, start: int = 0, frames: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """Read audio data.
        
        Args:
            start: Start frame
            frames: Number of frames to read (None for all)
            
        Returns:
            Tuple of (audio data, sample rate)
        """
        if self._file is None:
            raise AudioFormatError("File is not open")
            
        self._file.seek(start)
        data = self._file.read(frames)
        return data, self._file.samplerate
        
    def write(self, path: str, data: np.ndarray, sample_rate: int):
        """Write audio data to file.
        
        Args:
            path: Output file path
            data: Audio data
            sample_rate: Sample rate in Hz
        """
        sf.write(path, data, sample_rate, format='FLAC')


class OggFormat(AudioFormat):
    """Ogg Vorbis format handler."""
    
    def _load_info(self):
        """Load audio file information."""
        ogg = OggVorbis(self.path)
        self.info = {
            'sample_rate': ogg.info.sample_rate,
            'channels': ogg.info.channels,
            'duration': ogg.info.length,
            'bitrate': ogg.info.bitrate
        }
        self.metadata = dict(ogg.tags)
        
        # Use soundfile for actual audio data
        self._file = sf.SoundFile(self.path)
        
    def read(self, start: int = 0, frames: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """Read audio data.
        
        Args:
            start: Start frame
            frames: Number of frames to read (None for all)
            
        Returns:
            Tuple of (audio data, sample rate)
        """
        if self._file is None:
            raise AudioFormatError("File is not open")
            
        self._file.seek(start)
        data = self._file.read(frames)
        return data, self._file.samplerate
        
    def write(self, path: str, data: np.ndarray, sample_rate: int):
        """Write audio data to file.
        
        Args:
            path: Output file path
            data: Audio data
            sample_rate: Sample rate in Hz
        """
        sf.write(path, data, sample_rate, format='OGG')


class FormatFactory:
    """Audio format factory."""
    
    # Map of file extensions to format handlers
    FORMAT_MAP = {
        '.wav': SoundFileFormat,
        '.aiff': SoundFileFormat,
        '.flac': FLACFormat,
        '.mp3': MP3Format,
        '.ogg': OggFormat
    }
    
    @classmethod
    def create_handler(cls, path: str) -> AudioFormat:
        """Create format handler for audio file.
        
        Args:
            path: Path to audio file
            
        Returns:
            Audio format handler
            
        Raises:
            AudioFormatError: If format is not supported
        """
        ext = Path(path).suffix.lower()
        if ext not in cls.FORMAT_MAP:
            raise AudioFormatError(f"Unsupported format: {ext}")
            
        return cls.FORMAT_MAP[ext](path)
        
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of supported formats.
        
        Returns:
            List of supported file extensions
        """
        return list(cls.FORMAT_MAP.keys())


class AudioFileInfo:
    """Audio file information container."""
    
    def __init__(self, path: str):
        """Initialize audio file info.
        
        Args:
            path: Path to audio file
        """
        self.path = Path(path)
        self.format = self.path.suffix.lower()
        self.handler = FormatFactory.create_handler(path)
        
        # Basic properties
        self.sample_rate = self.handler.info['sample_rate']
        self.channels = self.handler.info['channels']
        self.duration = self.handler.info['duration']
        
        # Format-specific properties
        self.properties = self.handler.info
        
        # Metadata
        self.metadata = self.handler.metadata
        
    def __str__(self) -> str:
        """Get string representation."""
        return (
            f"Audio File: {self.path.name}\n"
            f"Format: {self.format}\n"
            f"Sample Rate: {self.sample_rate} Hz\n"
            f"Channels: {self.channels}\n"
            f"Duration: {self.duration:.2f} seconds"
        )


class AudioFile:
    """High-level audio file interface."""
    
    def __init__(self, path: str):
        """Initialize audio file.
        
        Args:
            path: Path to audio file
        """
        self.info = AudioFileInfo(path)
        self._handler = self.info.handler
        
    def read(self, start: float = 0.0, duration: Optional[float] = None) -> np.ndarray:
        """Read audio data.
        
        Args:
            start: Start time in seconds
            duration: Duration in seconds (None for entire file)
            
        Returns:
            Audio data as numpy array
        """
        # Convert time to frames
        start_frame = int(start * self.info.sample_rate)
        frames = None if duration is None else int(duration * self.info.sample_rate)
        
        # Read data
        data, _ = self._handler.read(start_frame, frames)
        return data
        
    def write(self, path: str, data: np.ndarray):
        """Write audio data to file.
        
        Args:
            path: Output file path
            data: Audio data
        """
        self._handler.write(path, data, self.info.sample_rate)
        
    def close(self):
        """Close audio file."""
        self._handler.close()
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()