"""
Audio buffer management.
"""
import numpy as np
from typing import Optional, List, Dict, Any

class AudioBuffer:
    """Audio buffer for handling audio data."""
    
    def __init__(self, data: np.ndarray, sample_rate: int):
        """Initialize audio buffer.
        
        Args:
            data: Audio data array (samples x channels)
            sample_rate: Sample rate in Hz
        """
        self.data = data
        self.sample_rate = sample_rate
        self.channels = data.shape[1] if len(data.shape) > 1 else 1
        
    def __len__(self) -> int:
        return len(self.data)
        
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return len(self.data) / self.sample_rate

class BufferManager:
    """Manages multiple audio buffers."""
    
    def __init__(self):
        self._buffers: Dict[str, AudioBuffer] = {}
        
    def add_buffer(self, name: str, buffer: AudioBuffer):
        """Add a buffer.
        
        Args:
            name: Buffer name
            buffer: Audio buffer
        """
        self._buffers[name] = buffer
        
    def get_buffer(self, name: str) -> Optional[AudioBuffer]:
        """Get a buffer by name.
        
        Args:
            name: Buffer name
            
        Returns:
            Audio buffer if exists, None otherwise
        """
        return self._buffers.get(name)
        
    def remove_buffer(self, name: str):
        """Remove a buffer.
        
        Args:
            name: Buffer name
        """
        if name in self._buffers:
            del self._buffers[name]
            
    def clear(self):
        """Remove all buffers."""
        self._buffers.clear()
        
    @property
    def buffers(self) -> Dict[str, AudioBuffer]:
        """Get all buffers."""
        return self._buffers