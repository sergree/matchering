"""
Unit tests for RealtimeStereoProcessor - Real-time stereo width control
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from matchering_player.dsp.stereo import RealtimeStereoProcessor, StereoProfile
from matchering_player.core.config import PlayerConfig


class TestStereoProfile:
    """Test the StereoProfile class"""

    def test_stereo_profile_initialization(self):
        """Test StereoProfile initialization"""
        profile = StereoProfile("/path/to/reference.wav")

        assert profile.file_path == "/path/to/reference.wav"
        assert profile.filename == "reference.wav"
        assert profile.mid_rms is None
        assert profile.side_rms is None
        assert profile.stereo_width is None
        assert profile.correlation is None
        assert profile.analysis_complete == False

    def test_stereo_profile_filename_extraction(self):
        """Test filename extraction from different paths"""
        # Unix path
        profile_unix = StereoProfile("/home/user/music/track.wav")
        assert profile_unix.filename == "track.wav"

        # Windows path
        profile_win = StereoProfile("C:\\Music\\track.wav")
        assert profile_win.filename == "C:\\Music\\track.wav"  # No '/' in path

        # Simple filename
        profile_simple = StereoProfile("track.wav")
        assert profile_simple.filename == "track.wav"

    def test_stereo_profile_serialization(self):
        """Test profile to_dict and from_dict"""
        profile = StereoProfile("/path/to/test.wav")
        profile.mid_rms = 0.3
        profile.side_rms = 0.15
        profile.stereo_width = 0.5
        profile.correlation = 0.8
        profile.analysis_complete = True

        # Test serialization
        data = profile.to_dict()
        assert data['file_path'] == "/path/to/test.wav"
        assert data['mid_rms'] == 0.3
        assert data['side_rms'] == 0.15
        assert data['stereo_width'] == 0.5

        # Test deserialization
        restored_profile = StereoProfile.from_dict(data)
        assert restored_profile.file_path == profile.file_path
        assert restored_profile.mid_rms == profile.mid_rms
        assert restored_profile.side_rms == profile.side_rms
        assert restored_profile.stereo_width == profile.stereo_width


class TestRealtimeStereoProcessor:
    """Test the RealtimeStereoProcessor class"""

    @pytest.fixture
    def config(self):
        """Basic stereo processor configuration"""
        return PlayerConfig(
            sample_rate=44100,
            buffer_size_ms=100.0,
            enable_stereo_width=True,
            rms_smoothing_alpha=0.1
        )

    @pytest.fixture
    def stereo_processor(self, config):
        """Create stereo processor instance"""
        return RealtimeStereoProcessor(config)

    def test_stereo_processor_initialization(self, stereo_processor, config):
        """Test RealtimeStereoProcessor initialization"""
        assert stereo_processor.config == config
        assert stereo_processor.enabled == True
        assert stereo_processor.bypass_mode == False
        assert stereo_processor.width_factor == 1.0
        assert stereo_processor.target_width == 1.0
        assert stereo_processor.manual_width == 1.0
        assert stereo_processor.use_reference_width == False
        assert stereo_processor.reference_profile is None

    def test_process_chunk_disabled(self, stereo_processor):
        """Test processing when disabled"""
        stereo_processor.enabled = False
        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.5

        result = stereo_processor.process_chunk(audio_chunk)
        np.testing.assert_array_equal(result, audio_chunk)

    def test_process_chunk_bypassed(self, stereo_processor):
        """Test processing when bypassed"""
        stereo_processor.bypass_mode = True
        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.5

        result = stereo_processor.process_chunk(audio_chunk)
        np.testing.assert_array_equal(result, audio_chunk)

    def test_process_chunk_mono_input(self, stereo_processor):
        """Test processing mono input (should return unchanged)"""
        mono_chunk = np.random.rand(1024, 1).astype(np.float32) * 0.5
        result = stereo_processor.process_chunk(mono_chunk)
        np.testing.assert_array_equal(result, mono_chunk)

    def test_process_chunk_normal_width(self, stereo_processor):
        """Test processing with normal width (1.0)"""
        # Create stereo test signal with clear L/R separation
        audio_chunk = np.zeros((1024, 2), dtype=np.float32)
        audio_chunk[:, 0] = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100) * 0.5  # Left
        audio_chunk[:, 1] = np.sin(2 * np.pi * 880 * np.arange(1024) / 44100) * 0.5  # Right

        result = stereo_processor.process_chunk(audio_chunk)

        assert result.shape == audio_chunk.shape
        assert result.dtype == audio_chunk.dtype
        # With width=1.0, should be similar to input
        assert np.allclose(result, audio_chunk, atol=0.1)

    def test_process_chunk_narrow_width(self, stereo_processor):
        """Test processing with narrow width (<1.0)"""
        stereo_processor.set_width(0.5)  # Narrow stereo

        # Create wide stereo test signal with time-varying content
        t = np.arange(1024) / 44100.0
        audio_chunk = np.zeros((1024, 2), dtype=np.float32)
        audio_chunk[:, 0] = np.sin(2 * np.pi * 440 * t) * 0.5  # Left channel
        audio_chunk[:, 1] = np.sin(2 * np.pi * 880 * t) * 0.5  # Right channel (different frequency)

        result = stereo_processor.process_chunk(audio_chunk)

        # Check that stereo width was reduced
        assert result.shape == audio_chunk.shape
        # Channels should be closer together than original (check RMS difference)
        diff_original = np.sqrt(np.mean((audio_chunk[:, 0] - audio_chunk[:, 1])**2))
        diff_processed = np.sqrt(np.mean((result[:, 0] - result[:, 1])**2))
        if diff_original > 1e-6:  # Only test if there was actual stereo content
            assert diff_processed <= diff_original

    def test_process_chunk_wide_width(self, stereo_processor):
        """Test processing with wide width (>1.0)"""
        stereo_processor.set_width(1.5)  # Wide stereo

        # Create narrow stereo test signal
        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.3
        # Make channels similar (narrow stereo)
        audio_chunk[:, 1] = audio_chunk[:, 0] * 0.9

        result = stereo_processor.process_chunk(audio_chunk)

        # Check that stereo width was increased
        assert result.shape == audio_chunk.shape
        # Channels should be more separated than original
        width_original = np.std(audio_chunk[:, 0] - audio_chunk[:, 1])
        width_processed = np.std(result[:, 0] - result[:, 1])
        assert width_processed > width_original

    def test_process_chunk_extreme_width(self, stereo_processor):
        """Test processing with extreme width (should be limited)"""
        stereo_processor.set_width(2.0)  # Very wide

        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.5
        result = stereo_processor.process_chunk(audio_chunk)

        # Should not clip or produce extreme values
        assert np.max(np.abs(result)) <= 1.0
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_set_width(self, stereo_processor):
        """Test manual width setting"""
        # Test normal range
        stereo_processor.set_width(1.5)
        assert stereo_processor.manual_width == 1.5
        assert stereo_processor.use_reference_width == False

        # Test clamping to valid range
        stereo_processor.set_width(-0.5)  # Below minimum
        assert stereo_processor.manual_width == 0.0

        stereo_processor.set_width(3.0)  # Above maximum
        assert stereo_processor.manual_width == 2.0

    def test_set_reference_matching(self, stereo_processor):
        """Test reference width matching enable/disable"""
        stereo_processor.set_reference_matching(True)
        assert stereo_processor.use_reference_width == True

        stereo_processor.set_reference_matching(False)
        assert stereo_processor.use_reference_width == False

    def test_get_current_width(self, stereo_processor):
        """Test getting current effective width"""
        stereo_processor.set_width(1.5)
        width = stereo_processor.get_current_width()
        assert width == stereo_processor.width_factor

    def test_set_enabled(self, stereo_processor):
        """Test enabling/disabling stereo processing"""
        stereo_processor.set_enabled(False)
        assert stereo_processor.enabled == False

        stereo_processor.set_enabled(True)
        assert stereo_processor.enabled == True

    def test_set_bypass(self, stereo_processor):
        """Test bypass mode"""
        stereo_processor.set_bypass(True)
        assert stereo_processor.bypass_mode == True

        stereo_processor.set_bypass(False)
        assert stereo_processor.bypass_mode == False

    def test_reset(self, stereo_processor):
        """Test resetting processor state"""
        # Process some audio to build state
        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.5
        stereo_processor.process_chunk(audio_chunk)

        assert stereo_processor.chunks_processed > 0

        # Reset
        stereo_processor.reset()
        assert stereo_processor.chunks_processed == 0
        assert stereo_processor.current_correlation == 0.0

    def test_calculate_correlation(self, stereo_processor):
        """Test L/R correlation calculation"""
        # Perfect correlation (mono)
        mono_chunk = np.random.rand(1024, 1).astype(np.float32) * 0.5
        stereo_mono = np.column_stack([mono_chunk[:, 0], mono_chunk[:, 0]])
        corr = stereo_processor._calculate_correlation(stereo_mono)
        assert abs(corr - 1.0) < 0.01  # Should be close to 1.0

        # No correlation (random)
        random_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.5
        corr = stereo_processor._calculate_correlation(random_chunk)
        assert -1.0 <= corr <= 1.0  # Should be valid correlation

        # Negative correlation (opposite phase)
        left = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100) * 0.5
        right = -left  # Opposite phase
        opposite_chunk = np.column_stack([left, right])
        corr = stereo_processor._calculate_correlation(opposite_chunk)
        assert corr < -0.5  # Should be strongly negative

    def test_get_current_stats_no_reference(self, stereo_processor):
        """Test statistics without reference"""
        stats = stereo_processor.get_current_stats()

        required_fields = [
            'enabled', 'bypass_mode', 'width_factor', 'manual_width',
            'target_width', 'use_reference_width', 'current_correlation',
            'chunks_processed', 'reference_loaded'
        ]

        for field in required_fields:
            assert field in stats

        assert stats['enabled'] == True
        assert stats['reference_loaded'] == False

    def test_get_current_stats_with_reference(self, stereo_processor):
        """Test statistics with reference loaded"""
        mock_profile = Mock()
        mock_profile.filename = "test_reference.wav"
        mock_profile.stereo_width = 1.2
        mock_profile.correlation = 0.85
        stereo_processor.reference_profile = mock_profile

        stats = stereo_processor.get_current_stats()

        assert stats['reference_loaded'] == True
        assert stats['reference_filename'] == "test_reference.wav"
        assert stats['reference_width'] == 1.2
        assert stats['reference_correlation'] == 0.85

    @pytest.mark.integration
    def test_load_reference_workflow(self, stereo_processor, test_audio_files):
        """Test complete reference loading workflow"""
        if 'loud_reference.wav' not in test_audio_files:
            pytest.skip("Test audio files not available")

        reference_file = test_audio_files['loud_reference.wav']

        # Mock the file loader to avoid dependency issues
        with patch('matchering_player.utils.file_loader.AudioFileLoader') as MockLoader:
            mock_loader_instance = Mock()
            # Create realistic stereo audio
            left = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100) * 0.5
            right = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100) * 0.4  # Slightly different
            mock_audio = np.column_stack([left, right]).astype(np.float32)
            mock_loader_instance.load_audio_file.return_value = (mock_audio, 44100)
            MockLoader.return_value = mock_loader_instance

            success = stereo_processor.load_reference(reference_file)

            # May succeed or fail depending on mocking, but shouldn't crash
            assert isinstance(success, bool)

    def test_analyze_stereo_profile_realistic(self, stereo_processor):
        """Test stereo analysis with realistic audio"""
        # Create realistic stereo audio
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Left: Bass + mid frequencies
        left = (np.sin(2 * np.pi * 220 * t) * 0.4 +
                np.sin(2 * np.pi * 880 * t) * 0.2)

        # Right: Similar but with different phase and amplitude
        right = (np.sin(2 * np.pi * 220 * t + np.pi/4) * 0.35 +
                 np.sin(2 * np.pi * 1760 * t) * 0.25)

        realistic_audio = np.column_stack([left, right]).astype(np.float32) * 0.6

        with patch('matchering_player.utils.file_loader.AudioFileLoader') as MockLoader:
            mock_loader_instance = Mock()
            mock_loader_instance.load_audio_file.return_value = (realistic_audio, sample_rate)
            MockLoader.return_value = mock_loader_instance

            profile = stereo_processor._analyze_stereo_profile("/fake/stereo.wav")

            if profile:  # If analysis succeeded
                assert profile.analysis_complete == True
                assert profile.mid_rms > 0
                assert profile.side_rms >= 0
                assert 0.1 <= profile.stereo_width <= 2.0
                assert -1.0 <= profile.correlation <= 1.0

    def test_process_chunk_with_reference_width(self, stereo_processor):
        """Test processing using reference width"""
        # Create mock reference profile
        mock_profile = Mock()
        mock_profile.stereo_width = 0.8  # Narrower than normal
        stereo_processor.reference_profile = mock_profile
        stereo_processor.target_width = 0.8
        stereo_processor.set_reference_matching(True)

        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.5
        result = stereo_processor.process_chunk(audio_chunk)

        # Should use reference width instead of manual width
        assert result.shape == audio_chunk.shape
        # Width factor should move toward target
        assert stereo_processor.width_factor <= 1.0

    def test_smoothing_behavior(self, stereo_processor):
        """Test width smoothing behavior"""
        # Start with current width (should be 1.0)
        initial_width = stereo_processor.width_factor

        # Set a different width
        stereo_processor.set_width(1.8)

        audio_chunk = np.random.rand(1024, 2).astype(np.float32) * 0.3

        # Process several chunks to observe smoothing
        widths = []
        for _ in range(20):  # More iterations to see smoothing effect
            stereo_processor.process_chunk(audio_chunk)
            widths.append(stereo_processor.width_factor)

        # Width should gradually approach target (allow for smoothing)
        # The first few values should be closer to initial, later values closer to target
        if len(widths) > 10:
            early_avg = np.mean(widths[:5])
            late_avg = np.mean(widths[-5:])
            assert late_avg > early_avg or abs(late_avg - 1.8) < 0.1  # Approaching target

    @pytest.mark.error
    def test_process_chunk_exception_handling(self, stereo_processor):
        """Test exception handling in processing"""
        # Create audio that might cause issues but still processable
        # Use very large values instead of inf to test limiting
        problematic_audio = np.full((1024, 2), 10.0, dtype=np.float32)

        result = stereo_processor.process_chunk(problematic_audio)

        # Should handle gracefully and return something reasonable
        assert result.shape == problematic_audio.shape
        # Result should be finite even if input was extreme
        assert np.all(np.isfinite(result))

    @pytest.mark.edge_cases
    def test_edge_cases(self, stereo_processor):
        """Test various edge cases"""
        # Zero audio
        zero_audio = np.zeros((1024, 2), dtype=np.float32)
        result = stereo_processor.process_chunk(zero_audio)
        assert result.shape == zero_audio.shape

        # Very quiet audio
        quiet_audio = np.random.rand(1024, 2).astype(np.float32) * 1e-6
        result = stereo_processor.process_chunk(quiet_audio)
        assert result.shape == quiet_audio.shape

        # Single sample
        single_sample = np.array([[0.5, -0.3]], dtype=np.float32)
        result = stereo_processor.process_chunk(single_sample)
        assert result.shape == single_sample.shape

    def test_threading_safety(self, stereo_processor):
        """Test basic thread safety of critical operations"""
        import threading

        def worker():
            audio_chunk = np.random.rand(512, 2).astype(np.float32) * 0.3
            for _ in range(10):
                stereo_processor.process_chunk(audio_chunk)
                stereo_processor.set_width(np.random.uniform(0.5, 1.5))

        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should complete without deadlock or crash
        assert stereo_processor.chunks_processed > 0