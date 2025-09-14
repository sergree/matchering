"""
Dynamics processors implementation.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from ..core.engine import AudioProcessor

@dataclass
class CompressorParams:
    """Compressor parameters."""
    threshold: float = -20.0  # dB
    ratio: float = 2.0       # Compression ratio (1:n)
    attack: float = 0.010    # Attack time in seconds
    release: float = 0.100   # Release time in seconds
    knee: float = 6.0        # Knee width in dB
    makeup_gain: float = 0.0 # Makeup gain in dB

class Compressor(AudioProcessor):
    """Dynamic range compressor."""
    
    def __init__(self, sample_rate: int = 44100, params: Optional[CompressorParams] = None):
        """Initialize compressor.
        
        Args:
            sample_rate: Sample rate in Hz
            params: Optional compressor parameters
        """
        self.sample_rate = sample_rate
        self.params = params or CompressorParams()
        
        # Calculate time constants
        self._attack_coef = np.exp(-1 / (self.sample_rate * self.params.attack))
        self._release_coef = np.exp(-1 / (self.sample_rate * self.params.release))
        
        # State variables
        self._envelope = 0.0
        self._gain_reduction = 0.0
        
    def _process_sample(self, sample: float) -> float:
        """Process single sample.
        
        Args:
            sample: Input sample
            
        Returns:
            Processed sample
        """
        # Calculate sample level in dB
        level = 20 * np.log10(np.abs(sample) + 1e-6)
        
        # Calculate gain reduction using knee
        over = level - self.params.threshold
        if over < -self.params.knee/2:
            gain_reduction = 0.0
        elif over > self.params.knee/2:
            gain_reduction = over - over/self.params.ratio
        else:
            # Smooth knee transition
            gain_reduction = over + (1/self.params.ratio - 1) * \
                           (over + self.params.knee/2)**2 / (2 * self.params.knee)
        
        # Apply envelope following
        coef = self._attack_coef if gain_reduction > self._gain_reduction \
               else self._release_coef
        self._gain_reduction = coef * self._gain_reduction + \
                             (1 - coef) * gain_reduction
        
        # Calculate gain
        gain_db = -self._gain_reduction + self.params.makeup_gain
        gain_linear = np.power(10, gain_db/20)
        
        return sample * gain_linear
        
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer
            
        Returns:
            Processed audio buffer
        """
        output = np.zeros_like(buffer)
        
        # Process each channel
        for ch in range(buffer.shape[1]):
            for i in range(buffer.shape[0]):
                output[i, ch] = self._process_sample(buffer[i, ch])
                
        return output
        
    def reset(self):
        """Reset processor state."""
        self._envelope = 0.0
        self._gain_reduction = 0.0
        
    def update_params(self, params: CompressorParams):
        """Update compressor parameters.
        
        Args:
            params: New parameters
        """
        self.params = params
        self._attack_coef = np.exp(-1 / (self.sample_rate * self.params.attack))
        self._release_coef = np.exp(-1 / (self.sample_rate * self.params.release))


class MultibandCompressor(AudioProcessor):
    """Multi-band compressor with customizable crossover frequencies."""
    
    def __init__(self, sample_rate: int = 44100,
                 crossover_freqs: Tuple[float, ...] = (100.0, 1000.0, 10000.0)):
        """Initialize multi-band compressor.
        
        Args:
            sample_rate: Sample rate in Hz
            crossover_freqs: Crossover frequencies in Hz
        """
        self.sample_rate = sample_rate
        self.crossover_freqs = crossover_freqs
        
        # Create band compressors
        self.compressors = [Compressor(sample_rate) for _ in range(len(crossover_freqs) + 1)]
        
        # Create crossover filters
        self._create_filters()
        self._filter_states = None
        self.reset()
        
    def _create_filters(self):
        """Create crossover filters."""
        from scipy import signal
        
        self._filters = []
        for freq in self.crossover_freqs:
            # Create 4th order Linkwitz-Riley filters (cascaded 2nd order Butterworth)
            nyq = self.sample_rate * 0.5
            freq_norm = freq / nyq
            
            # Low-pass
            b_lp, a_lp = signal.butter(2, freq_norm, btype='low')
            self._filters.append((b_lp, a_lp))
            
            # High-pass
            b_hp, a_hp = signal.butter(2, freq_norm, btype='high')
            self._filters.append((b_hp, a_hp))
            
    def process(self, buffer: np.ndarray) -> np.ndarray:
        """Process audio buffer.
        
        Args:
            buffer: Input audio buffer
            
        Returns:
            Processed audio buffer
        """
        from scipy import signal
        
        output = np.zeros_like(buffer)
        num_bands = len(self.compressors)
        
        # Process each band
        for band in range(num_bands):
            band_output = buffer.copy()
            
            if band == 0:
                # Low band - apply low-pass filters
                for i in range(len(self.crossover_freqs)):
                    b, a = self._filters[i * 2]  # Get low-pass filter
                    for ch in range(buffer.shape[1]):
                        band_output[:, ch], self._filter_states[band][i][ch] = \
                            signal.lfilter(b, a, band_output[:, ch],
                                         zi=self._filter_states[band][i][ch])
                                         
            elif band == num_bands - 1:
                # High band - apply high-pass filters
                for i in range(len(self.crossover_freqs)):
                    b, a = self._filters[i * 2 + 1]  # Get high-pass filter
                    for ch in range(buffer.shape[1]):
                        band_output[:, ch], self._filter_states[band][i][ch] = \
                            signal.lfilter(b, a, band_output[:, ch],
                                         zi=self._filter_states[band][i][ch])
                                         
            else:
                # Mid band - apply low-pass and high-pass filters
                # Low-pass from higher crossover
                b, a = self._filters[band * 2]
                for ch in range(buffer.shape[1]):
                    band_output[:, ch], self._filter_states[band][0][ch] = \
                        signal.lfilter(b, a, band_output[:, ch],
                                     zi=self._filter_states[band][0][ch])
                                     
                # High-pass from lower crossover
                b, a = self._filters[band * 2 - 1]
                for ch in range(buffer.shape[1]):
                    band_output[:, ch], self._filter_states[band][1][ch] = \
                        signal.lfilter(b, a, band_output[:, ch],
                                     zi=self._filter_states[band][1][ch])
                                     
            # Apply band compression
            band_output = self.compressors[band].process(band_output)
            output += band_output
            
        return output
        
    def reset(self):
        """Reset processor state."""
        # Reset compressors
        for comp in self.compressors:
            comp.reset()
            
        # Reset filter states
        num_bands = len(self.compressors)
        self._filter_states = []
        
        for band in range(num_bands):
            if band == 0 or band == num_bands - 1:
                # Outer bands need states for all crossovers
                states = []
                for _ in range(len(self.crossover_freqs)):
                    states.append([np.zeros(2) for _ in range(2)])  # For stereo
                self._filter_states.append(states)
            else:
                # Mid bands only need states for adjacent crossovers
                states = []
                for _ in range(2):  # Low-pass and high-pass
                    states.append([np.zeros(2) for _ in range(2)])  # For stereo
                self._filter_states.append(states)
                
    def update_params(self, band: int, params: CompressorParams):
        """Update band compressor parameters.
        
        Args:
            band: Band index
            params: New parameters
        """
        if 0 <= band < len(self.compressors):
            self.compressors[band].update_params(params)