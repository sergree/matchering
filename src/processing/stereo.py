"""
Stereo processing implementations.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from ..core.engine import AudioProcessor

@dataclass
class StereoParams:
    """Stereo processing parameters."""
    width: float = 1.0      # Stereo width (0.0 = mono, 1.0 = normal, 2.0 = wide)
    rotation: float = 0.0   # Stereo rotation in degrees (-180 to 180)
    balance: float = 0.0    # Channel balance (-1.0 = left, 0.0 = center, 1.0 = right)

class StereoProcessor(AudioProcessor):
    """Stereo field processor."""
    
    def __init__(self, params: Optional[StereoParams] = None):
        """Initialize stereo processor.
        
        Args:
            params: Optional stereo parameters
        """
        self.params = params or StereoParams()
        
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer (stereo)
            
        Returns:
            Processed audio buffer
        """
        if buffer.shape[1] != 2:
            return buffer  # Only process stereo audio
            
        # Convert to mid-side
        mid = (buffer[:, 0] + buffer[:, 1]) * 0.5
        side = (buffer[:, 0] - buffer[:, 1]) * 0.5
        
        # Apply width
        side *= self.params.width
        
        # Apply rotation
        if self.params.rotation != 0:
            angle = np.radians(self.params.rotation)
            mid_rot = mid * np.cos(angle) - side * np.sin(angle)
            side_rot = mid * np.sin(angle) + side * np.cos(angle)
            mid, side = mid_rot, side_rot
            
        # Convert back to left-right
        left = mid + side
        right = mid - side
        
        # Apply balance
        if self.params.balance > 0:
            left *= (1 - self.params.balance)
        elif self.params.balance < 0:
            right *= (1 + self.params.balance)
            
        return np.column_stack((left, right))
        
    def reset(self):
        """Reset processor state."""
        pass  # No state to reset
        
    def update_params(self, params: StereoParams):
        """Update stereo parameters.
        
        Args:
            params: New parameters
        """
        self.params = params


class MidSideProcessor(AudioProcessor):
    """Mid/Side processor with separate processing chains."""
    
    def __init__(self):
        """Initialize Mid/Side processor."""
        self.mid_processors: List[AudioProcessor] = []
        self.side_processors: List[AudioProcessor] = []
        
    def add_mid_processor(self, processor: AudioProcessor):
        """Add processor to mid channel.
        
        Args:
            processor: Processor to add
        """
        self.mid_processors.append(processor)
        
    def add_side_processor(self, processor: AudioProcessor):
        """Add processor to side channel.
        
        Args:
            processor: Processor to add
        """
        self.side_processors.append(processor)
        
    def remove_mid_processor(self, processor: AudioProcessor):
        """Remove processor from mid channel.
        
        Args:
            processor: Processor to remove
        """
        if processor in self.mid_processors:
            self.mid_processors.remove(processor)
            
    def remove_side_processor(self, processor: AudioProcessor):
        """Remove processor from side channel.
        
        Args:
            processor: Processor to remove
        """
        if processor in self.side_processors:
            self.side_processors.remove(processor)
            
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer (stereo)
            
        Returns:
            Processed audio buffer
        """
        if buffer.shape[1] != 2:
            return buffer  # Only process stereo audio
            
        # Convert to mid-side
        mid = (buffer[:, 0] + buffer[:, 1]) * 0.5
        side = (buffer[:, 0] - buffer[:, 1]) * 0.5
        
        # Process mid channel
        mid_processed = mid.copy()
        for processor in self.mid_processors:
            mid_processed = processor.process(mid_processed.reshape(-1, 1))[:, 0]
            
        # Process side channel
        side_processed = side.copy()
        for processor in self.side_processors:
            side_processed = processor.process(side_processed.reshape(-1, 1))[:, 0]
            
        # Convert back to left-right
        left = mid_processed + side_processed
        right = mid_processed - side_processed
        
        return np.column_stack((left, right))
        
    def reset(self):
        """Reset processor state."""
        for processor in self.mid_processors:
            processor.reset()
        for processor in self.side_processors:
            processor.reset()


class AutoPanner(AudioProcessor):
    """Automatic stereo panner."""
    
    def __init__(self, sample_rate: int = 44100):
        """Initialize auto-panner.
        
        Args:
            sample_rate: Sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.rate = 0.5  # Hz
        self.depth = 0.5  # 0-1
        self.shape = 'sine'  # 'sine', 'triangle', 'square'
        self._phase = 0.0
        
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer
            
        Returns:
            Processed audio buffer
        """
        if buffer.shape[1] != 2:
            return buffer
            
        # Generate LFO values
        t = np.arange(len(buffer)) / self.sample_rate + self._phase
        if self.shape == 'sine':
            lfo = np.sin(2 * np.pi * self.rate * t)
        elif self.shape == 'triangle':
            lfo = 2 * np.abs(2 * (self.rate * t % 1) - 1) - 1
        else:  # square
            lfo = np.sign(np.sin(2 * np.pi * self.rate * t))
            
        # Scale LFO
        lfo *= self.depth
        
        # Apply panning
        left_gain = np.sqrt(0.5 + lfo)
        right_gain = np.sqrt(0.5 - lfo)
        
        output = buffer.copy()
        output[:, 0] *= left_gain
        output[:, 1] *= right_gain
        
        # Update phase
        self._phase = (t[-1] * self.rate) % 1.0 / self.rate
        
        return output
        
    def reset(self):
        """Reset processor state."""
        self._phase = 0.0