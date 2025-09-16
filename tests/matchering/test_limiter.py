"""
Tests for Hyrax limiter implementation
"""

import pytest
import numpy as np
from matchering import Config
from matchering.limiter.hyrax import limit


@pytest.fixture
def test_signal():
    """Generate test signal for limiter testing"""
    duration = 1.0  # seconds
    sample_rate = 44100
    t = np.linspace(0, duration, int(duration * sample_rate))

    # Create a signal with known peaks
    signal = np.zeros((len(t), 2))
    
    # Add some peaks
    signal[1000, :] = [1.2, 1.1]  # Sharp peak
    signal[2000:2100, :] = [1.5, 1.4]  # Sustained peak
    signal[3000:3010, :] = [1.8, 1.7]  # Short burst
    
    # Add some content below threshold
    sine = np.sin(2 * np.pi * 440 * t)
    signal[:, 0] += sine * 0.3
    signal[:, 1] += sine * 0.27
    
    return signal


@pytest.fixture
def basic_config():
    """Create basic limiter configuration"""
    config = Config()
    config.threshold = 0.999  # Just below 0 dB, safer than 1.0
    config.limiter.attack = 5.0  # ms
    config.limiter.release = 50.0  # ms
    config.limiter.hold = 20.0  # ms
    return config


class TestHyraxLimiter:
    """Test Hyrax limiter implementation"""

    def test_basic_limiting(self, test_signal, basic_config):
        """Test basic limiting functionality"""
        # Apply limiting
        limited = limit(test_signal, basic_config)
        
        # Output should not exceed threshold
        assert np.all(np.abs(limited) <= basic_config.threshold + 1e-6)
        assert not np.any(np.isnan(limited))
        assert not np.any(np.isinf(limited))
        
        # Stereo balance should be approximately preserved
        left_ratio = np.mean(np.abs(limited[:, 0]) / (np.abs(limited[:, 1]) + 1e-10))
        orig_ratio = np.mean(np.abs(test_signal[:, 0]) / (np.abs(test_signal[:, 1]) + 1e-10))
        assert np.abs(left_ratio - orig_ratio) < 0.1

    @pytest.mark.parametrize("threshold_db", [-6.0, -3.0, -1.0])
    def test_threshold_accuracy(self, test_signal, threshold_db):
        """Test limiter threshold accuracy"""
        config = Config()
        threshold_linear = 10 ** (threshold_db / 20)  # Convert dB to linear
        config.threshold = threshold_linear
        
        limited = limit(test_signal, config)
        assert np.all(np.abs(limited) <= threshold_linear + 1e-6)
        assert not np.any(np.isnan(limited))
        assert not np.any(np.isinf(limited))


class TestLimiterEdgeCases:
    """Test limiter edge cases"""

    def test_no_limiting_needed(self, basic_config):
        """Test when no limiting is needed"""
        # Create signal and scale to guarantee it's below threshold
        signal = np.random.randn(1000, 2)
        max_val = np.max(np.abs(signal))
        # Scale to half the threshold to ensure we're well below it
        scale = 0.5 * basic_config.threshold / max_val
        signal = signal * scale
        limited = limit(signal, basic_config)
        
        # Should be very close to input, but allow for tiny differences
        # due to processing path even when no actual limiting occurs
        assert np.allclose(limited, signal, rtol=1e-3, atol=1e-3)

    def test_extreme_values(self, basic_config):
        """Test with extreme values"""
        # Create signal with extremes
        signal = np.random.randn(1000, 2) * 1e5
        limited = limit(signal, basic_config)
        
        assert np.all(np.abs(limited) <= basic_config.threshold + 1e-6)
        assert not np.any(np.isnan(limited))
        assert not np.any(np.isinf(limited))

    def test_silence(self, basic_config):
        """Test with silence"""
        signal = np.zeros((1000, 2))
        limited = limit(signal, basic_config)
        
        # Should return silence
        assert np.allclose(limited, 0)
        assert not np.any(np.isnan(limited))

    def test_dc_offset(self, basic_config):
        """Test with DC offset"""
        signal = np.ones((1000, 2)) * 1.5  # Constant above threshold
        limited = limit(signal, basic_config)
        
        assert np.all(np.abs(limited) <= basic_config.threshold + 1e-6)
        assert not np.any(np.isnan(limited))
        assert not np.any(np.isinf(limited))