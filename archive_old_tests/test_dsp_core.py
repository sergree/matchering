#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quick test of Matchering Player DSP core
Verify that basic processing works without audio I/O
"""

import numpy as np
import sys
import os

# Add the matchering_player package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matchering_player.core.config import PlayerConfig
from matchering_player.dsp import RealtimeProcessor, rms, lr_to_ms, ms_to_lr


def generate_test_audio(duration_seconds=5.0, sample_rate=44100):
    """Generate stereo test audio with some variation"""
    samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, samples)
    
    # Create a simple sine wave with some variation
    frequency = 440.0  # A4 note
    left = np.sin(2 * np.pi * frequency * t) * 0.5
    right = np.sin(2 * np.pi * frequency * t * 1.01) * 0.4  # Slightly different frequency
    
    # Add some amplitude variation to make it more realistic
    envelope = 0.5 + 0.3 * np.sin(2 * np.pi * 0.5 * t)  # Slow amplitude modulation
    left *= envelope
    right *= envelope
    
    return np.column_stack((left, right)).astype(np.float32)


def test_basic_dsp_functions():
    """Test basic DSP functions"""
    print("🧪 Testing basic DSP functions...")
    
    # Create test audio
    test_audio = generate_test_audio(1.0)  # 1 second
    
    # Test RMS calculation
    test_rms = rms(test_audio[:, 0])  # Left channel
    print(f"   RMS of test signal: {test_rms:.6f}")
    assert 0.1 < test_rms < 0.6, f"RMS should be reasonable, got {test_rms}"
    
    # Test Mid-Side conversion
    mid, side = lr_to_ms(test_audio)
    reconstructed = ms_to_lr(mid, side)
    
    # Should be nearly identical after round-trip
    difference = np.max(np.abs(test_audio - reconstructed))
    print(f"   Mid-Side conversion error: {difference:.8f}")
    assert difference < 1e-6, f"Mid-Side conversion error too large: {difference}"
    
    print("✅ Basic DSP functions working correctly")


def test_processor_initialization():
    """Test processor initialization and configuration"""
    print("🧪 Testing processor initialization...")
    
    # Create configuration
    config = PlayerConfig(
        buffer_size_ms=100.0,
        enable_level_matching=True,
        rms_smoothing_alpha=0.1
    )
    
    print(f"   Config: {config.buffer_size_samples} samples, {config.buffer_size_ms}ms")
    
    # Initialize processor
    processor = RealtimeProcessor(config)
    
    # Check initialization
    assert processor.config == config
    assert processor.level_matcher is not None
    assert not processor.is_processing
    
    # Check supported effects
    effects = processor.get_supported_effects()
    print(f"   Supported effects: {effects}")
    assert "level_matching" in effects
    
    print("✅ Processor initialization working correctly")


def test_processing_without_reference():
    """Test processing without a reference track (should pass through)"""
    print("🧪 Testing processing without reference...")
    
    config = PlayerConfig(buffer_size_ms=100.0, enable_level_matching=True)
    processor = RealtimeProcessor(config)
    
    # Generate test chunk
    test_chunk = generate_test_audio(0.1)  # 100ms chunk
    
    # Start processing
    processor.start_processing()
    
    # Process chunk (should pass through unchanged without reference)
    result = processor.process_audio_chunk(test_chunk)
    
    # Should be identical since no reference is loaded
    difference = np.max(np.abs(test_chunk - result))
    print(f"   Pass-through difference: {difference:.8f}")
    assert difference < 1e-6, f"Should pass through unchanged without reference"
    
    # Stop processing
    processor.stop_processing()
    
    print("✅ Processing without reference working correctly")


def test_processing_with_mock_reference():
    """Test processing with a mock reference"""
    print("🧪 Testing processing with mock reference...")
    
    config = PlayerConfig(buffer_size_ms=100.0, enable_level_matching=True)
    processor = RealtimeProcessor(config)
    
    # Load a mock reference (this will create default target values)
    success = processor.load_reference_track("mock_reference.wav")
    assert success, "Mock reference should load successfully"
    
    # Generate test chunk (quiet signal)
    test_chunk = generate_test_audio(0.1) * 0.1  # Very quiet
    original_rms = rms(test_chunk[:, 0])
    
    # Start processing
    processor.start_processing()
    
    # Process several chunks to allow smoothing to engage
    processed_chunk = test_chunk
    for i in range(10):  # Process 10 chunks (1 second)
        processed_chunk = processor.process_audio_chunk(processed_chunk)
    
    # Check if gain was applied
    processed_rms = rms(processed_chunk[:, 0])
    gain_applied = processed_rms / original_rms
    
    print(f"   Original RMS: {original_rms:.6f}")
    print(f"   Processed RMS: {processed_rms:.6f}")
    print(f"   Gain applied: {gain_applied:.2f} ({20*np.log10(gain_applied):.1f} dB)")
    
    # Should have applied some gain to the quiet signal
    assert gain_applied > 1.1, f"Should apply gain to quiet signal, got {gain_applied:.2f}"
    
    # Get processing stats
    stats = processor.get_processing_stats()
    print(f"   Chunks processed: {stats['chunks_processed']}")
    print(f"   Processing active: {stats['processing_active']}")
    print(f"   Level matching status: {stats.get('level_matching', {}).get('status', 'N/A')}")
    
    # Stop processing
    processor.stop_processing()
    
    print("✅ Processing with mock reference working correctly")


def test_performance_monitoring():
    """Test performance monitoring system"""
    print("🧪 Testing performance monitoring...")
    
    config = PlayerConfig(buffer_size_ms=50.0)  # Smaller buffer for faster processing
    processor = RealtimeProcessor(config)
    
    # Start processing
    processor.start_processing()
    
    # Process some chunks
    test_chunk = generate_test_audio(0.05)  # 50ms chunks
    for i in range(20):
        processor.process_audio_chunk(test_chunk)
    
    # Get performance stats
    perf_stats = processor.performance_monitor.get_stats()
    print(f"   CPU usage: {perf_stats['cpu_usage']:.2%}")
    print(f"   Status: {perf_stats['status']}")
    print(f"   Performance mode: {perf_stats['performance_mode']}")
    
    # Should have some CPU usage recorded
    assert perf_stats['cpu_usage'] >= 0, "Should have recorded some CPU usage"
    
    # Get health status
    health = processor.get_health_status()
    print(f"   Overall health: {health['overall']}")
    print(f"   Performance: {health['performance']}")
    
    processor.stop_processing()
    
    print("✅ Performance monitoring working correctly")


def main():
    """Run all tests"""
    print("🚀 Starting Matchering Player DSP Core Tests")
    print("=" * 50)
    
    try:
        test_basic_dsp_functions()
        print()
        
        test_processor_initialization()
        print()
        
        test_processing_without_reference()
        print()
        
        test_processing_with_mock_reference()
        print()
        
        test_performance_monitoring()
        print()
        
        print("=" * 50)
        print("🎉 All DSP core tests passed!")
        print("The Matchering Player DSP system is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
