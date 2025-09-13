"""
Unit tests for basic DSP functions and processor initialization
"""

import pytest
import numpy as np
from tests.conftest import HAS_PLAYER, assert_audio_equal


@pytest.mark.unit
@pytest.mark.dsp
@pytest.mark.player
class TestDSPCore:
    """Test basic DSP functionality"""

    def test_basic_dsp_functions(self, sine_wave):
        """Test basic DSP functions"""
        pytest.importorskip("matchering_player.dsp")
        from matchering_player.dsp import rms, lr_to_ms, ms_to_lr

        # Create test audio
        test_audio, sr = sine_wave(1.0)

        # Test RMS calculation
        test_rms = rms(test_audio[:, 0])  # Left channel
        assert 0.1 < test_rms < 0.6, f"RMS should be reasonable, got {test_rms}"

        # Test Mid-Side conversion
        mid, side = lr_to_ms(test_audio)
        reconstructed = ms_to_lr(mid, side)

        # Should be nearly identical after round-trip
        assert_audio_equal(test_audio, reconstructed, tolerance=1e-6)

    def test_processor_initialization(self, test_config):
        """Test processor initialization and configuration"""
        pytest.importorskip("matchering_player.dsp")
        from matchering_player.dsp import RealtimeProcessor

        # Initialize processor
        processor = RealtimeProcessor(test_config)

        # Check initialization
        assert processor.config == test_config
        assert processor.level_matcher is not None
        assert not processor.is_processing

        # Check supported effects
        effects = processor.get_supported_effects()
        assert "level_matching" in effects

    def test_processing_without_reference(self, test_config, sine_wave):
        """Test processing without a reference track (should pass through)"""
        pytest.importorskip("matchering_player.dsp")
        from matchering_player.dsp import RealtimeProcessor

        processor = RealtimeProcessor(test_config)

        # Generate test chunk
        test_chunk, _ = sine_wave(0.1)  # 100ms chunk

        # Start processing
        processor.start_processing()

        # Process chunk (should pass through unchanged without reference)
        result = processor.process_audio_chunk(test_chunk)

        # Should be identical since no reference is loaded
        assert_audio_equal(test_chunk, result, tolerance=1e-6)

        # Stop processing
        processor.stop_processing()

    def test_processing_with_mock_reference(self, test_config, sine_wave):
        """Test processing with a mock reference"""
        pytest.importorskip("matchering_player.dsp")
        from matchering_player.dsp import RealtimeProcessor, rms

        processor = RealtimeProcessor(test_config)

        # Load a mock reference (this will create default target values)
        success = processor.load_reference_track("mock_reference.wav")
        assert success, "Mock reference should load successfully"

        # Generate test chunk (quiet signal)
        test_chunk, _ = sine_wave(0.1, amplitude=0.1)  # Very quiet
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

        # Should have applied some gain to the quiet signal
        assert gain_applied > 1.1, f"Should apply gain to quiet signal, got {gain_applied:.2f}"

        # Get processing stats
        stats = processor.get_processing_stats()
        assert stats['chunks_processed'] > 0
        assert stats['processing_active'] is True

        # Stop processing
        processor.stop_processing()

    @pytest.mark.performance
    def test_performance_monitoring(self, test_config, sine_wave):
        """Test performance monitoring system"""
        pytest.importorskip("matchering_player.dsp")
        from matchering_player.dsp import RealtimeProcessor

        # Use smaller buffer for faster processing
        config = test_config
        config.buffer_size_ms = 50.0
        processor = RealtimeProcessor(config)

        # Start processing
        processor.start_processing()

        # Process some chunks
        test_chunk, _ = sine_wave(0.05)  # 50ms chunks
        for i in range(20):
            processor.process_audio_chunk(test_chunk)

        # Get performance stats
        perf_stats = processor.performance_monitor.get_stats()
        assert perf_stats['cpu_usage'] >= 0, "Should have recorded some CPU usage"

        # Get health status
        health = processor.get_health_status()
        assert 'overall' in health
        assert 'performance' in health

        processor.stop_processing()


@pytest.mark.unit
@pytest.mark.dsp
def test_dsp_import():
    """Test that DSP modules can be imported"""
    pytest.importorskip("matchering_player.dsp")
    from matchering_player.dsp import rms, lr_to_ms, ms_to_lr

    # Basic smoke test
    test_audio = np.array([[0.5, 0.4], [0.3, 0.6]], dtype=np.float32)
    test_rms = rms(test_audio[:, 0])
    assert test_rms > 0