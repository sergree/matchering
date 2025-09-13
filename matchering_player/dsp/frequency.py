# -*- coding: utf-8 -*-

"""
Real-time Frequency Matching for Matchering Player
Adapted from Matchering 2.0's frequency analysis for streaming chunks
"""

import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from scipy import signal, interpolate
import json
from pathlib import Path

from .basic import (
    rms, lr_to_ms, ms_to_lr, is_stereo
)
from ..core.config import PlayerConfig


class FrequencyProfile:
    """Stores frequency characteristics of a reference track"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = Path(file_path).stem

        # Frequency characteristics
        self.eq_bands: List[Dict] = []  # List of EQ band settings
        self.freq_response_mid: Optional[np.ndarray] = None
        self.freq_response_side: Optional[np.ndarray] = None
        self.frequencies: Optional[np.ndarray] = None

        # Analysis metadata
        self.sample_rate: Optional[int] = None
        self.analysis_complete = False

    def to_dict(self) -> dict:
        """Serialize to dictionary for caching"""
        return {
            'file_path': self.file_path,
            'filename': self.filename,
            'eq_bands': self.eq_bands,
            'sample_rate': int(self.sample_rate) if self.sample_rate else None,
            'analysis_complete': self.analysis_complete,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FrequencyProfile':
        """Deserialize from dictionary"""
        profile = cls(data['file_path'])
        profile.filename = data['filename']
        profile.eq_bands = data.get('eq_bands', [])
        profile.sample_rate = data.get('sample_rate')
        profile.analysis_complete = data.get('analysis_complete', False)
        return profile


class ParametricEQ:
    """Real-time parametric EQ with multiple bands"""

    def __init__(self, sample_rate: int, num_bands: int = 8):
        self.sample_rate = sample_rate
        self.num_bands = num_bands

        # Standard frequency bands (similar to professional EQ)
        self.band_frequencies = [
            60,    # Sub bass
            120,   # Bass
            250,   # Low mids
            500,   # Mid bass
            1000,  # Mids
            2000,  # Upper mids
            4000,  # Presence
            8000   # Brilliance
        ]

        # Initialize biquad filters for each band
        self.filters_mid = []
        self.filters_side = []

        for freq in self.band_frequencies:
            # Mid channel filters
            self.filters_mid.append({
                'b': np.array([1.0, 0.0, 0.0]),  # Numerator coefficients
                'a': np.array([1.0, 0.0, 0.0]),  # Denominator coefficients
                'z': np.zeros(2),  # State variables
                'freq': freq,
                'gain': 0.0,  # dB
                'Q': 1.0
            })

            # Side channel filters (copy)
            self.filters_side.append({
                'b': np.array([1.0, 0.0, 0.0]),
                'a': np.array([1.0, 0.0, 0.0]),
                'z': np.zeros(2),
                'freq': freq,
                'gain': 0.0,
                'Q': 1.0
            })

    def design_bell_filter(self, freq: float, gain_db: float, Q: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """Design a bell (peaking) filter using biquad topology"""
        if abs(gain_db) < 0.1:  # No significant gain change
            return np.array([1.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0])

        # Convert to radians
        w0 = 2 * np.pi * freq / self.sample_rate
        cos_w0 = np.cos(w0)
        sin_w0 = np.sin(w0)

        # Calculate gain
        A = 10 ** (gain_db / 40)  # Linear gain
        alpha = sin_w0 / (2 * Q)

        # Biquad coefficients for peaking EQ
        b0 = 1 + alpha * A
        b1 = -2 * cos_w0
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * cos_w0
        a2 = 1 - alpha / A

        # Normalize by a0
        b = np.array([b0, b1, b2]) / a0
        a = np.array([a0, a1, a2]) / a0

        return b, a

    def update_eq_settings(self, eq_bands: List[Dict]):
        """Update EQ settings from band configuration"""
        for i, band_config in enumerate(eq_bands):
            if i >= len(self.filters_mid):
                break

            freq = band_config.get('frequency', self.band_frequencies[i])
            gain = band_config.get('gain', 0.0)
            Q = band_config.get('Q', 1.0)

            # Update mid channel filter
            b, a = self.design_bell_filter(freq, gain, Q)
            self.filters_mid[i]['b'] = b
            self.filters_mid[i]['a'] = a
            self.filters_mid[i]['gain'] = gain
            self.filters_mid[i]['Q'] = Q

            # Update side channel filter (could be different in future)
            self.filters_side[i]['b'] = b
            self.filters_side[i]['a'] = a
            self.filters_side[i]['gain'] = gain
            self.filters_side[i]['Q'] = Q

    def process_chunk(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Apply EQ to audio chunk"""
        if not is_stereo(audio_chunk):
            return audio_chunk

        # Convert to Mid-Side
        mid, side = lr_to_ms(audio_chunk)

        # Apply EQ to mid channel
        processed_mid = mid.copy()
        for filt in self.filters_mid:
            if abs(filt['gain']) > 0.1:  # Only process if significant gain
                processed_mid, filt['z'] = signal.lfilter(
                    filt['b'], filt['a'], processed_mid, zi=filt['z']
                )

        # Apply EQ to side channel
        processed_side = side.copy()
        for filt in self.filters_side:
            if abs(filt['gain']) > 0.1:
                processed_side, filt['z'] = signal.lfilter(
                    filt['b'], filt['a'], processed_side, zi=filt['z']
                )

        # Convert back to L/R
        return ms_to_lr(processed_mid, processed_side)

    def reset(self):
        """Reset filter states"""
        for filt in self.filters_mid + self.filters_side:
            filt['z'] = np.zeros(2)


class RealtimeFrequencyMatcher:
    """Real-time frequency matching processor"""

    def __init__(self, config: PlayerConfig):
        self.config = config
        self.enabled = True
        self.bypass_mode = False

        # Frequency analysis parameters
        self.fft_size = 4096  # Enough resolution for frequency analysis
        self.overlap_ratio = 0.5
        self.hop_size = int(self.fft_size * (1 - self.overlap_ratio))

        # Analysis buffers
        self.analysis_buffer_mid = np.zeros(self.fft_size)
        self.analysis_buffer_side = np.zeros(self.fft_size)
        self.buffer_position = 0

        # EQ processor
        self.parametric_eq = ParametricEQ(config.sample_rate)

        # Reference profile
        self.reference_profile: Optional[FrequencyProfile] = None

        # Analysis state
        self.spectrum_history_mid = []
        self.spectrum_history_side = []
        self.analysis_chunks_processed = 0
        self.adaptation_rate = 0.1  # How fast to adapt to spectral changes

    def load_reference(self, reference_file_path: str) -> bool:
        """Load and analyze reference track for frequency matching"""
        try:
            print(f"🎛️ Analyzing frequency characteristics: {Path(reference_file_path).name}")
            profile = self._analyze_frequency_profile(reference_file_path)

            if profile and profile.analysis_complete:
                self.reference_profile = profile

                # Update EQ with reference characteristics
                self.parametric_eq.update_eq_settings(profile.eq_bands)

                print(f"✅ Frequency profile loaded with {len(profile.eq_bands)} EQ bands")
                return True

            return False

        except Exception as e:
            print(f"❌ Error loading frequency reference: {e}")
            return False

    def _analyze_frequency_profile(self, reference_file_path: str) -> Optional[FrequencyProfile]:
        """Analyze reference track to extract frequency characteristics"""
        try:
            # Import file loader
            from ..utils.file_loader import AudioFileLoader

            # Load reference audio
            loader = AudioFileLoader(
                target_sample_rate=self.config.sample_rate,
                target_channels=2
            )

            reference_audio, sample_rate = loader.load_audio_file(reference_file_path)
            print(f"🔍 Analyzing frequency spectrum ({len(reference_audio)} samples)")

            # Convert to Mid-Side for analysis
            mid, side = lr_to_ms(reference_audio)

            # Perform FFT analysis
            frequencies = np.fft.rfftfreq(self.fft_size, 1/sample_rate)

            # Calculate average spectrum using overlapping windows
            mid_spectra = []
            side_spectra = []

            for i in range(0, len(mid) - self.fft_size, self.hop_size):
                window = signal.windows.hann(self.fft_size)

                # Mid channel
                mid_chunk = mid[i:i + self.fft_size] * window
                mid_fft = np.abs(np.fft.rfft(mid_chunk))
                mid_spectra.append(mid_fft)

                # Side channel
                side_chunk = side[i:i + self.fft_size] * window
                side_fft = np.abs(np.fft.rfft(side_chunk))
                side_spectra.append(side_fft)

            # Average spectra
            avg_mid_spectrum = np.mean(mid_spectra, axis=0)
            avg_side_spectrum = np.mean(side_spectra, axis=0)

            # Create frequency profile
            profile = FrequencyProfile(reference_file_path)
            profile.sample_rate = sample_rate
            profile.frequencies = frequencies
            profile.freq_response_mid = avg_mid_spectrum
            profile.freq_response_side = avg_side_spectrum

            # Extract EQ band settings
            profile.eq_bands = self._extract_eq_bands(frequencies, avg_mid_spectrum, avg_side_spectrum)
            profile.analysis_complete = True

            print(f"📊 Frequency analysis complete:")
            print(f"   EQ Bands: {len(profile.eq_bands)}")
            for band in profile.eq_bands:
                print(f"   {band['frequency']:4.0f}Hz: {band['gain']:+5.1f} dB")

            return profile

        except Exception as e:
            print(f"❌ Error analyzing frequency profile: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_eq_bands(self, frequencies: np.ndarray, mid_spectrum: np.ndarray,
                         side_spectrum: np.ndarray) -> List[Dict]:
        """Extract parametric EQ settings from frequency spectrum"""

        # Target frequencies for EQ bands
        target_freqs = [60, 120, 250, 500, 1000, 2000, 4000, 8000]
        eq_bands = []

        # Calculate reference level (around 1kHz)
        ref_idx = np.argmin(np.abs(frequencies - 1000))
        ref_level = mid_spectrum[ref_idx]

        for freq in target_freqs:
            # Find closest frequency bin
            freq_idx = np.argmin(np.abs(frequencies - freq))

            if freq_idx < len(mid_spectrum):
                # Calculate gain relative to reference
                band_level = mid_spectrum[freq_idx]
                gain_linear = band_level / max(ref_level, 1e-10)
                gain_db = 20 * np.log10(max(gain_linear, 1e-10))

                # Limit gain adjustments to reasonable range
                gain_db = np.clip(gain_db, -12, +12)

                eq_bands.append({
                    'frequency': freq,
                    'gain': float(gain_db),
                    'Q': 1.0  # Standard Q factor
                })

        return eq_bands

    def process_chunk(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Process audio chunk with frequency matching"""
        if not self.enabled or self.bypass_mode or not self.reference_profile:
            return audio_chunk

        if not is_stereo(audio_chunk):
            return audio_chunk

        try:
            # Apply parametric EQ
            processed_chunk = self.parametric_eq.process_chunk(audio_chunk)

            # Update analysis buffers for adaptive processing (future enhancement)
            self._update_analysis_buffers(audio_chunk)

            return processed_chunk

        except Exception as e:
            print(f"⚠️ Error in frequency processing: {e}")
            return audio_chunk

    def _update_analysis_buffers(self, audio_chunk: np.ndarray):
        """Update analysis buffers for adaptive EQ (future enhancement)"""
        # This would analyze current spectral content and adapt EQ in real-time
        # For now, we use static EQ settings from reference analysis
        pass

    def set_enabled(self, enabled: bool):
        """Enable or disable frequency matching"""
        self.enabled = enabled
        if not enabled:
            self.parametric_eq.reset()

    def set_bypass(self, bypass: bool):
        """Set bypass mode"""
        self.bypass_mode = bypass
        if bypass:
            self.parametric_eq.reset()

    def get_eq_settings(self) -> List[Dict]:
        """Get current EQ band settings"""
        if self.reference_profile:
            return self.reference_profile.eq_bands
        return []

    def set_eq_band(self, band_index: int, frequency: float, gain: float, Q: float = 1.0):
        """Manually set EQ band parameters"""
        if self.reference_profile and band_index < len(self.reference_profile.eq_bands):
            self.reference_profile.eq_bands[band_index] = {
                'frequency': frequency,
                'gain': gain,
                'Q': Q
            }
            self.parametric_eq.update_eq_settings(self.reference_profile.eq_bands)

    def get_current_stats(self) -> dict:
        """Get current frequency matching statistics"""
        stats = {
            'enabled': self.enabled,
            'bypass_mode': self.bypass_mode,
            'reference_loaded': self.reference_profile is not None,
            'eq_bands_count': len(self.reference_profile.eq_bands) if self.reference_profile else 0,
        }

        if self.reference_profile:
            stats['reference_filename'] = self.reference_profile.filename
            stats['eq_bands'] = self.reference_profile.eq_bands

        return stats