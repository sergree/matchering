"""
Test fixtures for the matchering algorithm.

Provides synthetic test signals and reference data for validation.
"""

import numpy as np
from typing import Tuple, Dict, List
from dataclasses import dataclass
from scipy import signal

@dataclass
class TestSignalInfo:
    """Test signal information."""
    description: str
    expected_rms: float
    expected_peak: float
    expected_crest_factor: float
    expected_lufs: float  # Expected LUFS-I value
    expected_freq_peaks: List[float]  # List of expected frequency peaks in Hz

class TestSignals:
    """Generates test signals for matchering algorithm validation."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        # Deterministic RNG for reproducible tests
        self.rng = np.random.default_rng(12345)
        
    def sine_wave(self, frequency: float, duration: float = 1.0,
                 amplitude: float = 1.0) -> np.ndarray:
        """Generate a sine wave test signal.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds
            amplitude: Peak amplitude (0.0 to 1.0)
            
        Returns:
            Stereo audio array of shape (samples, 2)
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        mono = amplitude * np.sin(2 * np.pi * frequency * t)
        return np.column_stack((mono, mono))
        
    def multi_sine(self, frequencies: List[float], amplitudes: List[float],
                  duration: float = 1.0) -> np.ndarray:
        """Generate a signal with multiple sine waves.
        
        Args:
            frequencies: List of frequencies in Hz
            amplitudes: List of amplitudes for each frequency
            duration: Duration in seconds
            
        Returns:
            Stereo audio array of shape (samples, 2)
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        mono = np.zeros_like(t)
        for freq, amp in zip(frequencies, amplitudes):
            mono += amp * np.sin(2 * np.pi * freq * t)
        return np.column_stack((mono, mono))
        
    def white_noise(self, duration: float = 1.0,
                   amplitude: float = 1.0) -> np.ndarray:
        """Generate white noise test signal.
        
        Args:
            duration: Duration in seconds
            amplitude: Peak amplitude (0.0 to 1.0)
            
        Returns:
            Stereo audio array of shape (samples, 2)
        """
        samples = int(self.sample_rate * duration)
        mono = amplitude * (2 * self.rng.random(samples) - 1)
        return np.column_stack((mono, mono))
        
    def pink_noise(self, duration: float = 1.0,
                  amplitude: float = 1.0) -> np.ndarray:
        """Generate pink noise test signal.
        
        Uses a simple IIR filter to approximate pink noise.
        
        Args:
            duration: Duration in seconds
            amplitude: Peak amplitude (0.0 to 1.0)
            
        Returns:
            Stereo audio array of shape (samples, 2)
        """
        samples = int(self.sample_rate * duration)
        white = self.white_noise(duration)
        
        # IIR filter coefficients for pink noise (-3 dB/octave)
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        
        # Apply filter and normalize to target peak amplitude
        mono = signal.lfilter(b, a, white[:, 0])
        mono = amplitude * mono / np.max(np.abs(mono))
        return np.column_stack((mono, mono))
        
    def impulse_response(self, duration: float = 1.0) -> np.ndarray:
        """Generate impulse response test signal.
        
        Args:
            duration: Duration in seconds
            
        Returns:
            Stereo audio array of shape (samples, 2)
        """
        samples = int(self.sample_rate * duration)
        mono = np.zeros(samples)
        mono[0] = 1.0
        return np.column_stack((mono, mono))
        
    def frequency_sweep(self, start_freq: float = 20.0,
                       end_freq: float = 20000.0,
                       duration: float = 1.0) -> np.ndarray:
        """Generate logarithmic frequency sweep (chirp).
        
        Args:
            start_freq: Starting frequency in Hz
            end_freq: Ending frequency in Hz
            duration: Duration in seconds
            
        Returns:
            Stereo audio array of shape (samples, 2)
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        mono = np.sin(2 * np.pi * start_freq * duration / np.log(end_freq/start_freq) * 
                     (np.exp(t * np.log(end_freq/start_freq) / duration) - 1))
        return np.column_stack((mono, mono))
        
    def get_test_signal(self, name: str) -> Tuple[np.ndarray, TestSignalInfo]:
        """Get a standard test signal with known characteristics.
        
        Args:
            name: Name of the test signal to generate
            
        Returns:
            Tuple of (audio_data, signal_info)
        """
        generators = {
            'sine_1k': lambda: (
                self.sine_wave(1000.0, amplitude=0.5),
                TestSignalInfo(
                    description="1 kHz sine wave at -6 dBFS",
                    expected_rms=0.3535,  # -9 dBFS
                    expected_peak=0.5,    # -6 dBFS
                    expected_crest_factor=3.01,
                    expected_lufs=-8.81,  # Measured with our BS.1770 implementation
                    expected_freq_peaks=[1000.0]
                )
            ),
            'dual_sine': lambda: (
                self.multi_sine([100.0, 1000.0], [0.3, 0.3]),
                TestSignalInfo(
                    description="100 Hz + 1 kHz sines at equal amplitude",
                    expected_rms=0.3,     # -10.5 dBFS
                    expected_peak=0.6,    # -4.4 dBFS
                    expected_crest_factor=2.0,
                    expected_lufs=-11.08,  # Measured with our BS.1770 implementation
                    expected_freq_peaks=[100.0, 1000.0]
                )
            ),
            'white_noise': lambda: (
                self.white_noise(amplitude=0.5),
                TestSignalInfo(
                    description="White noise at -6 dBFS RMS",
                    expected_rms=0.289,   # ~0.288675 for uniform [-0.5, 0.5]
                    expected_peak=0.5,    # amplitude limited
                    expected_crest_factor=0.5/0.289,
                    expected_lufs=-7.57,  # Measured with our BS.1770 implementation
                    expected_freq_peaks=[]  # Flat spectrum
                )
            ),
            'pink_noise': lambda: (
                self.pink_noise(amplitude=0.5),
                TestSignalInfo(
                    description="Pink noise at -6 dBFS RMS",
                    expected_rms=0.1335,   # measured RMS after our filter with fixed RNG
                    expected_peak=0.5,    # amplitude limited
                    expected_crest_factor=0.5/0.1335,
                    expected_lufs=-17.30,  # Measured with our BS.1770 implementation
                    expected_freq_peaks=[]  # -3 dB/octave rolloff
                )
            ),
            'sweep': lambda: (
                self.frequency_sweep(duration=5.0),
                TestSignalInfo(
                    description="20 Hz to 20 kHz logarithmic sweep",
                    expected_rms=0.707,   # -3 dBFS
                    expected_peak=1.0,    # 0 dBFS
                    expected_crest_factor=1.414,
                    expected_lufs=-3.0,
                    expected_freq_peaks=[]  # Moving frequency
                )
            ),
        }
        
        if name not in generators:
            raise ValueError(f"Unknown test signal: {name}")
            
        return generators[name]()