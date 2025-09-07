# -*- coding: utf-8 -*-

"""
Basic DSP functions for Matchering Player
Adapted from Matchering 2.0 for realtime processing
"""

import numpy as np
from typing import Tuple


def size(array: np.ndarray) -> int:
    """Get the number of samples in audio array"""
    return array.shape[0]


def channel_count(array: np.ndarray) -> int:
    """Get the number of channels in audio array"""
    return array.shape[1] if len(array.shape) > 1 else 1


def is_stereo(array: np.ndarray) -> bool:
    """Check if audio array is stereo"""
    return len(array.shape) > 1 and array.shape[1] == 2


def lr_to_ms(array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert Left/Right stereo to Mid/Side format
    Mid = (L + R) / 2
    Side = (L - R) / 2
    """
    if not is_stereo(array):
        raise ValueError("Input must be stereo (2-channel) audio")
    
    # Create a copy to avoid modifying original
    stereo = np.copy(array)
    
    # Calculate Mid and Side channels
    mid = (stereo[:, 0] + stereo[:, 1]) * 0.5
    side = (stereo[:, 0] - stereo[:, 1]) * 0.5
    
    return mid, side


def ms_to_lr(mid_array: np.ndarray, side_array: np.ndarray) -> np.ndarray:
    """
    Convert Mid/Side format back to Left/Right stereo
    L = Mid + Side
    R = Mid - Side
    """
    left = mid_array + side_array
    right = mid_array - side_array
    
    # Stack into stereo array
    return np.column_stack((left, right))


def rms(array: np.ndarray) -> float:
    """Calculate Root Mean Square (RMS) of audio array"""
    return np.sqrt(np.mean(array ** 2))


def amplify(array: np.ndarray, gain: float) -> np.ndarray:
    """Amplify audio by gain factor"""
    return array * gain


def normalize(
    array: np.ndarray, 
    threshold: float, 
    epsilon: float, 
    normalize_clipped: bool = False
) -> Tuple[np.ndarray, float]:
    """
    Normalize audio array to threshold level
    Returns normalized audio and the coefficient applied
    """
    coefficient = 1.0
    max_value = np.abs(array).max()
    
    if max_value < threshold or normalize_clipped:
        coefficient = max(epsilon, max_value / threshold)
    
    return array / coefficient, coefficient


def clip(array: np.ndarray, to: float = 1.0) -> np.ndarray:
    """Clip audio to specified range [-to, +to]"""
    return np.clip(array, -to, to)


class ExponentialSmoother:
    """Exponential smoothing for realtime parameter adjustment"""
    
    def __init__(self, alpha: float = 0.1):
        """
        Initialize smoother
        alpha: smoothing factor (0 < alpha <= 1)
               - Higher alpha = faster response, more jitter
               - Lower alpha = slower response, smoother
        """
        assert 0 < alpha <= 1, "Alpha must be between 0 and 1"
        self.alpha = alpha
        self.current_value = None
    
    def update(self, new_value: float) -> float:
        """Update and return smoothed value"""
        if self.current_value is None:
            self.current_value = new_value
        else:
            self.current_value = (self.alpha * new_value + 
                                (1 - self.alpha) * self.current_value)
        
        return self.current_value
    
    def reset(self):
        """Reset smoother state"""
        self.current_value = None


class CircularBuffer:
    """Circular buffer for audio processing"""
    
    def __init__(self, size: int, channels: int = 2):
        """Initialize circular buffer with given size and channel count"""
        self.size = size
        self.channels = channels
        self.buffer = np.zeros((size, channels), dtype=np.float32)
        self.write_pos = 0
        self.read_pos = 0
        self.filled = False
    
    def write(self, data: np.ndarray):
        """Write data to buffer"""
        data_size = len(data)
        
        # Handle wraparound
        if self.write_pos + data_size <= self.size:
            self.buffer[self.write_pos:self.write_pos + data_size] = data
        else:
            # Split write across buffer boundary
            first_chunk = self.size - self.write_pos
            self.buffer[self.write_pos:] = data[:first_chunk]
            self.buffer[:data_size - first_chunk] = data[first_chunk:]
        
        self.write_pos = (self.write_pos + data_size) % self.size
        
        # Check if buffer is filled
        if not self.filled and self.write_pos <= self.read_pos:
            self.filled = True
    
    def read(self, size: int) -> np.ndarray:
        """Read data from buffer"""
        if not self.filled and self.write_pos <= self.read_pos + size:
            # Not enough data available
            return None
        
        # Handle wraparound
        if self.read_pos + size <= self.size:
            data = self.buffer[self.read_pos:self.read_pos + size].copy()
        else:
            # Split read across buffer boundary
            first_chunk = self.size - self.read_pos
            data = np.zeros((size, self.channels), dtype=np.float32)
            data[:first_chunk] = self.buffer[self.read_pos:]
            data[first_chunk:] = self.buffer[:size - first_chunk]
        
        self.read_pos = (self.read_pos + size) % self.size
        
        return data
    
    def available_samples(self) -> int:
        """Get number of samples available for reading"""
        if not self.filled:
            if self.write_pos > self.read_pos:
                return self.write_pos - self.read_pos
            else:
                return 0
        else:
            return self.size - 1  # Always keep one sample free to detect full state
