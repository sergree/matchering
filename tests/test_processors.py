"""
Tests for audio processors.
"""

import pytest
import numpy as np
from src.processing.eq import Equalizer, ThreeBandEQ, GraphicEQ
from src.processing.dynamics import Compressor, MultibandCompressor, CompressorParams
from src.processing.stereo import StereoProcessor, MidSideProcessor, AutoPanner, StereoParams
from src.processing.limiter import Limiter, BrickwallLimiter, LimiterParams

@pytest.fixture
def test_buffer():
    """Create test audio buffer."""
    # Create 1 second of 440Hz sine wave
    sample_rate = 44100
    duration = 0.1  # Short duration for faster tests
    t = np.linspace(0, duration, int(sample_rate * duration))
    mono = np.sin(2 * np.pi * 440 * t)
    return np.column_stack((mono, mono))  # Convert to stereo

def test_equalizer(test_buffer):
    """Test equalizer processor."""
    eq = Equalizer(44100)
    
    # Add some bands
    low = eq.add_band(100.0, -6.0)    # Cut low frequencies
    mid = eq.add_band(1000.0, 3.0)    # Boost mids
    high = eq.add_band(5000.0, -3.0)  # Cut highs
    
    # Process audio
    output = eq.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)  # Should be different
    
    # Test band controls
    eq.set_band_gain(mid, 0.0)  # Remove mid boost
    output2 = eq.process(test_buffer)
    assert not np.array_equal(output, output2)  # Should be different
    
    # Test band bypass
    eq.set_band_enabled(low, False)
    eq.set_band_enabled(mid, False)
    eq.set_band_enabled(high, False)
    output3 = eq.process(test_buffer)
    np.testing.assert_allclose(output3, test_buffer, rtol=1e-10)

def test_three_band_eq(test_buffer):
    """Test three-band equalizer."""
    eq = ThreeBandEQ(44100)
    
    # Adjust bands
    eq.set_band_gain(eq.low, -3.0)
    eq.set_band_gain(eq.mid, 2.0)
    eq.set_band_gain(eq.high, 1.0)
    
    # Process audio
    output = eq.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)

def test_graphic_eq(test_buffer):
    """Test graphic equalizer."""
    eq = GraphicEQ(44100)
    
    # Set band gains
    gains = [3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0, -2.0, -1.0, 0.0]
    eq.set_gains(gains)
    
    # Process audio
    output = eq.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)

def test_compressor(test_buffer):
    """Test compressor processor."""
    comp = Compressor(44100)
    
    # Set parameters
    params = CompressorParams(
        threshold=-20.0,
        ratio=4.0,
        attack=0.005,
        release=0.050
    )
    comp.update_params(params)
    
    # Process audio
    output = comp.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)
    
    # Check output level
    input_peak = np.max(np.abs(test_buffer))
    output_peak = np.max(np.abs(output))
    assert output_peak < input_peak  # Should be reduced

def test_multiband_compressor(test_buffer):
    """Test multiband compressor."""
    comp = MultibandCompressor(44100)
    
    # Set band parameters
    for i, band in enumerate(comp.compressors):
        params = CompressorParams(
            threshold=-20.0,
            ratio=2.0 + i,  # Different ratio for each band
            attack=0.005,
            release=0.050
        )
        band.update_params(params)
    
    # Process audio
    output = comp.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)

def test_stereo_processor(test_buffer):
    """Test stereo processor."""
    proc = StereoProcessor()
    
    # Test width control
    proc.update_params(StereoParams(width=2.0))  # Wide stereo
    output = proc.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)
    
    # Test mono
    proc.update_params(StereoParams(width=0.0))  # Mono
    output = proc.process(test_buffer)
    np.testing.assert_allclose(output[:, 0], output[:, 1], rtol=1e-10)

def test_mid_side_processor(test_buffer):
    """Test mid/side processor."""
    proc = MidSideProcessor()
    
    # Add different processing to mid and side
    mid_comp = Compressor(44100)
    side_comp = Compressor(44100)
    
    proc.add_mid_processor(mid_comp)
    proc.add_side_processor(side_comp)
    
    # Process audio
    output = proc.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)

def test_auto_panner(test_buffer):
    """Test auto-panner."""
    panner = AutoPanner(44100)
    
    # Set parameters
    panner.rate = 1.0  # 1 Hz
    panner.depth = 0.8
    
    # Process audio
    output = panner.process(test_buffer)
    assert output.shape == test_buffer.shape
    assert not np.array_equal(output, test_buffer)
    
    # Check that channels are different
    assert not np.array_equal(output[:, 0], output[:, 1])

def test_limiter(test_buffer):
    """Test limiter processor."""
    limiter = Limiter(44100)
    
    # Scale input to be hot
    hot_input = test_buffer * 2.0
    
    # Set threshold
    params = LimiterParams(threshold=-1.0)
    limiter.update_params(params)
    
    # Process audio
    output = limiter.process(hot_input)
    assert output.shape == hot_input.shape
    
    # Check that output is limited
    assert np.max(np.abs(output)) <= np.power(10, params.threshold / 20)

def test_brickwall_limiter(test_buffer):
    """Test brickwall limiter."""
    limiter = BrickwallLimiter(44100)
    
    # Scale input to be hot
    hot_input = test_buffer * 2.0
    
    # Set threshold
    params = LimiterParams(threshold=-1.0)
    limiter.update_params(params)
    
    # Process audio
    output = limiter.process(hot_input)
    assert output.shape == hot_input.shape
    
    # Check that output is limited (with some margin for oversampling artifacts)
    max_peak = np.max(np.abs(output))
    threshold_linear = np.power(10, params.threshold / 20)
    assert max_peak <= threshold_linear * 1.01  # Allow 1% margin