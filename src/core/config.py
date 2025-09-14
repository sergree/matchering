"""
Audio configuration module.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AudioConfig:
    """Audio configuration."""
    
    sample_rate: int = 44100
    channels: int = 2
    bit_depth: int = 16
    block_size: int = 1024
    device_name: Optional[str] = None
    buffer_count: int = 2  # Number of buffers for audio device
    
    # Processing settings
    enable_effects: bool = True
    enable_visualizers: bool = True
    enable_metering: bool = True
    
    # Format preferences
    preferred_formats: list[str] = None
    format_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.preferred_formats is None:
            self.preferred_formats = ["wav", "flac", "aiff", "mp3", "ogg"]
        if self.format_settings is None:
            self.format_settings = {
                "wav": {"subtype": "PCM_16"},
                "flac": {"compression_level": 5},
                "mp3": {"bitrate": 320000},
                "ogg": {"quality": 0.6}
            }