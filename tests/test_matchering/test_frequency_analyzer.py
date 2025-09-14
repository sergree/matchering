"""
Tests for the frequency analyzer component.
"""

import pytest
import numpy as np
from tests.test_matchering.fixtures import TestSignals
from src.core.matchering.analyzer import FrequencyAnalyzer

@pytest.fixture
def signals():
    """Create test signal generator."""
    return TestSignals(sample_rate=44100)

@pytest.fixture
def analyzer():
    """Create frequency analyzer instance."""
    return FrequencyAnalyzer(sample_rate=44100)

def test_single_sine_spectrum(signals, analyzer):
    """Test frequency analysis of a single sine wave."""
    # Get 1 kHz test signal
    audio_data, info = signals.get_test_signal('sine_1k')
    
    # Analyze spectrum
    spectrum = analyzer.analyze_spectrum(audio_data)
    
    # Get frequency peak
    peak_freq = analyzer.find_peak_frequencies(spectrum, threshold=-60)[0]
    
    # Should find 1 kHz peak within 1% tolerance
    assert abs(peak_freq - 1000.0) < 10.0

def test_dual_sine_spectrum(signals, analyzer):
    """Test frequency analysis of dual sine waves."""
    # Get dual sine test signal
    audio_data, info = signals.get_test_signal('dual_sine')
    
    # Analyze spectrum
    spectrum = analyzer.analyze_spectrum(audio_data)
    
    # Get frequency peaks
    peaks = analyzer.find_peak_frequencies(spectrum, threshold=-60)
    
    # Should find both peaks within 1% tolerance
    assert len(peaks) == 2
    assert any(abs(p - 100.0) < 1.0 for p in peaks)
    assert any(abs(p - 1000.0) < 10.0 for p in peaks)
    
    # Peaks should have similar magnitude (within 1 dB)
    mags = [spectrum[analyzer.frequency_to_bin(f)] for f in peaks]
    assert abs(20 * np.log10(mags[0] / mags[1])) < 1.0

def test_white_noise_spectrum(signals, analyzer):
    """Test frequency analysis of white noise."""
    # Get white noise test signal
    audio_data, info = signals.get_test_signal('white_noise')
    
    # Analyze spectrum
    spectrum = analyzer.analyze_spectrum(audio_data)
    
    # Calculate spectrum slope (should be approximately flat)
    freqs = analyzer.get_frequencies()
    valid_range = (freqs > 20) & (freqs < 20000)  # Audio range only
    slope = np.polyfit(np.log10(freqs[valid_range]),
                      20 * np.log10(spectrum[valid_range]), 1)[0]
    
    # Slope should be close to 0 dB/decade
    assert abs(slope) < 1.0

def test_pink_noise_spectrum(signals, analyzer):
    """Test frequency analysis of pink noise."""
    # Get pink noise test signal
    audio_data, info = signals.get_test_signal('pink_noise')
    
    # Analyze spectrum
    spectrum = analyzer.analyze_spectrum(audio_data)
    
    # Calculate spectrum slope (should be approximately -10 dB/decade)
    freqs = analyzer.get_frequencies()
    valid_range = (freqs > 20) & (freqs < 20000)  # Audio range only
    slope = np.polyfit(np.log10(freqs[valid_range]),
                      20 * np.log10(spectrum[valid_range]), 1)[0]
    
    # Slope should be close to -10 dB/decade
    assert abs(slope + 10) < 2.0

def test_sweep_spectrum(signals, analyzer):
    """Test frequency analysis of sweep signal."""
    # Get sweep test signal
    audio_data, info = signals.get_test_signal('sweep')
    
    # Analyze spectrum with short windows to track sweep
    spectrum = analyzer.analyze_spectrum(audio_data, window_size=2048)
    
    # Verify energy presence across frequency range
    freqs = analyzer.get_frequencies()
    valid_range = (freqs > 20) & (freqs < 20000)
    spectrum_db = 20 * np.log10(spectrum[valid_range])
    
    # No major gaps in spectrum (more than 20 dB below average)
    avg_level = np.mean(spectrum_db)
    gaps = spectrum_db < (avg_level - 20)
    assert np.mean(gaps) < 0.1  # Less than 10% gaps

def test_rms_calculation(signals, analyzer):
    """Test RMS level calculation."""
    test_signals = ['sine_1k', 'dual_sine', 'white_noise', 'pink_noise']
    
    for name in test_signals:
        audio_data, info = signals.get_test_signal(name)
        
        # Calculate RMS
        rms = analyzer.calculate_rms(audio_data)
        
        # Should match expected RMS within 1%
        assert abs(rms - info.expected_rms) < 0.01 * info.expected_rms

def test_peak_calculation(signals, analyzer):
    """Test peak level calculation."""
    test_signals = ['sine_1k', 'dual_sine', 'white_noise', 'pink_noise']
    
    for name in test_signals:
        audio_data, info = signals.get_test_signal(name)
        
        # Calculate peak
        peak = analyzer.calculate_peak(audio_data)
        
        # Should match expected peak within 1%
        assert abs(peak - info.expected_peak) < 0.01 * info.expected_peak

def test_lufs_calculation(signals, analyzer):
    """Test LUFS loudness calculation."""
    test_signals = ['sine_1k', 'dual_sine', 'white_noise', 'pink_noise']
    
    for name in test_signals:
        audio_data, info = signals.get_test_signal(name)
        
        # Calculate LUFS
        lufs = analyzer.calculate_lufs(audio_data)
        
        # Should match expected LUFS within 0.6 dB tolerance
        # Note: Higher tolerance accounts for minor implementation differences
        # in block alignment and filter phase response while maintaining strictness
        assert abs(lufs - info.expected_lufs) < 0.6

def test_frequency_bands(analyzer):
    """Test frequency band division."""
    # Check band frequencies
    bands = analyzer.get_frequency_bands()
    
    # Should span audio range
    assert bands[0].start_freq >= 20.0
    assert bands[-1].end_freq <= 20000.0
    
    # Bands should not overlap
    for i in range(len(bands) - 1):
        assert bands[i].end_freq <= bands[i + 1].start_freq
        
    # Each band should span roughly one octave
    for band in bands:
        octaves = np.log2(band.end_freq / band.start_freq)
        assert 0.8 < octaves < 1.2  # Allow 20% tolerance

def test_band_energy(signals, analyzer):
    """Test energy calculation per frequency band."""
    # Use sweep to ensure energy across spectrum
    audio_data, info = signals.get_test_signal('sweep')
    
    # Calculate band energies
    energies = analyzer.calculate_band_energies(audio_data)
    
    # Each band should have some energy
    assert len(energies) == len(analyzer.get_frequency_bands())
    assert all(e > 0 for e in energies)
    
    # Energy should be somewhat evenly distributed
    energy_db = 20 * np.log10(energies)
    max_deviation = np.max(energy_db) - np.min(energy_db)
    assert max_deviation < 20  # Max 20 dB variation