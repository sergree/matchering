"""
Peak limiter implementation.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass
from ..core.engine import AudioProcessor

@dataclass
class LimiterParams:
    """Limiter parameters."""
    threshold: float = -0.1    # dB
    release: float = 0.050     # Release time in seconds
    lookahead: float = 0.005   # Lookahead time in seconds
    output_gain: float = 0.0   # Output gain in dB

class Limiter(AudioProcessor):
    """Peak limiter with lookahead."""
    
    def __init__(self, sample_rate: int = 44100, params: Optional[LimiterParams] = None):
        """Initialize limiter.
        
        Args:
            sample_rate: Sample rate in Hz
            params: Optional limiter parameters
        """
        self.sample_rate = sample_rate
        self.params = params or LimiterParams()
        
        # Calculate time constants
        self._release_coef = np.exp(-1 / (self.sample_rate * self.params.release))
        self._lookahead_samples = int(self.sample_rate * self.params.lookahead)
        
        # State variables
        self._gain_reduction = 0.0
        self._buffer = None
        self.reset()
        
    def _init_buffer(self, channels: int):
        """Initialize delay buffer.
        
        Args:
            channels: Number of audio channels
        """
        if self._buffer is None or self._buffer.shape[1] != channels:
            self._buffer = np.zeros((self._lookahead_samples, channels))
            
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer
            
        Returns:
            Processed audio buffer
        """
        self._init_buffer(buffer.shape[1])
        
        # Convert threshold to linear gain
        threshold_linear = np.power(10, self.params.threshold / 20)
        output_gain = np.power(10, self.params.output_gain / 20)
        
        # Prepare output buffer
        output = np.zeros_like(buffer)
        
        # Process each sample
        for i in range(len(buffer)):
            # Look ahead for peaks
            look_buffer = np.concatenate((
                buffer[i:min(i + self._lookahead_samples, len(buffer))],
                np.zeros((max(0, i + self._lookahead_samples - len(buffer)),
                         buffer.shape[1]))
            ))
            
            # Find maximum peak in lookahead window
            peak_level = np.max(np.abs(look_buffer))
            
            # Calculate target gain reduction
            if peak_level > threshold_linear:
                target_reduction = threshold_linear / peak_level
            else:
                target_reduction = 1.0
                
            # Apply release envelope
            if target_reduction < self._gain_reduction:
                self._gain_reduction = target_reduction
            else:
                self._gain_reduction = self._release_coef * self._gain_reduction + \
                                     (1 - self._release_coef) * target_reduction
                                     
            # Apply gain reduction to delayed signal with hard clip
            sample = self._buffer[0] * self._gain_reduction * output_gain
            # Hard clip with a tiny margin below threshold to ensure we never exceed it
            # even after potential output gain application
            hard_clip = threshold_linear * 0.999  # 0.1% margin
            output[i] = np.clip(sample, -hard_clip, hard_clip)
            
            # Update delay buffer
            self._buffer = np.vstack((self._buffer[1:], buffer[i]))
            
        return output
        
    def reset(self):
        """Reset processor state."""
        self._gain_reduction = 1.0
        if self._buffer is not None:
            self._buffer.fill(0)
            
    def update_params(self, params: LimiterParams):
        """Update limiter parameters.
        
        Args:
            params: New parameters
        """
        old_lookahead = self.params.lookahead
        self.params = params
        
        # Update time constants
        self._release_coef = np.exp(-1 / (self.sample_rate * self.params.release))
        
        # Update buffer size if lookahead changed
        if old_lookahead != self.params.lookahead:
            self._lookahead_samples = int(self.sample_rate * self.params.lookahead)
            self._buffer = None  # Will be recreated on next process call


class BrickwallLimiter(Limiter):
    """Brickwall limiter with true peak detection."""
    
    def __init__(self, sample_rate: int = 44100, params: Optional[LimiterParams] = None,
                 oversampling: int = 4):
        """Initialize brickwall limiter.
        
        Args:
            sample_rate: Sample rate in Hz
            params: Optional limiter parameters
            oversampling: Oversampling factor for true peak detection
        """
        # Initialize state placeholders before base init (base.reset may reference them)
        self._up_state = None
        self._down_state = None
        super().__init__(sample_rate, params)
        self.oversampling = oversampling
        
        # Create oversampling filters
        from scipy import signal
        self._up_filter = signal.firwin(61, 0.45, window='hamming')
        self._down_filter = self._up_filter * self.oversampling
        
        # Ensure states are in a known state
        self._up_state = None
        self._down_state = None
        self.reset()
        
    def _init_states(self, channels: int):
        """Initialize filter states.
        
        Args:
            channels: Number of audio channels
        """
        if self._up_state is None or self._up_state.shape[1] != channels:
            self._up_state = np.zeros((len(self._up_filter) - 1, channels))
            self._down_state = np.zeros((len(self._down_filter) - 1, channels))
            
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer
            
        Returns:
            Processed audio buffer
        """
        from scipy import signal
        
        self._init_states(buffer.shape[1])
        
        # Convert threshold to linear gain
        threshold_linear = np.power(10, self.params.threshold / 20)
        
        # Upsample
        up_samples = self.oversampling * len(buffer)
        up_buffer = np.zeros((up_samples, buffer.shape[1]))
        for ch in range(buffer.shape[1]):
            # Insert zeros
            up_buffer[:, ch][::self.oversampling] = buffer[:, ch]
            # Apply filter
            up_buffer[:, ch], self._up_state[:, ch] = signal.lfilter(
                self._up_filter, [1.0],
                up_buffer[:, ch],
                zi=self._up_state[:, ch]
            )
            
        # Process at higher sample rate
        up_output = super().process(up_buffer)
        
        # Downsample
        output = np.zeros_like(buffer)
        for ch in range(buffer.shape[1]):
            # Apply filter
            down_filtered, self._down_state[:, ch] = signal.lfilter(
                self._down_filter, [1.0],
                up_output[:, ch],
                zi=self._down_state[:, ch]
            )
            # Decimate and apply final hard clip to be absolutely certain
            output[:, ch] = np.clip(
                down_filtered[::self.oversampling],
                -threshold_linear,
                threshold_linear
            )
            
        return output
        
    def reset(self):
        """Reset processor state."""
        super().reset()
        if self._up_state is not None:
            self._up_state.fill(0)
            self._down_state.fill(0)