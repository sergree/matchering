"""
Unit tests for matchering limiter system (hyrax.py)
Tests the Hyrax brickwall limiter implementation and configurations
"""

import pytest
import numpy as np
from tests.conftest import assert_audio_equal


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.audio
class TestLimiterBasicFunctionality:
    """Test basic limiter functionality"""

    def test_limiter_import(self):
        """Test limiter module can be imported"""
        limiter = pytest.importorskip("matchering.limiter")

        # Should have limit function
        assert hasattr(limiter, 'limit')
        assert callable(limiter.limit)

    def test_limit_basic_functionality(self):
        """Test basic limiting with audio above threshold"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create audio that exceeds threshold
        audio = np.array([[1.5, -1.2], [0.8, 1.8], [-1.9, 0.5]]).astype(np.float32)
        config = matchering.Config(threshold=1.0)

        # Apply limiting
        limited = limiter.limit(audio, config)

        # Verify limiting occurred
        assert limited.shape == audio.shape
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6  # Allow small float precision
        assert not np.array_equal(limited, audio)  # Should be different

    def test_limit_no_limiting_needed(self):
        """Test that audio below threshold is not modified"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create audio below threshold
        audio = np.array([[0.3, -0.4], [0.2, 0.5], [-0.6, 0.1]]).astype(np.float32)
        config = matchering.Config(threshold=1.0)

        # Apply limiting
        limited = limiter.limit(audio, config)

        # Should not be modified
        np.testing.assert_array_equal(limited, audio)

    def test_limit_different_thresholds(self):
        """Test limiting with different threshold values"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create test audio
        audio = np.random.random((1000, 2)).astype(np.float32) * 2.0  # Range 0-2

        # Test different thresholds (within valid range)
        thresholds = [0.5, 0.8, 1.0]

        for threshold in thresholds:
            config = matchering.Config(threshold=threshold)
            limited = limiter.limit(audio, config)

            # Verify threshold is respected
            max_amplitude = np.max(np.abs(limited))
            assert max_amplitude <= threshold + 1e-6, f"Failed for threshold {threshold}"

            # Verify shape is preserved
            assert limited.shape == audio.shape

    def test_limit_legacy_sample_rate_parameter(self):
        """Test legacy sample_rate parameter still works"""
        limiter = pytest.importorskip("matchering.limiter")

        # Create test audio that needs limiting
        audio = np.array([[1.5, -1.2], [0.8, 1.8]]).astype(np.float32)

        # Use legacy sample_rate parameter
        limited = limiter.limit(audio, sample_rate=44100)

        # Should still work and limit the audio
        assert limited.shape == audio.shape
        assert np.max(np.abs(limited)) <= 1.0  # Default threshold


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.audio
class TestLimiterConfiguration:
    """Test limiter with different configurations"""

    def test_limiter_config_parameters(self):
        """Test limiter with custom LimiterConfig parameters"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create test audio
        audio = np.random.random((2000, 2)).astype(np.float32) * 1.5

        # Create custom limiter config
        limiter_config = matchering.defaults.LimiterConfig(
            attack=2.0,  # Custom attack time
            hold=2.0,    # Custom hold time
            release=4000,  # Custom release time
            attack_filter_coefficient=-3,
            hold_filter_order=2,
            release_filter_order=2
        )

        # Create main config with custom limiter
        config = matchering.Config(
            threshold=0.8,
            limiter=limiter_config
        )

        # Apply limiting
        limited = limiter.limit(audio, config)

        # Verify basic functionality
        assert limited.shape == audio.shape
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6

    def test_limiter_different_sample_rates(self):
        """Test limiter with different sample rates"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create test audio
        audio = np.random.random((1000, 2)).astype(np.float32) * 1.5

        # Test different sample rates
        sample_rates = [22050, 44100, 48000, 96000]

        for sr in sample_rates:
            config = matchering.Config(
                internal_sample_rate=sr,
                threshold=0.9
            )

            limited = limiter.limit(audio, config)

            # Verify limiting works at all sample rates
            assert limited.shape == audio.shape
            assert np.max(np.abs(limited)) <= config.threshold + 1e-6

    def test_limiter_extreme_configurations(self):
        """Test limiter with extreme configuration values"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        audio = np.random.random((500, 2)).astype(np.float32) * 1.8

        # Test very low threshold
        config_low = matchering.Config(threshold=0.1)
        limited_low = limiter.limit(audio, config_low)
        assert np.max(np.abs(limited_low)) <= 0.1 + 1e-6

        # Test maximum valid threshold (should not limit much for normal audio)
        config_high = matchering.Config(threshold=1.0)
        limited_high = limiter.limit(audio, config_high)
        # Audio peaks around 1.8, so limiting should occur
        assert np.max(np.abs(limited_high)) <= 1.0


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.edge_cases
class TestLimiterEdgeCases:
    """Test limiter edge cases and error conditions"""

    def test_limit_empty_audio(self):
        """Test limiter with empty audio array"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create empty audio
        empty_audio = np.array([]).reshape(0, 2).astype(np.float32)
        config = matchering.Config()

        # Should handle empty audio gracefully
        limited = limiter.limit(empty_audio, config)

        assert limited.shape == (0, 2)
        assert limited.dtype == np.float32

    def test_limit_single_sample(self):
        """Test limiter with single audio sample"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Single sample that needs limiting
        single_sample = np.array([[1.5, -1.8]]).astype(np.float32)
        config = matchering.Config(threshold=1.0)

        limited = limiter.limit(single_sample, config)

        assert limited.shape == (1, 2)
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6

    def test_limit_very_short_audio(self):
        """Test limiter with very short audio"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Very short audio (5 samples)
        short_audio = np.array([
            [1.2, -1.1],
            [0.8, 1.9],
            [-1.5, 0.3],
            [1.7, -0.9],
            [0.4, 1.3]
        ]).astype(np.float32)

        config = matchering.Config(threshold=1.0)
        limited = limiter.limit(short_audio, config)

        assert limited.shape == short_audio.shape
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6

    def test_limit_silent_audio(self):
        """Test limiter with silent audio"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Silent audio
        silent_audio = np.zeros((1000, 2), dtype=np.float32)
        config = matchering.Config()

        limited = limiter.limit(silent_audio, config)

        # Should remain silent and unchanged
        np.testing.assert_array_equal(limited, silent_audio)

    def test_limit_mono_audio(self):
        """Test limiter with mono audio (single channel)"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create mono audio that needs limiting
        mono_audio = np.array([[1.5], [0.8], [-1.2], [1.9]]).astype(np.float32)
        config = matchering.Config(threshold=1.0)

        limited = limiter.limit(mono_audio, config)

        assert limited.shape == mono_audio.shape
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6

    def test_limit_extreme_values(self):
        """Test limiter with extreme audio values"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create audio with extreme values
        extreme_audio = np.array([
            [10.0, -5.0],
            [3.0, 8.0],
            [-15.0, 2.0],
            [0.1, -12.0]
        ]).astype(np.float32)

        config = matchering.Config(threshold=1.0)
        limited = limiter.limit(extreme_audio, config)

        # Should handle extreme values and limit them properly
        assert limited.shape == extreme_audio.shape
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6
        assert not np.array_equal(limited, extreme_audio)

    def test_limit_already_limited_audio(self):
        """Test limiter with audio that's already properly limited"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create audio that's already at the threshold
        limited_audio = np.array([
            [1.0, -0.95],
            [0.8, 1.0],
            [-1.0, 0.3],
            [0.7, -0.9]
        ]).astype(np.float32)

        config = matchering.Config(threshold=1.0)
        re_limited = limiter.limit(limited_audio, config)

        # Should be mostly unchanged (may have tiny differences due to processing)
        assert re_limited.shape == limited_audio.shape
        assert np.max(np.abs(re_limited)) <= config.threshold + 1e-6
        # Should be very similar to input
        np.testing.assert_array_almost_equal(re_limited, limited_audio, decimal=5)


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.audio
class TestLimiterQuality:
    """Test limiter audio quality and characteristics"""

    def test_limit_preserves_audio_length(self):
        """Test that limiting preserves audio length"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create various length audio
        lengths = [100, 1000, 5000, 10000]

        for length in lengths:
            audio = np.random.random((length, 2)).astype(np.float32) * 1.5
            config = matchering.Config(threshold=0.8)

            limited = limiter.limit(audio, config)

            assert len(limited) == length, f"Failed for length {length}"
            assert limited.shape == audio.shape

    def test_limit_preserves_stereo_balance(self):
        """Test that limiting preserves stereo balance characteristics"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create audio with known stereo characteristics
        duration = 1000
        left_channel = np.sin(np.linspace(0, 10*np.pi, duration)) * 1.2
        right_channel = np.cos(np.linspace(0, 10*np.pi, duration)) * 1.5

        audio = np.column_stack([left_channel, right_channel]).astype(np.float32)
        config = matchering.Config(threshold=1.0)

        limited = limiter.limit(audio, config)

        # Both channels should be limited but maintain relative characteristics
        assert limited.shape == audio.shape
        assert np.max(np.abs(limited[:, 0])) <= config.threshold + 1e-6
        assert np.max(np.abs(limited[:, 1])) <= config.threshold + 1e-6

        # Verify correlation between channels is maintained (to some degree)
        original_corr = np.corrcoef(audio[:, 0], audio[:, 1])[0, 1]
        limited_corr = np.corrcoef(limited[:, 0], limited[:, 1])[0, 1]

        # Correlation should be similar (allowing for some change due to limiting)
        assert abs(original_corr - limited_corr) < 0.3

    def test_limit_frequency_content_preservation(self):
        """Test that limiting doesn't dramatically alter frequency content"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create audio with specific frequency content
        sample_rate = 44100
        duration = 0.5
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Mix of frequencies
        freq1 = 440  # A4
        freq2 = 880  # A5
        audio = np.column_stack([
            (np.sin(2*np.pi*freq1*t) + 0.5*np.sin(2*np.pi*freq2*t)) * 1.3,
            (np.cos(2*np.pi*freq1*t) + 0.3*np.cos(2*np.pi*freq2*t)) * 1.4
        ]).astype(np.float32)

        config = matchering.Config(threshold=1.0)
        limited = limiter.limit(audio, config)

        # Verify limiting occurred
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6

        # The fundamental frequencies should still be detectable
        # (This is a basic check - comprehensive frequency analysis would be more complex)
        assert limited.shape == audio.shape
        assert np.std(limited) > 0.1  # Should not be overly flattened

    def test_limit_dynamic_range_impact(self):
        """Test impact of limiting on dynamic range"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create audio with specific dynamic range
        quiet_section = np.random.random((1000, 2)) * 0.1  # Quiet
        loud_section = np.random.random((1000, 2)) * 1.8   # Loud (needs limiting)
        audio = np.vstack([quiet_section, loud_section]).astype(np.float32)

        config = matchering.Config(threshold=1.0)
        limited = limiter.limit(audio, config)

        # Quiet section should be mostly unchanged
        quiet_limited = limited[:1000]
        np.testing.assert_array_almost_equal(quiet_limited, quiet_section, decimal=3)

        # Loud section should be limited
        loud_limited = limited[1000:]
        assert np.max(np.abs(loud_limited)) <= config.threshold + 1e-6


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.performance
@pytest.mark.slow
class TestLimiterPerformance:
    """Test limiter performance characteristics"""

    def test_limit_processing_speed(self):
        """Test that limiting completes in reasonable time"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")
        import time

        # Create longer audio for performance testing
        duration = 10.0  # 10 seconds
        sample_rate = 44100
        samples = int(duration * sample_rate)
        audio = np.random.random((samples, 2)).astype(np.float32) * 1.5

        config = matchering.Config(threshold=0.9)

        # Time the limiting process
        start_time = time.perf_counter()
        limited = limiter.limit(audio, config)
        end_time = time.perf_counter()

        processing_time = end_time - start_time

        # Should process faster than real-time (very generous limit)
        max_time = duration * 2  # 2x real-time
        assert processing_time < max_time, f"Limiting took {processing_time:.2f}s for {duration}s audio"

        # Verify processing was successful
        assert limited.shape == audio.shape
        assert np.max(np.abs(limited)) <= config.threshold + 1e-6

    def test_limit_memory_efficiency(self):
        """Test limiter memory usage with large audio"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Create large audio file (5 minutes at 44.1 kHz)
        samples = 5 * 60 * 44100
        # Use smaller data type for initial creation to save memory
        audio = (np.random.random((samples, 2)) * 1.5).astype(np.float32)

        config = matchering.Config(threshold=1.0)

        try:
            # Should handle large files without memory errors
            limited = limiter.limit(audio, config)

            assert limited.shape == audio.shape
            assert np.max(np.abs(limited)) <= config.threshold + 1e-6

        except MemoryError:
            pytest.skip("Insufficient memory for large audio test")

    def test_limit_different_audio_sizes(self):
        """Test limiter with various audio sizes"""
        limiter = pytest.importorskip("matchering.limiter")
        matchering = pytest.importorskip("matchering")

        # Test various sizes
        sizes = [10, 100, 1000, 10000, 50000]

        for size in sizes:
            audio = np.random.random((size, 2)).astype(np.float32) * 1.4
            config = matchering.Config(threshold=1.0)

            limited = limiter.limit(audio, config)

            assert limited.shape == audio.shape, f"Failed for size {size}"
            assert np.max(np.abs(limited)) <= config.threshold + 1e-6


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.integration
class TestLimiterIntegration:
    """Test limiter integration with other components"""

    def test_limit_with_processing_pipeline(self, test_audio_files):
        """Test limiter as part of the full processing pipeline"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")

        # Load test files
        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")

        # Process with limiting enabled
        config = matchering.Config(threshold=0.95)
        result_limited, result_no_limiter, _ = stages.main(
            target, reference, config,
            need_default=True,
            need_no_limiter=True
        )

        # Verify limited version respects threshold
        assert np.max(np.abs(result_limited)) <= config.threshold + 1e-6

        # Verify unlimited version may exceed threshold
        # (depending on processing, it might or might not exceed)
        assert result_no_limiter is not None

        # Limited and unlimited should be different if limiting was needed
        if np.max(np.abs(result_no_limiter)) > config.threshold:
            assert not np.array_equal(result_limited, result_no_limiter)

    def test_limit_consistency_with_dsp_functions(self):
        """Test limiter consistency with other DSP functions"""
        limiter = pytest.importorskip("matchering.limiter")
        dsp = pytest.importorskip("matchering.dsp")
        matchering = pytest.importorskip("matchering")

        # Create test audio
        audio = np.random.random((2000, 2)).astype(np.float32) * 1.6
        config = matchering.Config(threshold=1.0)

        # Apply limiting
        limited = limiter.limit(audio, config)

        # Test that other DSP functions work with limited audio
        rms_limited = dsp.rms(limited)
        assert rms_limited > 0

        # Test amplification after limiting
        amplified = dsp.amplify(limited, 0.8)
        assert amplified.shape == limited.shape

        # Test normalization after limiting
        normalized, _ = dsp.normalize(limited, threshold=0.9)
        assert normalized.shape == limited.shape