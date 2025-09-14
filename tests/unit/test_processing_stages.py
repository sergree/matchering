"""
Unit tests for processing stages (stages.py)
Tests the main processing pipeline stages: level matching, frequency matching, and limiting
"""

import pytest
import numpy as np
from tests.conftest import assert_audio_equal, assert_rms_similar


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.audio
class TestProcessingStagesMain:
    """Test main processing stages pipeline"""

    def test_main_basic_processing(self, test_audio_files):
        """Test basic processing pipeline with real audio files"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")

        # Load test audio files
        target, target_sr = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, reference_sr = loader.load(test_audio_files["loud_reference.wav"], "reference")

        # Create config
        config = matchering.Config()

        # Process through stages
        result, result_no_limiter, result_no_limiter_normalized = stages.main(
            target, reference, config,
            need_default=True,
            need_no_limiter=True,
            need_no_limiter_normalized=True
        )

        # Verify all outputs are generated
        assert result is not None
        assert result_no_limiter is not None
        assert result_no_limiter_normalized is not None

        # Verify output shapes match target
        assert result.shape == target.shape
        assert result_no_limiter.shape == target.shape
        assert result_no_limiter_normalized.shape == target.shape

        # Verify output data types (should be floating point)
        assert np.issubdtype(result.dtype, np.floating)
        assert np.issubdtype(result_no_limiter.dtype, np.floating)
        assert np.issubdtype(result_no_limiter_normalized.dtype, np.floating)

        # Verify outputs are different from input (processing occurred)
        assert not np.array_equal(result, target)
        assert not np.array_equal(result_no_limiter, target)

        # Verify outputs have reasonable amplitude ranges
        assert np.max(np.abs(result)) <= 1.0  # Should be limited
        assert np.max(np.abs(result_no_limiter_normalized)) <= 1.0  # Should be normalized

    def test_main_selective_outputs(self, test_audio_files):
        """Test main() with selective output generation"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")

        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")
        config = matchering.Config()

        # Test with only default output
        result, result_no_limiter, result_no_limiter_normalized = stages.main(
            target.copy(), reference.copy(), config,
            need_default=True,
            need_no_limiter=False,
            need_no_limiter_normalized=False
        )

        assert result is not None
        assert result_no_limiter is None
        assert result_no_limiter_normalized is None

        # Test with only no_limiter output
        result, result_no_limiter, result_no_limiter_normalized = stages.main(
            target.copy(), reference.copy(), config,
            need_default=False,
            need_no_limiter=True,
            need_no_limiter_normalized=False
        )

        assert result is None
        assert result_no_limiter is not None
        assert result_no_limiter_normalized is None

        # Test with only normalized output
        result, result_no_limiter, result_no_limiter_normalized = stages.main(
            target.copy(), reference.copy(), config,
            need_default=False,
            need_no_limiter=False,
            need_no_limiter_normalized=True
        )

        assert result is None
        assert result_no_limiter is None
        assert result_no_limiter_normalized is not None

    def test_main_different_configurations(self, test_audio_files):
        """Test main() with different configurations"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")

        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")

        # Test with custom config
        config = matchering.Config(
            fft_size=2048,          # Smaller FFT
            rms_correction_steps=2,  # Fewer correction steps
            threshold=0.9           # Different threshold
        )

        result, result_no_limiter, _ = stages.main(
            target, reference, config,
            need_default=True,
            need_no_limiter=True
        )

        assert result is not None
        assert result_no_limiter is not None
        assert result.shape == target.shape

    def test_main_level_matching_effectiveness(self, test_audio_files):
        """Test that level matching actually improves RMS similarity"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")
        dsp = pytest.importorskip("matchering.dsp")

        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")
        config = matchering.Config()

        # Calculate original RMS levels
        target_rms = dsp.rms(target)
        reference_rms = dsp.rms(reference)
        original_rms_diff = abs(target_rms - reference_rms)

        # Process
        result, _, _ = stages.main(
            target, reference, config,
            need_default=True
        )

        # Calculate processed RMS
        result_rms = dsp.rms(result)
        processed_rms_diff = abs(result_rms - reference_rms)

        # Level matching should improve RMS similarity
        # (Allow some tolerance since limiting and other processing affects final RMS)
        improvement_ratio = original_rms_diff / max(processed_rms_diff, 1e-6)
        assert improvement_ratio > 1.5  # Should show significant improvement


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.audio
class TestProcessingStagesFunctionality:
    """Test specific functionality of processing stages"""

    def test_stages_with_synthetic_audio(self):
        """Test stages with controlled synthetic audio"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        dsp = pytest.importorskip("matchering.dsp")

        # Create synthetic audio with known characteristics
        duration = 5.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)

        # Target: quiet sine wave
        target_amplitude = 0.1
        target = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * target_amplitude,
            np.sin(2 * np.pi * 440 * t * 1.01) * target_amplitude * 0.9
        ]).astype(np.float32)

        # Reference: loud sine wave
        reference_amplitude = 0.6
        reference = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * reference_amplitude,
            np.sin(2 * np.pi * 440 * t * 1.01) * reference_amplitude * 0.9
        ]).astype(np.float32)

        config = matchering.Config()

        # Process
        result, result_no_limiter, result_no_limiter_normalized = stages.main(
            target, reference, config,
            need_default=True,
            need_no_limiter=True,
            need_no_limiter_normalized=True
        )

        # Verify basic properties
        assert result.shape == target.shape
        assert result_no_limiter.shape == target.shape
        assert result_no_limiter_normalized.shape == target.shape

        # Verify RMS increase (target should become louder)
        target_rms = dsp.rms(target)
        result_rms = dsp.rms(result)
        assert result_rms > target_rms

        # Verify different output variants (may be identical if no limiting/normalization needed)
        # Check if limiting was actually needed by examining peak levels
        result_peak = np.max(np.abs(result))
        result_no_limiter_peak = np.max(np.abs(result_no_limiter))

        if result_no_limiter_peak > 0.99:  # If limiting was needed
            assert not np.array_equal(result, result_no_limiter)

        # Check if normalization was needed
        if result_no_limiter_peak > config.threshold:
            assert not np.array_equal(result_no_limiter, result_no_limiter_normalized)

    def test_stages_stereo_width_preservation(self):
        """Test that stereo width characteristics are preserved"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        dsp = pytest.importorskip("matchering.dsp")

        # Create stereo audio with specific width characteristics
        duration = 3.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)

        # Target: narrow stereo (similar L/R)
        target = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.2,
            np.sin(2 * np.pi * 440 * t) * 0.18  # Slightly different
        ]).astype(np.float32)

        # Reference: wide stereo (different L/R)
        reference = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.6,
            np.sin(2 * np.pi * 880 * t) * 0.6  # Different frequency
        ]).astype(np.float32)

        config = matchering.Config()

        # Process
        result, _, _ = stages.main(target, reference, config, need_default=True)

        # Calculate stereo characteristics
        target_mid, target_side = dsp.lr_to_ms(target)
        reference_mid, reference_side = dsp.lr_to_ms(reference)
        result_mid, result_side = dsp.lr_to_ms(result)

        # Verify stereo processing occurred
        target_side_rms = dsp.rms(target_side)
        result_side_rms = dsp.rms(result_side)

        # Side component should be processed (may increase or decrease based on reference)
        assert not np.isclose(target_side_rms, result_side_rms, rtol=0.1)

    def test_stages_memory_efficiency(self, test_audio_files):
        """Test that stages process without memory issues"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")

        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")

        # Use long audio if available, otherwise repeat short audio
        if len(target) < 44100 * 10:  # Less than 10 seconds
            # Repeat to make longer
            target = np.tile(target, (5, 1))
            reference = np.tile(reference, (5, 1))

        config = matchering.Config()

        # Process larger audio
        result, result_no_limiter, _ = stages.main(
            target, reference, config,
            need_default=True,
            need_no_limiter=True
        )

        # Should complete without memory errors
        assert result is not None
        assert result_no_limiter is not None
        assert result.shape == target.shape


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.edge_cases
class TestProcessingStagesEdgeCases:
    """Test edge cases and error conditions"""

    def test_stages_minimal_audio_length(self):
        """Test processing with minimal audio length"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")

        # Create very short audio (just above minimum FFT size)
        config = matchering.Config(fft_size=1024)
        samples = config.fft_size + 100  # Slightly more than FFT size

        target = np.random.random((samples, 2)).astype(np.float32) * 0.2
        reference = np.random.random((samples, 2)).astype(np.float32) * 0.6

        # Should process without errors
        result, _, _ = stages.main(target, reference, config, need_default=True)

        assert result is not None
        assert result.shape == target.shape

    def test_stages_identical_target_reference(self):
        """Test processing when target and reference are identical"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")

        # Create identical audio
        audio = np.random.random((44100, 2)).astype(np.float32) * 0.5
        config = matchering.Config(allow_equality=True)

        # Process identical audio
        result, result_no_limiter, _ = stages.main(
            audio.copy(), audio.copy(), config,
            need_default=True,
            need_no_limiter=True
        )

        # Should process successfully (though result may be similar to input)
        assert result is not None
        assert result_no_limiter is not None
        assert result.shape == audio.shape

    def test_stages_extreme_amplitude_differences(self):
        """Test processing with extreme amplitude differences"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")

        # Very quiet target
        target = np.random.random((44100, 2)).astype(np.float32) * 0.001

        # Very loud reference
        reference = np.random.random((44100, 2)).astype(np.float32) * 0.9

        config = matchering.Config()

        # Should handle extreme differences
        result, _, _ = stages.main(target, reference, config, need_default=True)

        assert result is not None
        assert result.shape == target.shape
        assert np.max(np.abs(result)) <= 1.0  # Should be limited

    def test_stages_different_configurations_edge_cases(self):
        """Test stages with edge case configurations"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")

        target = np.random.random((44100, 2)).astype(np.float32) * 0.3
        reference = np.random.random((44100, 2)).astype(np.float32) * 0.7

        # Test with minimal RMS correction steps
        config_min_rms = matchering.Config(rms_correction_steps=0)
        result_min, _, _ = stages.main(target.copy(), reference.copy(), config_min_rms, need_default=True)
        assert result_min is not None

        # Test with maximum RMS correction steps
        config_max_rms = matchering.Config(rms_correction_steps=8)
        result_max, _, _ = stages.main(target.copy(), reference.copy(), config_max_rms, need_default=True)
        assert result_max is not None

        # Test with different threshold values
        config_low_thresh = matchering.Config(threshold=0.5)
        result_low, _, _ = stages.main(target.copy(), reference.copy(), config_low_thresh, need_default=True)
        assert result_low is not None

    def test_stages_no_outputs_requested(self):
        """Test stages when no outputs are requested"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")

        target = np.random.random((10000, 2)).astype(np.float32) * 0.3
        reference = np.random.random((10000, 2)).astype(np.float32) * 0.7
        config = matchering.Config()

        # Request no outputs
        result, result_no_limiter, result_no_limiter_normalized = stages.main(
            target, reference, config,
            need_default=False,
            need_no_limiter=False,
            need_no_limiter_normalized=False
        )

        # All outputs should be None
        assert result is None
        assert result_no_limiter is None
        assert result_no_limiter_normalized is None

    def test_stages_normalized_output_behavior(self):
        """Test normalized output specific behavior"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")

        # Create audio that will need normalization
        target = np.random.random((20000, 2)).astype(np.float32) * 0.2
        reference = np.random.random((20000, 2)).astype(np.float32) * 0.8

        config = matchering.Config(threshold=0.7)

        result, result_no_limiter, result_no_limiter_normalized = stages.main(
            target, reference, config,
            need_default=False,
            need_no_limiter=True,
            need_no_limiter_normalized=True
        )

        # Verify normalized output respects threshold
        if result_no_limiter_normalized is not None:
            max_amplitude = np.max(np.abs(result_no_limiter_normalized))
            assert max_amplitude <= config.threshold + 1e-6  # Allow small floating point error

        # Normalized and non-normalized should be different if normalization was needed
        if np.max(np.abs(result_no_limiter)) > config.threshold:
            assert not np.array_equal(result_no_limiter, result_no_limiter_normalized)


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.performance
@pytest.mark.slow
class TestProcessingStagesPerformance:
    """Test performance characteristics of processing stages"""

    def test_stages_processing_time(self, test_audio_files):
        """Test that processing completes in reasonable time"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")
        import time

        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")
        config = matchering.Config()

        # Time the processing
        start_time = time.perf_counter()

        result, _, _ = stages.main(target, reference, config, need_default=True)

        end_time = time.perf_counter()
        processing_time = end_time - start_time

        # Should complete in reasonable time (adjust based on audio length)
        max_time = max(30.0, len(target) / 44100 * 5)  # 5x real-time max
        assert processing_time < max_time, f"Processing took {processing_time:.2f}s"

        # Verify processing was successful
        assert result is not None
        assert not np.array_equal(result, target)

    def test_stages_output_quality(self, test_audio_files):
        """Test output quality characteristics"""
        stages = pytest.importorskip("matchering.stages")
        matchering = pytest.importorskip("matchering")
        loader = pytest.importorskip("matchering.loader")

        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")
        config = matchering.Config()

        result, result_no_limiter, _ = stages.main(
            target, reference, config,
            need_default=True,
            need_no_limiter=True
        )

        # Quality checks
        # 1. No NaN or Inf values
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
        assert not np.any(np.isnan(result_no_limiter))
        assert not np.any(np.isinf(result_no_limiter))

        # 2. Reasonable amplitude range
        assert np.max(np.abs(result)) <= 1.0
        assert np.min(result) >= -1.0

        # 3. Audio should not be silent
        assert np.max(np.abs(result)) > 1e-6
        assert np.max(np.abs(result_no_limiter)) > 1e-6

        # 4. Limited result should have controlled peaks
        limited_peaks = np.sum(np.abs(result) > 0.99)
        unlimited_peaks = np.sum(np.abs(result_no_limiter) > 0.99)

        # Limited version should have fewer extreme peaks
        assert limited_peaks <= unlimited_peaks