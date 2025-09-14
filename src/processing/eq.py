"""
Equalizer processor implementation.
"""

import numpy as np
from typing import List, Optional, Tuple
from scipy import signal
from dataclasses import dataclass
from ..core.engine import AudioProcessor

@dataclass
class EQBand:
    """Equalizer band configuration."""
    frequency: float  # Center frequency in Hz
    gain: float      # Gain in dB
    q: float        # Q factor (bandwidth)
    enabled: bool = True

class Equalizer(AudioProcessor):
    """Multi-band parametric equalizer."""
    
    def __init__(self, sample_rate: int = 44100):
        """Initialize equalizer.
        
        Args:
            sample_rate: Sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.bands: List[EQBand] = []
        self._coefficients: List[Tuple[np.ndarray, np.ndarray]] = []
        self._state: List[np.ndarray] = []
        
    def add_band(self, frequency: float, gain: float = 0.0, q: float = 1.0) -> EQBand:
        """Add equalizer band.
        
        Args:
            frequency: Center frequency in Hz
            gain: Gain in dB
            q: Q factor (bandwidth)
            
        Returns:
            Created EQ band
        """
        band = EQBand(frequency, gain, q)
        self.bands.append(band)
        self._update_coefficients()
        return band
        
    def remove_band(self, band: EQBand):
        """Remove equalizer band.
        
        Args:
            band: Band to remove
        """
        if band in self.bands:
            self.bands.remove(band)
            self._update_coefficients()
            
    def set_band_gain(self, band: EQBand, gain: float):
        """Set band gain.
        
        Args:
            band: Band to modify
            gain: New gain in dB
        """
        if band in self.bands:
            band.gain = gain
            self._update_coefficients()
            
    def set_band_q(self, band: EQBand, q: float):
        """Set band Q factor.
        
        Args:
            band: Band to modify
            q: New Q factor
        """
        if band in self.bands:
            band.q = q
            self._update_coefficients()
            
    def set_band_enabled(self, band: EQBand, enabled: bool):
        """Enable/disable band.
        
        Args:
            band: Band to modify
            enabled: Enable state
        """
        if band in self.bands:
            band.enabled = enabled
            self._update_coefficients()
            
    def _update_coefficients(self):
        """Update filter coefficients."""
        self._coefficients = []
        self._state = []
        
        for band in self.bands:
            if band.enabled and abs(band.gain) > 0.01:  # Skip if disabled or no gain
                # Convert parameters
                w0 = 2 * np.pi * band.frequency / self.sample_rate
                alpha = np.sin(w0) / (2 * band.q)
                A = np.power(10, band.gain / 40)  # Convert dB to linear gain
                
                # Calculate coefficients
                b0 = 1 + alpha * A
                b1 = -2 * np.cos(w0)
                b2 = 1 - alpha * A
                a0 = 1 + alpha / A
                a1 = -2 * np.cos(w0)
                a2 = 1 - alpha / A
                
                # Normalize coefficients
                b = np.array([b0, b1, b2]) / a0
                a = np.array([1.0, a1, a2]) / a0
                
                self._coefficients.append((b, a))
                self._state.append(np.zeros((2, 2)))  # For stereo processing
                
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer
            
        Returns:
            Processed audio buffer
        """
        output = buffer.copy()
        
        # Apply each band's filter
        for i, (b, a) in enumerate(self._coefficients):
            # Process each channel
            for ch in range(buffer.shape[1]):
                output[:, ch], self._state[i][ch] = signal.lfilter(
                    b, a,
                    output[:, ch],
                    zi=self._state[i][ch]
                )
                
        return output
        
    def reset(self):
        """Reset processor state."""
        if self._state:
            for state in self._state:
                state.fill(0)


class ThreeBandEQ(Equalizer):
    """Simple three-band equalizer (low, mid, high)."""
    
    def __init__(self, sample_rate: int = 44100):
        """Initialize three-band EQ.
        
        Args:
            sample_rate: Sample rate in Hz
        """
        super().__init__(sample_rate)
        
        # Add default bands
        self.low = self.add_band(100.0, 0.0, 0.707)    # Low shelf
        self.mid = self.add_band(1000.0, 0.0, 0.707)   # Mid peak
        self.high = self.add_band(10000.0, 0.0, 0.707) # High shelf


class GraphicEQ(Equalizer):
    """10-band graphic equalizer."""
    
    BAND_FREQUENCIES = [
        31.25,   # Sub-bass
        62.5,    # Bass
        125,     # Low-mids
        250,
        500,
        1000,    # Mids
        2000,
        4000,    # High-mids
        8000,    # Presence
        16000    # Air
    ]
    
    def __init__(self, sample_rate: int = 44100):
        """Initialize graphic EQ.
        
        Args:
            sample_rate: Sample rate in Hz
        """
        super().__init__(sample_rate)
        
        # Add bands with constant Q
        self.bands_by_freq = {}
        for freq in self.BAND_FREQUENCIES:
            band = self.add_band(freq, 0.0, 1.4)  # Q of 1.4 for minimal overlap
            self.bands_by_freq[freq] = band
            
    def set_gains(self, gains: List[float]):
        """Set all band gains at once.
        
        Args:
            gains: List of gains in dB (must match number of bands)
        """
        if len(gains) != len(self.BAND_FREQUENCIES):
            raise ValueError("Number of gains must match number of bands")
            
        for freq, gain in zip(self.BAND_FREQUENCIES, gains):
            self.set_band_gain(self.bands_by_freq[freq], gain)