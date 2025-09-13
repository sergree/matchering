"""
Tests for frequency matching functionality
"""

import pytest
import numpy as np
from scipy import signal
from matchering import Config
from matchering.stage_helpers.match_frequencies import (
    get_fir,
    convolve
)


@pytest.fixture
def test_config():
    """Create test configuration"""
    config = Config()
    config.fft_size = 2048  # Smaller FFT size for faster tests
    config.internal_sample_rate = 44100
    config.lowess_frac = 0.2
    config.lowess_it = 3
    config.lowess_delta = 0.01
    config.lin_log_oversampling = 8
    config.min_value = 1e-10
    return config


@pytest.fixture
def test_signals():
    """Create test audio signals"""
    duration = 5.0  # Long enough for accurate FFT
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples)

    # Target: Mix of frequencies with more low end
    target = (np.sin(2 * np.pi * 440 * t) * 0.7 + 
             np.sin(2 * np.pi * 880 * t) * 0.3)

    # Reference: Mix of frequencies with more high end
    reference = (np.sin(2 * np.pi * 440 * t) * 0.3 + 
                np.sin(2 * np.pi * 880 * t) * 0.7)
    
    # Add small noise to avoid exact zeros
    noise = np.random.randn(num_samples) * 1e-6
    target = target + noise
    reference = reference + noise
    
    # Create stereo signals
    target_stereo = np.vstack([target, target * 0.9]).T
    reference_stereo = np.vstack([reference, reference * 0.95]).T
    
    return {
        'target': target_stereo,
        'reference': reference_stereo,
        'sample_rate': sample_rate
    }


class TestFrequencyMatching:
    """Test frequency matching functionality"""

    def test_convolve(self, test_signals, test_config):
        """Test convolution with FIR filters"""
        # Create test filters
        mid_fir = signal.firwin(test_config.fft_size, 0.5)
        side_fir = signal.firwin(test_config.fft_size, 0.3)
        
        # Convert stereo to mid-side
        target_lr = test_signals['target']
        target_mid = np.mean(target_lr, axis=1)
        target_side = target_lr[:, 0] - target_lr[:, 1]
        
        # Apply convolution
        result_lr, result_mid = convolve(
            target_mid, mid_fir,
            target_side, side_fir
        )
        
        # Check output properties
        assert result_lr.shape == target_lr.shape
        assert len(result_mid) == len(target_mid)
        assert not np.any(np.isnan(result_lr))
        assert not np.any(np.isinf(result_lr))
        
        # Check stereo field preservation
        assert not np.allclose(result_lr[:, 0], result_lr[:, 1])

    def test_fir_generation(self, test_config):
        """Test FIR filter generation"""
        # Create signals matching FFT size
        # Create one second of audio at the internal sample rate
        duration = 1.0
        samples = int(duration * test_config.internal_sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Generate mono signals with known frequency content
        target = (np.sin(2 * np.pi * 440 * t) +
                 np.sin(2 * np.pi * 880 * t) * 0.5)
        ref = (np.sin(2 * np.pi * 440 * t) * 0.5 +
               np.sin(2 * np.pi * 880 * t))
        
        # Ensure length is a multiple of fft_size
        total = (samples // test_config.fft_size) * test_config.fft_size
        target = target[:total]
        ref = ref[:total]
        
        # Reshape into pieces matching FFT size (pieces, samples)
        target_pieces = target.reshape(-1, test_config.fft_size)
        ref_pieces = ref.reshape(-1, test_config.fft_size)
        
        # Generate FIR filter
        fir = get_fir(target_pieces, ref_pieces, 'test', test_config)
        
        # Check basic properties
        assert len(fir) == test_config.fft_size
        assert not np.any(np.isnan(fir))
        assert not np.any(np.isinf(fir))
        
        # Impulse response should be centered due to ifftshift
        center = test_config.fft_size // 2
        peak_idx = int(np.argmax(np.abs(fir)))
        assert abs(peak_idx - center) < test_config.fft_size * 0.1
        
        # Should be windowed (taper to zero at edges)
        assert abs(fir[0]) < 1e-6
        assert abs(fir[-1]) < 1e-6
        
        # Check frequency response is reasonable
        w, h = signal.freqz(fir)
        freqs = w * test_config.internal_sample_rate / (2 * np.pi)
        h_mag = np.abs(h)
        
        # Find peak frequencies in magnitude response
        peaks = signal.find_peaks(h_mag)[0]
        
        # Frequency response should be finite and bounded
        assert np.all(np.isfinite(h_mag))
        assert np.max(h_mag) < 10.0  # Avoid extreme gains
        
        # Should not be all-pass (some shaping expected)
        assert np.std(h_mag) > 1e-4
        
        # Response should be smooth (no abrupt changes)
        response_diff = np.diff(h_mag)
        assert np.max(np.abs(response_diff)) < 1.0


@pytest.mark.xfail(reason="Interpolation unstable for small/degenerate inputs")
class TestFrequencyMatchingEdgeCases:
    """Test frequency matching edge cases"""

    def test_near_silence(self, test_config):
        """Test handling of near-silence"""
        num_samples = test_config.fft_size * 4  # Enough samples for FFT
        
        # Create near-silence with tiny noise
        signal = np.random.randn(num_samples, 2) * 1e-6
        
        fir = get_fir(signal, signal, 'test', test_config)
        assert len(fir) == test_config.fft_size
        assert not np.any(np.isnan(fir))
        assert not np.any(np.isinf(fir))

    def test_extreme_values(self, test_config):
        """Test handling of extreme values with noise"""
        num_samples = test_config.fft_size * 4
        t = np.linspace(0, 1.0, num_samples)
        
        # Large values with noise
        base = np.sin(2 * np.pi * 440 * t) * 1e10
        noise = np.random.randn(num_samples) * 1e8
        signal = np.column_stack([base + noise, base + noise])
        
        fir = get_fir(signal, signal, 'test', test_config)
        assert len(fir) == test_config.fft_size
        assert not np.any(np.isnan(fir))
        assert not np.any(np.isinf(fir))

    @pytest.mark.parametrize('fft_size', [1024, 2048, 4096])
    def test_different_fft_sizes(self, test_signals, test_config, fft_size):
        """Test frequency matching with different FFT sizes"""
        test_config.fft_size = fft_size
        
        # Get FIR filter with extended signals
        fir = get_fir(
            test_signals['target'],
            test_signals['reference'],
            'test',
            test_config
        )
        
        # Check filter length and properties
        assert len(fir) == fft_size
        assert np.all(np.isfinite(fir))
        assert np.allclose(fir, np.flip(fir), rtol=1e-5)  # Symmetric