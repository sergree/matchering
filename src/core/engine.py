"""
Core audio engine implementation.
"""

from typing import Optional, List, Dict, Any
import numpy as np
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from abc import ABC, abstractmethod

@dataclass
class AudioConfig:
    """Audio configuration parameters."""
    sample_rate: int = 44100
    channels: int = 2
    buffer_size: int = 512
    device_name: Optional[str] = None
    format: np.dtype = np.float32

class AudioBuffer:
    """Audio buffer implementation with zero-copy operations."""
    
    def __init__(self, size: int, channels: int, dtype: np.dtype = np.float32):
        """Initialize audio buffer.
        
        Args:
            size: Buffer size in samples
            channels: Number of channels
            dtype: Buffer data type
        """
        self.data = np.zeros((size, channels), dtype=dtype)
        self._position = 0
        self._lock = threading.RLock()
        
    @property
    def position(self) -> int:
        """Current buffer position."""
        return self._position
        
    @position.setter
    def position(self, value: int):
        """Set buffer position."""
        with self._lock:
            self._position = max(0, min(value, len(self.data)))
            
    def write(self, data: np.ndarray) -> int:
        """Write data to buffer.
        
        Args:
            data: Audio data to write
            
        Returns:
            Number of samples written
        """
        with self._lock:
            available = len(self.data) - self._position
            if available <= 0:
                return 0
                
            write_size = min(len(data), available)
            self.data[self._position:self._position + write_size] = data[:write_size]
            self._position += write_size
            return write_size
            
    def read(self, size: int) -> np.ndarray:
        """Read data from buffer.
        
        Args:
            size: Number of samples to read
            
        Returns:
            Audio data
        """
        with self._lock:
            if self._position >= len(self.data):
                return np.zeros((0, self.data.shape[1]), dtype=self.data.dtype)
                
            read_size = min(size, len(self.data) - self._position)
            data = self.data[self._position:self._position + read_size].copy()
            self._position += read_size
            return data
            
    def reset(self):
        """Reset buffer position."""
        with self._lock:
            self._position = 0

class AudioProcessor(ABC):
    """Base class for audio processors."""
    
    @abstractmethod
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio data.
        
        Args:
            buffer: Input audio buffer
            
        Returns:
            Processed audio data
        """
        pass
        
    @abstractmethod
    def reset(self):
        """Reset processor state."""
        pass

class AudioEngine:
    """Core audio engine implementation."""
    
    def __init__(self, config: AudioConfig):
        """Initialize audio engine.
        
        Args:
            config: Audio configuration
        """
        self.config = config
        self.processors: List[AudioProcessor] = []
        self._input_buffer = AudioBuffer(
            config.buffer_size * 4,  # 4x buffer for safety
            config.channels,
            config.format
        )
        self._output_buffer = AudioBuffer(
            config.buffer_size * 4,
            config.channels,
            config.format
        )
        self._running = False
        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._processing_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
        
    def add_processor(self, processor: AudioProcessor):
        """Add audio processor to chain.
        
        Args:
            processor: Audio processor instance
        """
        with self._lock:
            self.processors.append(processor)
            
    def remove_processor(self, processor: AudioProcessor):
        """Remove audio processor from chain.
        
        Args:
            processor: Audio processor instance
        """
        with self._lock:
            if processor in self.processors:
                self.processors.remove(processor)
                
    async def start(self):
        """Start audio processing."""
        if self._running:
            return
            
        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        
    async def stop(self):
        """Stop audio processing."""
        self._running = False
        if self._processing_task:
            await self._processing_task
            self._processing_task = None
            
    async def _processing_loop(self):
        """Main processing loop."""
        while self._running:
            # Read input buffer
            input_data = self._input_buffer.read(self.config.buffer_size)
            if len(input_data) == 0:
                await asyncio.sleep(0.001)  # Prevent busy loop
                continue
                
            # Process audio
            output_data = input_data
            for processor in self.processors:
                output_data = await asyncio.get_event_loop().run_in_executor(
                    self._thread_pool,
                    processor.process,
                    output_data
                )
                
            # Write to output buffer
            self._output_buffer.write(output_data)
            
            # Small sleep to prevent busy loop
            await asyncio.sleep(0.001)
            
    def write_input(self, data: np.ndarray) -> int:
        """Write data to input buffer.
        
        Args:
            data: Audio data to write
            
        Returns:
            Number of samples written
        """
        return self._input_buffer.write(data)
        
    def read_output(self, size: int) -> np.ndarray:
        """Read data from output buffer.
        
        Args:
            size: Number of samples to read
            
        Returns:
            Audio data
        """
        return self._output_buffer.read(size)
        
    def reset(self):
        """Reset engine state."""
        with self._lock:
            self._input_buffer.reset()
            self._output_buffer.reset()
            for processor in self.processors:
                processor.reset()