"""
Tests for core DSP functionality
"""

import pytest
import numpy as np
from matchering.dsp import (
    size,
    channel_count,
    is_mono,
    is_stereo,
    mono_to_stereo,
    lr_to_ms,
    ms_to_lr,
    rms,
    batch_rms,
    normalize,
    amplify,
    fade
)


@pytest.fixture
def test_signals():
    """Generate test signals"""
    # Create mono signal
    duration = 1.0  # seconds
    sample_rate = 44100
    t = np.linspace(0, duration, int(duration * sample_rate))
    mono = np.sin(2 * np.pi * 440 * t)
    
    # Create stereo signal
    left = np.sin(2 * np.pi * 440 * t)
    right = np.sin(2 * np.pi * 880 * t)
    stereo = np.column_stack([left, right])
    
    return {
        'mono': mono[:, np.newaxis],  # Make it 2D
        'stereo': stereo,
        'sample_rate': sample_rate
    }


class TestDSPCore:
    """Test core DSP functionality"""

    def test_signal_properties(self, test_signals):
        """Test basic signal property functions"""
        mono = test_signals['mono']
        stereo = test_signals['stereo']
        
        # Test size
        assert size(mono) == 44100
        assert size(stereo) == 44100
        
        # Test channel count
        assert channel_count(mono) == 1
        assert channel_count(stereo) == 2
        
        # Test mono/stereo detection
        assert is_mono(mono)
        assert not is_mono(stereo)
        assert is_stereo(stereo)
        assert not is_stereo(mono)

    def test_mono_to_stereo(self, test_signals):
        """Test mono to stereo conversion"""
        mono = test_signals['mono']
        stereo = mono_to_stereo(mono)
        
        assert stereo.shape[1] == 2
        assert np.allclose(stereo[:, 0], stereo[:, 1])
        assert np.allclose(stereo[:, 0], mono[:, 0])

    def test_ms_conversion(self, test_signals):
        """Test mid-side conversion"""
        stereo = test_signals['stereo']
        
        # Convert to mid-side
        mid, side = lr_to_ms(stereo)
        
        # Convert back to left-right
        lr = ms_to_lr(mid, side)
        
        # Should get original signal back
        assert np.allclose(lr, stereo)

    def test_rms_computation(self, test_signals):
        """Test RMS computation"""
        # Create a known signal
        t = np.linspace(0, 1, 1000)
        sine = np.sin(2 * np.pi * t)  # Pure sine wave
        rms_value = rms(sine)
        expected_rms = 1/np.sqrt(2)  # RMS of unit sine wave
        assert np.allclose(rms_value, expected_rms, rtol=1e-2)

        # Test with batched signals
        test_batch = np.vstack([sine, sine * 0.5])  # Two sine waves
        batch_rms_values = batch_rms(test_batch)
        assert len(batch_rms_values) == 2
        assert np.allclose(batch_rms_values[0], expected_rms, rtol=1e-2)
        assert np.allclose(batch_rms_values[1], expected_rms * 0.5, rtol=1e-2)

    def test_normalization(self, test_signals):
        """Test signal normalization"""
        # Create test signal
        signal = np.array([0.1, 0.5, -0.8, 0.3])  # Max abs is 0.8
        
        # Test normalization with threshold 1.0
        normalized, coef = normalize(signal, threshold=1.0, epsilon=1e-10, normalize_clipped=False)
        assert np.max(np.abs(normalized)) <= 1.0
        assert np.allclose(normalized * coef, signal)

        # Test with very small signal
        tiny = signal * 1e-6
        norm_tiny, coef_tiny = normalize(tiny, threshold=1.0, epsilon=1e-10, normalize_clipped=False)
        assert coef_tiny >= 1e-10

    def test_amplification(self, test_signals):
        """Test signal amplification"""
        signal = np.array([0.1, -0.2, 0.3, -0.4])
        gain = 2.0
        
        amplified = amplify(signal, gain)
        assert np.allclose(amplified, signal * gain)

    def test_fade(self, test_signals):
        """Test fade in/out"""
        # Create test signal
        signal = np.ones((100, 2))  # Constant amplitude stereo signal
        fade_size = 10
        
        faded = fade(signal, fade_size)
        
        # Check fade in
        assert np.allclose(faded[0], 0)
        assert np.all(faded[0:fade_size] <= signal[0:fade_size])
        
        # Check fade out
        assert np.allclose(faded[-1], 0)
        assert np.all(faded[-fade_size:] <= signal[-fade_size:])


class TestDSPEdgeCases:
    """Test DSP edge cases"""
    
    def test_edge_cases(self):
        """Test handling of edge cases"""
        # Test empty array handling
        empty_mono = np.zeros((0, 1))
        empty_stereo = np.zeros((0, 2))
        
        assert size(empty_mono) == 0
        assert channel_count(empty_stereo) == 2
        assert is_mono(empty_mono)
        assert is_stereo(empty_stereo)
        
        # Test single sample
        single = np.array([[0.5]])
        stereo_single = np.array([[0.5, 0.5]])
        
        assert size(single) == 1
        assert size(stereo_single) == 1
        assert rms(single[:, 0]) == 0.5
        
        # Test normalization with extremes
        extreme = np.array([1e-10, 1e10])
        norm, coef = normalize(extreme, threshold=1.0, epsilon=1e-10, normalize_clipped=True)
        assert np.all(np.abs(norm) <= 1.0)