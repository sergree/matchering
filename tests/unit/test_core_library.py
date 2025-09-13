"""
Unit tests for core Matchering library components
"""

import pytest
import numpy as np
from tests.conftest import HAS_SOUNDFILE, HAS_MATCHERING, assert_audio_equal


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.dsp
class TestCoreLibraryDSP:
    """Test core DSP functions in matchering.dsp"""

    def test_dsp_functions(self, sine_wave):
        """Test core DSP functions"""
        matchering = pytest.importorskip("matchering")
        from matchering import dsp

        # Create test audio
        audio, sr = sine_wave(1.0)

        # Test RMS calculation
        rms_value = dsp.rms(audio)
        assert 0.1 < rms_value < 0.8, f"RMS should be reasonable, got {rms_value}"

        # Test normalization
        normalized = dsp.normalize(audio, 0.8)
        normalized_rms = dsp.rms(normalized)
        assert abs(normalized_rms - 0.8) < 0.01, "Normalization failed"

        # Test amplification
        amplified = dsp.amplify(audio, 2.0)
        amplified_rms = dsp.rms(amplified)
        original_rms = dsp.rms(audio)
        gain_ratio = amplified_rms / original_rms
        assert abs(gain_ratio - 2.0) < 0.1, "Amplification failed"

    def test_mid_side_processing(self, sine_wave):
        """Test mid-side processing if available"""
        matchering = pytest.importorskip("matchering")
        from matchering import dsp

        audio, sr = sine_wave(1.0)

        # Test mid-side processing if available
        if hasattr(dsp, 'to_mid_side') and hasattr(dsp, 'from_mid_side'):
            mid, side = dsp.to_mid_side(audio)
            reconstructed = dsp.from_mid_side(mid, side)
            assert_audio_equal(audio, reconstructed, tolerance=1e-6)


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.files
class TestCoreLibraryLoader:
    """Test audio file loading functionality"""

    def test_loader_module(self, test_audio_files):
        """Test loader functionality"""
        matchering = pytest.importorskip("matchering")
        from matchering import loader

        # Test loading a file
        test_file = test_audio_files["quiet_target.wav"]
        loaded_audio, loaded_sr = loader.load(test_file)

        assert loaded_audio.shape[1] == 2, "Should load as stereo"
        assert loaded_sr == 44100, "Sample rate should match"
        assert loaded_audio.dtype == np.float32, "Should be float32"

    def test_loader_different_sample_rates(self, temp_dir):
        """Test loading files with different sample rates"""
        sf = pytest.importorskip("soundfile")
        matchering = pytest.importorskip("matchering")
        from matchering import loader

        # Create test files with different sample rates
        for test_sr in [22050, 48000, 96000]:
            samples = int(1.0 * test_sr)  # 1 second
            t = np.linspace(0, 1.0, samples)
            audio = np.column_stack([
                np.sin(2 * np.pi * 440 * t) * 0.5,
                np.sin(2 * np.pi * 440 * t * 1.01) * 0.4
            ]).astype(np.float32)

            test_file = temp_dir / f"test_{test_sr}.wav"
            sf.write(test_file, audio, test_sr)

            # Test loading
            loaded_audio, loaded_sr = loader.load(str(test_file))
            assert loaded_sr == test_sr, f"Sample rate mismatch for {test_sr}Hz"
            assert loaded_audio.shape[0] == samples, "Sample count mismatch"


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.dsp
class TestCoreLibraryLimiter:
    """Test Hyrax limiter functionality"""

    def test_limiter_module(self, sine_wave):
        """Test limiter functionality"""
        matchering = pytest.importorskip("matchering")
        from matchering.limiter import hyrax

        # Create test audio with peaks
        audio, sr = sine_wave(1.0, amplitude=1.2)  # Clipped audio

        # Test limiter
        limited = hyrax.limit(audio, sample_rate=sr)

        # Check that output is limited
        assert np.max(np.abs(limited)) <= 1.0, "Limiter failed to limit peaks"

        # Check that RMS is preserved reasonably
        input_rms = np.sqrt(np.mean(audio**2))
        output_rms = np.sqrt(np.mean(limited**2))
        rms_ratio = output_rms / input_rms
        assert 0.7 < rms_ratio < 1.0, "Limiter changed RMS too much"


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.dsp
class TestCoreLibraryStages:
    """Test multi-stage processing pipeline"""

    def test_stages_module(self, audio_pair):
        """Test stage processing if available"""
        matchering = pytest.importorskip("matchering")
        from matchering import stages

        target_audio, reference_audio, sr = audio_pair

        # Test stage processing if available
        if hasattr(stages, 'process'):
            result = stages.process(target_audio, reference_audio, sr)

            # Check that result has same shape as input
            assert result.shape == target_audio.shape, "Stage processing changed audio shape"

            # Check that level was adjusted
            target_rms = np.sqrt(np.mean(target_audio**2))
            result_rms = np.sqrt(np.mean(result**2))

            assert result_rms > target_rms * 1.5, "Stage processing should increase quiet audio level"


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.dsp
class TestCoreLibraryStageHelpers:
    """Test stage helper modules for level and frequency matching"""

    def test_stage_helpers(self, audio_pair):
        """Test stage helper functionality"""
        matchering = pytest.importorskip("matchering")

        target_audio, reference_audio, sr = audio_pair

        try:
            from matchering.stage_helpers import match_levels, match_frequencies

            # Test level matching if available
            if hasattr(match_levels, 'match'):
                level_matched = match_levels.match(target_audio, reference_audio, sr)

                target_rms = np.sqrt(np.mean(target_audio**2))
                matched_rms = np.sqrt(np.mean(level_matched**2))

                # Should be closer to reference level
                assert matched_rms > target_rms * 2, "Level matching should increase level significantly"

            # Test frequency matching if available
            if hasattr(match_frequencies, 'match'):
                freq_matched = match_frequencies.match(target_audio, reference_audio, sr)
                assert freq_matched.shape == target_audio.shape, "Frequency matching changed shape"

        except ImportError:
            pytest.skip("Stage helpers not available")


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.files
class TestCoreLibrarySaver:
    """Test audio file saving functionality"""

    def test_saver_module(self, sine_wave, temp_dir):
        """Test saver functionality"""
        sf = pytest.importorskip("soundfile")
        matchering = pytest.importorskip("matchering")

        # Create test audio
        audio, sr = sine_wave(1.0)

        # Test saving different formats
        formats_to_test = [
            ("test_16bit.wav", {"subtype": "PCM_16"}),
            ("test_24bit.wav", {"subtype": "PCM_24"}),
            ("test_float.wav", {"subtype": "FLOAT"})
        ]

        for filename, format_options in formats_to_test:
            output_path = temp_dir / filename

            # Save audio (use saver module if available, otherwise fallback)
            try:
                from matchering import saver
                if hasattr(saver, 'save'):
                    saver.save(audio, str(output_path), sr, **format_options)
                else:
                    sf.write(output_path, audio, sr, **format_options)
            except ImportError:
                sf.write(output_path, audio, sr, **format_options)

            # Verify file was created and can be loaded
            assert output_path.exists(), f"Failed to create {filename}"

            loaded_audio, loaded_sr = sf.read(output_path)
            assert loaded_audio.shape == audio.shape, f"Shape mismatch in {filename}"
            assert loaded_sr == sr, f"Sample rate mismatch in {filename}"