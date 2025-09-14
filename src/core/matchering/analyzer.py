"""
Frequency analysis for matchering algorithm.

This module handles all frequency-domain analysis including:
- Spectrum analysis
- Band splitting
- RMS and loudness measurement
- Peak detection
"""

import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from scipy import signal

@dataclass
class FrequencyBand:
    """Represents a frequency band for analysis."""
    start_freq: float
    end_freq: float
    center_freq: float

class FrequencyAnalyzer:
    """Handles frequency-domain analysis of audio signals."""
    
    def __init__(self, sample_rate: int = 44100):
        """Initialize analyzer.
        
        Args:
            sample_rate: Sample rate in Hz
        """
        self.sample_rate = sample_rate
        self._window_size = 2048  # Default FFT size
        self._hop_size = self._window_size // 2  # 50% overlap
        self._init_frequency_bands()
        
        # Cache for last computed spectrum and frequency axis
        self._last_freqs = None
        self._last_spectrum = None
        
    def _init_frequency_bands(self):
        """Initialize frequency band division.
        
        Creates roughly one-octave bands across audio range.
        """
        # Start at ~20 Hz
        start_freq = 20.0
        self._bands: List[FrequencyBand] = []
        
        while start_freq < 20000.0:
            # Calculate band frequencies
            end_freq = start_freq * 2  # One octave
            # Cap the last band at 20 kHz
            if end_freq > 20000.0:
                end_freq = 20000.0
            center_freq = np.sqrt(start_freq * end_freq)
            
            self._bands.append(FrequencyBand(
                start_freq=start_freq,
                end_freq=end_freq,
                center_freq=center_freq
            ))
            
            if end_freq >= 20000.0:
                break
            start_freq = end_freq
            
    def get_frequency_bands(self) -> List[FrequencyBand]:
        """Get frequency band information.
        
        Returns:
            List of frequency bands
        """
        return self._bands
        
    def frequency_to_bin(self, freq: float) -> int:
        """Convert frequency to FFT bin number.
        
        Args:
            freq: Frequency in Hz
            
        Returns:
            FFT bin number
        """
        return int(freq * self._window_size / self.sample_rate)
        
    def get_frequencies(self) -> np.ndarray:
        """Get frequencies for FFT bins.
        
        If a spectrum was recently computed, returns its exact frequency axis.
        Otherwise returns theoretical frequencies for current window size.
        
        Returns:
            Array of frequencies in Hz
        """
        if self._last_freqs is not None:
            return self._last_freqs
        return np.fft.rfftfreq(self._window_size, 1/self.sample_rate)
        
    def analyze_spectrum(self, audio_data: np.ndarray,
                        window_size: Optional[int] = None) -> np.ndarray:
        """Analyze frequency spectrum of audio data.
        
        Uses Welch's method for spectrum estimation with configurable windowing
        and overlap. Zero-pads to improve frequency resolution for low frequencies.
        
        Args:
            audio_data: Audio data array of shape (samples, channels)
            window_size: Optional override for FFT size
            
        Returns:
            Magnitude spectrum array
        """
        if window_size is not None:
            self._window_size = window_size
            self._hop_size = window_size // 2  # 50% overlap for Welch
            
        # Process each channel
        spectra = []
        for ch in range(audio_data.shape[1]):
            # Zero-pad for better low frequency resolution
            n_pad = len(audio_data) * 4  # Lots of padding for better resolution
            padded = np.pad(audio_data[:, ch], (n_pad, n_pad), mode='reflect')
            
            # Apply longer window for better resolution
            window_size = min(16384, len(padded))  # Use large window for better resolution
            if window_size != self._window_size:
                self._window_size = window_size
                self._hop_size = window_size // 2
            
            # Compute PSD using Welch's method
            freqs, psd = signal.welch(
                padded,
                fs=self.sample_rate,
                window='hann',  # Good balance of main lobe and side lobes
                nperseg=self._window_size,
                noverlap=self._hop_size,
                nfft=self._window_size,  # Keep consistent with frequency grid
                detrend=False,
                scaling='spectrum'  # To match magnitude spectrum
            )
            
            # Convert to magnitude spectrum
            spectrum = np.sqrt(psd * self._window_size)
            
            # Cache frequency axis from first channel
            if ch == 0:
                self._last_freqs = freqs
            
            spectra.append(spectrum)
            
        # Sum channels (preserve power) and normalize
        spectrum = np.sqrt(np.mean([s**2 for s in spectra], axis=0))
        return spectrum / np.max(spectrum)  # Normalize to 1.0
        
    def find_peak_frequencies(self, spectrum: np.ndarray,
                            threshold: float = -60) -> List[float]:
        """Find peak frequencies in spectrum.
        
        Uses adaptive prominence threshold based on local noise floor to improve
        detection of both strong and weak peaks. Peak separation is adjusted
        based on frequency to handle both low and high frequency components.
        
        Args:
            spectrum: Magnitude spectrum array
            threshold: Detection threshold in dB
            
        Returns:
            List of peak frequencies in Hz
        """
        freqs = self.get_frequencies()
        
        # Convert threshold to linear and get spectrum in dB
        threshold_linear = 10 ** (threshold / 20)
        spectrum_db = 20 * np.log10(spectrum + 1e-10)
        
        # Calculate local noise floor (with shorter window at low freq)
        noise_floor = np.zeros_like(spectrum_db)
        # Shorter window below 500 Hz for better low frequency detection
        low_freq_mask = freqs < 500
        high_freq_mask = ~low_freq_mask
        
        # Low frequency noise floor (short window)
        if np.any(low_freq_mask):
            window_low = max(5, len(spectrum[low_freq_mask]) // 10)
            if window_low % 2 == 0:
                window_low += 1
            noise_floor[low_freq_mask] = signal.medfilt(
                spectrum_db[low_freq_mask], window_low)
        
        # High frequency noise floor (longer window)
        if np.any(high_freq_mask):
            window_high = len(spectrum[high_freq_mask]) // 20
            if window_high % 2 == 0:
                window_high += 1
            noise_floor[high_freq_mask] = signal.medfilt(
                spectrum_db[high_freq_mask], window_high)
        
        # Adaptive prominence threshold
        min_prominence = 20  # dB above noise floor
        prominence_thresh = np.maximum(noise_floor + min_prominence, threshold)
        prominence_linear = 10 ** (prominence_thresh / 20)
        
        # Find peaks with adaptive criteria
        peaks, props = signal.find_peaks(
            spectrum,
            height=threshold_linear,
            prominence=prominence_linear,
            distance=20,  # Allow fairly close peaks
            width=1  # Require minimal width to avoid noise
        )
        
        if len(peaks) == 0:
            return []  # No peaks found
            
        # Calculate relative prominence threshold (fraction of max peak)
        max_prominence = np.max(props['prominences'])
        prominence_thresh = max_prominence * 0.05  # Allow peaks down to -26 dB relative
        
        # Keep peaks with sufficient prominence and sort by frequency
        valid_peaks = props['prominences'] >= prominence_thresh
        peak_indices = peaks[valid_peaks][np.argsort(peaks[valid_peaks])]
        
        # Sort peaks by magnitude
        peak_mags = spectrum[peak_indices]
        sorted_idx = np.argsort(peak_mags)[::-1]
        peak_indices = peak_indices[sorted_idx]
        
        # Keep only significant peaks (relative to max)
        max_peak = np.max(spectrum[peak_indices])
        significant = spectrum[peak_indices] > max_peak * threshold_linear
        peak_indices = peak_indices[significant]
        
        # Convert to frequencies
        return [freqs[i] for i in peak_indices]
        
    def calculate_band_energies(self, audio_data: np.ndarray) -> np.ndarray:
        """Calculate energy in each frequency band.
        
        Normalizes by bandwidth to reduce bias toward wider bands.
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Array of band energies
        """
        # Get spectrum
        spectrum = self.analyze_spectrum(audio_data)
        freqs = self.get_frequencies()
        
        # Calculate energy in each band
        energies = []
        for band in self._bands:
            # Get frequency range for band
            mask = (freqs >= band.start_freq) & (freqs <= band.end_freq)
            band_spectrum = spectrum[mask]
            band_freqs = freqs[mask]
            if len(band_freqs) == 0:
                energies.append(0.0)
                continue
            
            # Calculate band power with smoother weighting
            # Use Hann window for smoother band transitions
            band_width = len(band_spectrum)
            if len(band_freqs) > 1:
                # Use power per octave normalization
                octave_width = np.log2(band_freqs[-1] / band_freqs[0])
                # Calculate power density spectrum (power/Hz)
                df = band_freqs[1] - band_freqs[0]
                psd = band_spectrum**2 / df
                # Weight by frequency to account for logarithmic perception
                weighted_psd = psd * np.sqrt(band_freqs / 1000.0)
                # Integrate over log-frequency
                power = np.trapezoid(weighted_psd, np.log2(band_freqs))
                # Normalize by octave width
                energy = np.sqrt(power / max(octave_width, 1e-6))
            else:
                energy = band_spectrum[0] if len(band_spectrum) > 0 else 0.0
            energies.append(energy)
            
        # Normalize energies using frequency-dependent scaling
        energies = np.array(energies)
        if np.max(energies) > 0:
            # Normalize and apply mild compression
            energies = energies / np.max(energies)
            energies = np.power(energies, 0.8)
        return energies
        
    def calculate_rms(self, audio_data: np.ndarray) -> float:
        """Calculate RMS level of audio data.
        
        Calculates RMS per channel then averages to preserve power relationships.
        
        Args:
            audio_data: Audio data array
            
        Returns:
            RMS level
        """
        # Square all samples, average per channel, take sqrt for RMS
        squared = audio_data ** 2
        # Note: We want the average power across all samples
        mean_power = np.mean(squared)
        return float(np.sqrt(mean_power))
        
    def calculate_peak(self, audio_data: np.ndarray) -> float:
        """Calculate peak level of audio data.
        
        Takes maximum absolute value across all channels.
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Peak level
        """
        channel_peaks = np.max(np.abs(audio_data), axis=0)
        return float(np.max(channel_peaks))
        
    def calculate_lufs(self, audio_data: np.ndarray) -> float:
        """Calculate LUFS-I loudness of audio data.
        
        Implements ITU-R BS.1770-4 integrated loudness measurement with K-weighting
        and gating as specified in the standard.
        
        Args:
            audio_data: Audio data array
            
        Returns:
            LUFS-I level
        """
        # BS.1770-4 K-weighting filters (pre-filter + RLB)
        # High-shelf +4dB at 1681 Hz (pre-filter)
        b_high = [1.53512485958697, -2.69169618940638, 1.19839281085285]
        a_high = [1.0, -1.69065929318241, 0.73248077421585]
        
        # High-pass filter at 38 Hz (RLB weighting)
        b_hp = [1.0, -2.0, 1.0]
        a_hp = [1.0, -1.99004745483398, 0.99007225036621]
        
        # Channel weights for stereo material per ITU-R BS.1770-4
        self._channel_weights = [1.0, 1.0]  # L/R channels
        
        # Apply filters to each channel
        gated_powers = []
        for ch in range(audio_data.shape[1]):
            # Apply ITU-R BS.1770 K-weighting per channel
            channel = audio_data[:, ch] * self._channel_weights[ch]
            stage1 = signal.lfilter(b_high, a_high, channel)  # Pre-filter
            stage2 = signal.lfilter(b_hp, a_hp, stage1)      # RLB weighting
            
            # Calculate power in 400ms blocks (overlap 75%)
            block_size = int(0.4 * self.sample_rate)
            hop_size = block_size // 4
            n_blocks = (len(stage2) - block_size) // hop_size + 1
            
            powers = np.zeros(n_blocks)
            for i in range(n_blocks):
                start = i * hop_size
                block = stage2[start:start + block_size]
                powers[i] = np.mean(block ** 2)
            
            gated_powers.append(powers)
            
        # Average powers across channels with BS.1770 weights
        if len(gated_powers) == 1:  # Mono
            powers = gated_powers[0]
        elif len(gated_powers) == 2:  # Stereo
            # BS.1770 stereo weights
            powers = 1.0 * gated_powers[0] + 1.0 * gated_powers[1]  # Equal weights for L/R
            powers *= 0.5  # Scale to maintain calibration
        else:
            # Default to equal weights for other channel counts
            powers = np.mean(gated_powers, axis=0)
        
        # First gate: -70 LUFS absolute threshold
        abs_thresh = 10 ** (-70/10)  # -70 LUFS in linear scale
        abs_mask = powers > abs_thresh
        if not np.any(abs_mask):
            return -70.0  # If all below absolute gate
            
        # Calculate relative threshold (ungated LUFS)
        ungated_loudness = -0.691 + 10 * np.log10(np.mean(powers[abs_mask]))
        rel_thresh = 10 ** ((ungated_loudness - 10) / 10)  # -10 LU relative gate
        
        # Apply both gates
        gated_mask = (powers > abs_thresh) & (powers > rel_thresh)
        if not np.any(gated_mask):
            return -70.0  # If all below relative gate
            
        # Calculate gated LUFS-I value per BS.1770-4
        lufs = -0.691 + 10 * np.log10(np.mean(powers[gated_mask]))
        
        return lufs
