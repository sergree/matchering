"""
Unit tests for RealtimeProcessor - Main realtime DSP coordinator
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from matchering_player.dsp.processor import RealtimeProcessor, PerformanceMonitor
from matchering_player.core.config import PlayerConfig


class TestPerformanceMonitor:
    """Test the PerformanceMonitor class"""

    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization"""
        monitor = PerformanceMonitor(max_cpu_usage=0.7)

        assert monitor.max_cpu_usage == 0.7
        assert monitor.processing_times == []
        assert monitor.performance_mode == False
        assert monitor.consecutive_overruns == 0

    def test_record_processing_time_normal(self):
        """Test recording normal processing times"""
        monitor = PerformanceMonitor(max_cpu_usage=0.8)

        # Simulate normal processing (50% CPU usage)
        processing_time = 0.005  # 5ms
        chunk_duration = 0.010   # 10ms

        monitor.record_processing_time(processing_time, chunk_duration)

        assert len(monitor.processing_times) == 1
        assert monitor.processing_times[0] == 0.5  # 50% CPU usage
        assert monitor.consecutive_overruns == 0
        assert monitor.performance_mode == False

    def test_record_processing_time_overrun(self):
        """Test recording overrun processing times"""
        monitor = PerformanceMonitor(max_cpu_usage=0.8)

        # Simulate overrun processing (90% CPU usage)
        processing_time = 0.009  # 9ms
        chunk_duration = 0.010   # 10ms

        for _ in range(6):  # Trigger performance mode
            monitor.record_processing_time(processing_time, chunk_duration)

        assert monitor.consecutive_overruns >= 5
        assert monitor.performance_mode == True

    def test_get_stats_initializing(self):
        """Test stats when no processing times recorded"""
        monitor = PerformanceMonitor()
        stats = monitor.get_stats()

        assert stats['cpu_usage'] == 0.0
        assert stats['performance_mode'] == False
        assert stats['status'] == 'initializing'

    def test_get_stats_optimal(self):
        """Test stats during optimal performance"""
        monitor = PerformanceMonitor(max_cpu_usage=0.8)

        # Record several low CPU usage measurements
        for _ in range(20):
            monitor.record_processing_time(0.002, 0.010)  # 20% CPU

        stats = monitor.get_stats()
        assert stats['status'] == 'optimal'
        assert stats['cpu_usage'] < 0.5
        assert stats['performance_mode'] == False


class TestRealtimeProcessor:
    """Test the main RealtimeProcessor class"""

    @pytest.fixture
    def config(self):
        """Basic processor configuration"""
        return PlayerConfig(
            sample_rate=44100,
            buffer_size_ms=100.0,
            enable_level_matching=True,
            enable_frequency_matching=False,
            enable_stereo_width=False,
            enable_auto_mastering=False
        )

    @pytest.fixture
    def full_config(self):
        """Full-featured processor configuration"""
        return PlayerConfig(
            sample_rate=44100,
            buffer_size_ms=100.0,
            enable_level_matching=True,
            enable_frequency_matching=True,
            enable_stereo_width=True,
            enable_auto_mastering=True
        )

    def test_processor_initialization_basic(self, config):
        """Test basic processor initialization"""
        processor = RealtimeProcessor(config)

        assert processor.config == config
        assert processor.is_processing == False
        assert processor.bypass_all == False
        assert processor.total_processed_samples == 0
        assert processor.level_matcher is not None
        assert processor.frequency_matcher is None
        assert processor.stereo_processor is None

    def test_processor_initialization_full(self, full_config):
        """Test full processor initialization"""
        processor = RealtimeProcessor(full_config)

        assert processor.level_matcher is not None
        assert processor.frequency_matcher is not None
        assert processor.stereo_processor is not None
        assert processor.auto_master is not None

    def test_start_stop_processing(self, config):
        """Test starting and stopping processing"""
        processor = RealtimeProcessor(config)

        # Start processing
        processor.start_processing()
        assert processor.is_processing == True
        assert processor.total_processed_samples == 0
        assert processor.chunks_processed == 0

        # Stop processing
        processor.stop_processing()
        assert processor.is_processing == False

    def test_process_audio_chunk_bypass(self, config):
        """Test audio processing when bypassed"""
        processor = RealtimeProcessor(config)

        # Test with processing stopped
        audio_chunk = np.random.rand(4410, 2).astype(np.float32) * 0.5
        result = processor.process_audio_chunk(audio_chunk)
        np.testing.assert_array_equal(result, audio_chunk)

        # Test with bypass enabled
        processor.start_processing()
        processor.set_bypass_all(True)
        result = processor.process_audio_chunk(audio_chunk)
        np.testing.assert_array_equal(result, audio_chunk)

    def test_process_audio_chunk_mono_warning(self, config):
        """Test processing with mono input (should warn but return input)"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        # Mono input
        mono_chunk = np.random.rand(4410, 1).astype(np.float32) * 0.5
        result = processor.process_audio_chunk(mono_chunk)
        np.testing.assert_array_equal(result, mono_chunk)

    def test_process_audio_chunk_level_matching(self, config):
        """Test audio processing with level matching"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        # Create test audio with low level
        audio_chunk = np.random.rand(4410, 2).astype(np.float32) * 0.1

        # Mock level matcher to have a reference
        with patch.object(processor.level_matcher, 'reference_profile', Mock()):
            with patch.object(processor.level_matcher, 'process_chunk') as mock_process:
                mock_process.return_value = audio_chunk * 2  # Simulate gain

                result = processor.process_audio_chunk(audio_chunk)

                mock_process.assert_called_once()
                assert processor.total_processed_samples == len(audio_chunk)
                assert processor.chunks_processed == 1

    def test_load_reference_track_success(self, full_config, temp_dir):
        """Test loading reference track successfully"""
        processor = RealtimeProcessor(full_config)

        # Mock all load_reference methods to return True
        with patch.object(processor.level_matcher, 'load_reference', return_value=True):
            with patch.object(processor.frequency_matcher, 'load_reference', return_value=True):
                with patch.object(processor.stereo_processor, 'load_reference', return_value=True):

                    result = processor.load_reference_track("/fake/reference.wav")
                    assert result == True

    def test_load_reference_track_partial_failure(self, full_config):
        """Test loading reference with some processors failing"""
        processor = RealtimeProcessor(full_config)

        # Mock mixed success/failure
        with patch.object(processor.level_matcher, 'load_reference', return_value=True):
            with patch.object(processor.frequency_matcher, 'load_reference', return_value=False):
                with patch.object(processor.stereo_processor, 'load_reference', return_value=True):

                    result = processor.load_reference_track("/fake/reference.wav")
                    assert result == True  # Should succeed if at least one works

    def test_set_effect_enabled(self, full_config):
        """Test enabling/disabling individual effects"""
        processor = RealtimeProcessor(full_config)

        # Test level matching
        with patch.object(processor.level_matcher, 'set_enabled') as mock_set:
            processor.set_effect_enabled("level_matching", False)
            mock_set.assert_called_once_with(False)

        # Test frequency matching
        with patch.object(processor.frequency_matcher, 'set_enabled') as mock_set:
            processor.set_effect_enabled("frequency_matching", True)
            mock_set.assert_called_once_with(True)

        # Test stereo width
        with patch.object(processor.stereo_processor, 'set_enabled') as mock_set:
            processor.set_effect_enabled("stereo_width", False)
            mock_set.assert_called_once_with(False)

    def test_set_effect_parameter(self, config):
        """Test setting effect parameters"""
        processor = RealtimeProcessor(config)

        # Test level matching parameters
        with patch.object(processor.level_matcher, 'set_bypass') as mock_bypass:
            processor.set_effect_parameter("level_matching", "bypass", True)
            mock_bypass.assert_called_once_with(True)

        # Test smoothing speed parameter
        processor.set_effect_parameter("level_matching", "smoothing_speed", 0.5)
        # Should update the gain smoother alphas
        assert processor.gain_smoother.base_attack_alpha > 0

    def test_performance_monitoring(self, config):
        """Test performance monitoring during processing"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        # Process several chunks to build performance history
        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.3

        for _ in range(10):
            processor.process_audio_chunk(audio_chunk)

        stats = processor.get_processing_stats()
        assert stats['chunks_processed'] == 10
        assert stats['total_processed_samples'] == 10 * 1024
        assert 'cpu_usage' in stats
        assert 'performance_mode' in stats

    def test_get_processing_stats_comprehensive(self, config):
        """Test comprehensive processing statistics"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        stats = processor.get_processing_stats()

        # Check required fields
        required_fields = [
            'processing_active', 'bypass_all', 'total_processed_samples',
            'chunks_processed', 'processed_duration_seconds',
            'current_quality_factor', 'cpu_usage', 'smoothing', 'buffers'
        ]

        for field in required_fields:
            assert field in stats

    def test_get_latency_info(self, config):
        """Test latency information reporting"""
        processor = RealtimeProcessor(config)

        latency_info = processor.get_latency_info()

        required_fields = [
            'buffer_latency_ms', 'processing_overhead_ms',
            'total_estimated_latency_ms', 'buffer_latency_samples', 'is_low_latency'
        ]

        for field in required_fields:
            assert field in latency_info

        assert latency_info['buffer_latency_ms'] > 0
        assert latency_info['total_estimated_latency_ms'] > latency_info['buffer_latency_ms']

    def test_reset_all_effects(self, config):
        """Test resetting all effects"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        # Process some audio to build state
        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.3
        processor.process_audio_chunk(audio_chunk)

        # Reset all effects
        processor.reset_all_effects()

        assert processor.total_processed_samples == 0
        assert processor.chunks_processed == 0
        assert processor.current_quality_factor == 1.0
        assert len(processor.performance_monitor.processing_times) == 0

    def test_effect_chain_management(self, config):
        """Test adding and removing effects from chain"""
        processor = RealtimeProcessor(config)

        # Mock effect
        mock_effect = Mock()
        mock_effect.__class__.__name__ = "MockEffect"

        # Add effect
        processor.add_effect_to_chain(mock_effect)
        assert len(processor.effect_chain) == 1
        assert processor.effect_chain[0] == mock_effect

        # Remove effect
        processor.remove_effect_from_chain(type(mock_effect))
        assert len(processor.effect_chain) == 0

    def test_get_supported_effects(self, full_config):
        """Test getting list of supported effects"""
        processor = RealtimeProcessor(full_config)
        effects = processor.get_supported_effects()

        expected_effects = ["level_matching", "frequency_matching", "stereo_width"]
        for effect in expected_effects:
            assert effect in effects

    def test_get_health_status(self, config):
        """Test system health status reporting"""
        processor = RealtimeProcessor(config)

        health = processor.get_health_status()

        required_fields = ['overall', 'processing', 'performance', 'level_matching', 'buffers']
        for field in required_fields:
            assert field in health

        assert health['overall'] in ['healthy', 'degraded', 'idle']
        assert health['processing'] in ['active', 'stopped']

    def test_quality_adaptation(self, config):
        """Test adaptive quality control"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        # Simulate high CPU usage to trigger performance mode
        for _ in range(10):
            processor.performance_monitor.record_processing_time(0.015, 0.010)  # 150% CPU

        # Process should adapt quality
        processor._adapt_quality()
        assert processor.current_quality_factor < 1.0

    @pytest.mark.error
    def test_process_audio_chunk_exception_handling(self, config):
        """Test exception handling in audio processing"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        # Mock level matcher to raise exception
        with patch.object(processor.level_matcher, 'process_chunk', side_effect=Exception("Test error")):
            audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.3
            result = processor.process_audio_chunk(audio_chunk)

            # Should return original audio on exception
            np.testing.assert_array_equal(result, audio_chunk)

    def test_auto_mastering_integration(self, full_config):
        """Test auto-mastering integration with other effects"""
        processor = RealtimeProcessor(full_config)
        processor.start_processing()

        # Mock auto-mastering to return targets
        auto_targets = {
            'target_rms_db': -20.0,
            'eq_bands': [{'frequency': 1000, 'gain': 2.0, 'Q': 1.0}],
            'stereo_width': 1.2
        }

        with patch.object(processor.auto_master, 'process_chunk', return_value=(auto_targets, None)):
            audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.3

            # Should process with auto-mastering targets
            result = processor.process_audio_chunk(audio_chunk)
            assert result is not None

    @pytest.mark.performance
    def test_processing_performance_benchmark(self, config):
        """Benchmark processing performance"""
        processor = RealtimeProcessor(config)
        processor.start_processing()

        # Generate test audio
        chunk_size = config.buffer_size_samples
        audio_chunk = np.random.rand(chunk_size, 2).astype(np.float32) * 0.3

        # Benchmark processing time
        start_time = time.perf_counter()
        num_chunks = 100

        for _ in range(num_chunks):
            processor.process_audio_chunk(audio_chunk)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Calculate performance metrics
        audio_duration = (num_chunks * chunk_size) / config.sample_rate
        real_time_factor = audio_duration / total_time

        print(f"Processing performance: {real_time_factor:.1f}x real-time")

        # Should be able to process faster than real-time
        assert real_time_factor > 1.0, f"Processing too slow: {real_time_factor:.2f}x real-time"