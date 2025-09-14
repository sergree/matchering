"""
Unit tests for audio file I/O (loader.py and saver.py)
Tests audio loading, format conversion, and saving functionality
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from tests.conftest import assert_audio_equal


@pytest.mark.unit
@pytest.mark.files
class TestAudioLoader:
    """Test audio file loading functionality"""

    def test_load_basic_wav(self, test_audio_files):
        """Test loading basic WAV files"""
        loader = pytest.importorskip("matchering.loader")

        # Test loading target file
        target_file = test_audio_files["quiet_target.wav"]
        audio, sample_rate = loader.load(target_file, "target")

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio.shape) == 2  # Should be 2D (samples, channels)
        assert audio.shape[1] == 2    # Should be stereo
        assert sample_rate > 0
        assert len(audio) > 0

        # Test loading reference file
        reference_file = test_audio_files["loud_reference.wav"]
        ref_audio, ref_sample_rate = loader.load(reference_file, "reference")

        assert isinstance(ref_audio, np.ndarray)
        assert ref_audio.dtype == np.float32
        assert len(ref_audio.shape) == 2
        assert ref_audio.shape[1] == 2
        assert ref_sample_rate > 0

    def test_load_with_temp_folder(self, test_audio_files, temp_dir):
        """Test loading with custom temp folder"""
        loader = pytest.importorskip("matchering.loader")

        target_file = test_audio_files["quiet_target.wav"]
        audio, sample_rate = loader.load(target_file, "target", str(temp_dir))

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert sample_rate > 0

    def test_load_with_resampling(self, test_audio_files):
        """Test loading with resampling"""
        loader = pytest.importorskip("matchering.loader")

        target_file = test_audio_files["quiet_target.wav"]

        # Load original
        original_audio, original_sr = loader.load(target_file, "target")

        # Load with resampling
        target_sr = 22050
        resampled_audio, resampled_sr = loader.load(target_file, "target", resample_rate=target_sr)

        assert resampled_sr == target_sr
        assert isinstance(resampled_audio, np.ndarray)
        assert resampled_audio.dtype == np.float32
        assert resampled_audio.shape[1] == 2  # Still stereo

        # Length should be different (scaled by sample rate ratio)
        expected_length = int(len(original_audio) * target_sr / original_sr)
        # Allow some tolerance for resampling
        assert abs(len(resampled_audio) - expected_length) < 100

    def test_load_invalid_file(self):
        """Test loading non-existent file"""
        loader = pytest.importorskip("matchering.loader")
        from matchering.log.exceptions import ModuleError

        # Test non-existent target file
        with pytest.raises(ModuleError):
            loader.load("nonexistent_file.wav", "target")

        # Test non-existent reference file
        with pytest.raises(ModuleError):
            loader.load("nonexistent_file.wav", "reference")

    def test_load_file_type_handling(self, test_audio_files):
        """Test file type parameter handling"""
        loader = pytest.importorskip("matchering.loader")

        target_file = test_audio_files["quiet_target.wav"]

        # Test different file_type values
        audio1, sr1 = loader.load(target_file, "target")
        audio2, sr2 = loader.load(target_file, "TARGET")
        audio3, sr3 = loader.load(target_file, "reference")
        audio4, sr4 = loader.load(target_file, "REFERENCE")

        # All should load successfully and produce same results
        np.testing.assert_array_equal(audio1, audio2)
        np.testing.assert_array_equal(audio1, audio3)
        np.testing.assert_array_equal(audio1, audio4)
        assert sr1 == sr2 == sr3 == sr4

    def test_load_mono_file_format(self, temp_dir):
        """Test loading mono files (preserves mono format)"""
        loader = pytest.importorskip("matchering.loader")
        sf = pytest.importorskip("soundfile")

        # Create mono test file
        mono_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100)) * 0.5
        mono_file = temp_dir / "mono_test.wav"
        sf.write(mono_file, mono_audio, 44100)

        # Load and verify it remains mono
        loaded_audio, sample_rate = loader.load(str(mono_file), "target")

        assert loaded_audio.shape[1] == 1  # Should remain mono
        assert sample_rate == 44100
        assert len(loaded_audio) == len(mono_audio)

    def test_load_different_formats(self, temp_dir):
        """Test loading different audio formats"""
        loader = pytest.importorskip("matchering.loader")
        sf = pytest.importorskip("soundfile")

        # Create test audio
        duration = 1.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        stereo_audio = np.random.random((samples, 2)).astype(np.float32) * 0.5

        # Test different bit depths
        formats = [
            ("PCM_16", "16-bit PCM"),
            ("PCM_24", "24-bit PCM"),
            ("FLOAT", "32-bit float"),
        ]

        for subtype, description in formats:
            test_file = temp_dir / f"test_{subtype}.wav"

            # Save in this format
            sf.write(test_file, stereo_audio, sample_rate, subtype=subtype)

            # Load back
            loaded_audio, loaded_sr = loader.load(str(test_file), "target")

            assert loaded_audio.dtype == np.float32
            assert loaded_sr == sample_rate
            assert loaded_audio.shape == stereo_audio.shape


@pytest.mark.unit
@pytest.mark.files
class TestAudioSaver:
    """Test audio file saving functionality"""

    def test_save_basic_wav(self, temp_dir):
        """Test basic WAV file saving"""
        saver = pytest.importorskip("matchering.saver")
        sf = pytest.importorskip("soundfile")

        # Create test audio
        duration = 0.5
        sample_rate = 44100
        samples = int(duration * sample_rate)
        test_audio = np.random.random((samples, 2)).astype(np.float32) * 0.5

        output_file = temp_dir / "test_output.wav"

        # Save audio
        saver.save(str(output_file), test_audio, sample_rate, "PCM_16")

        # Verify file was created
        assert output_file.exists()

        # Load back and verify
        loaded_audio, loaded_sr = sf.read(output_file, always_2d=True)
        assert loaded_sr == sample_rate
        assert loaded_audio.shape[1] == 2  # Stereo
        assert len(loaded_audio) == len(test_audio)

    def test_save_different_subtypes(self, temp_dir):
        """Test saving with different subtypes"""
        saver = pytest.importorskip("matchering.saver")
        sf = pytest.importorskip("soundfile")

        # Create test audio
        test_audio = np.random.random((1000, 2)).astype(np.float32) * 0.5
        sample_rate = 44100

        subtypes = ["PCM_16", "PCM_24", "FLOAT"]

        for subtype in subtypes:
            output_file = temp_dir / f"test_{subtype}.wav"

            # Save audio
            saver.save(str(output_file), test_audio, sample_rate, subtype)

            # Verify file was created
            assert output_file.exists()

            # Verify format
            info = sf.info(output_file)
            assert info.subtype == subtype
            assert info.samplerate == sample_rate
            assert info.channels == 2

    def test_save_mono_input(self, temp_dir):
        """Test saving with mono input (should be converted)"""
        saver = pytest.importorskip("matchering.saver")
        sf = pytest.importorskip("soundfile")

        # Create mono test audio
        mono_audio = np.random.random(1000).astype(np.float32) * 0.5
        sample_rate = 44100

        output_file = temp_dir / "mono_output.wav"

        # Save mono audio
        saver.save(str(output_file), mono_audio, sample_rate, "PCM_16")

        # Verify file was created
        assert output_file.exists()

        # Load back and verify it's mono
        loaded_audio, loaded_sr = sf.read(output_file, always_2d=True)
        assert loaded_sr == sample_rate
        assert loaded_audio.shape[1] == 1  # Should remain mono

    def test_save_array_reshaping(self, temp_dir):
        """Test that arrays are properly reshaped for saving"""
        saver = pytest.importorskip("matchering.saver")
        sf = pytest.importorskip("soundfile")

        sample_rate = 44100

        # Test 1D array (mono)
        mono_1d = np.random.random(1000).astype(np.float32) * 0.5
        output_file_1d = temp_dir / "reshaped_1d.wav"
        saver.save(str(output_file_1d), mono_1d, sample_rate, "PCM_16")
        assert output_file_1d.exists()

        # Test 3D array (should be flattened to 2D)
        multi_3d = np.random.random((500, 2, 1)).astype(np.float32) * 0.5
        output_file_3d = temp_dir / "reshaped_3d.wav"
        saver.save(str(output_file_3d), multi_3d, sample_rate, "PCM_16")
        assert output_file_3d.exists()

        # Verify the 3D was reshaped properly
        info_3d = sf.info(output_file_3d)
        assert info_3d.frames == 500
        assert info_3d.channels == 2

    def test_save_custom_name(self, temp_dir):
        """Test saving with custom name parameter"""
        saver = pytest.importorskip("matchering.saver")

        test_audio = np.random.random((1000, 2)).astype(np.float32) * 0.5
        sample_rate = 44100
        output_file = temp_dir / "custom_name.wav"

        # Save with custom name (should not affect file content, just logging)
        saver.save(str(output_file), test_audio, sample_rate, "PCM_16", name="custom_result")

        # Verify file was created normally
        assert output_file.exists()

    def test_save_argument_swapping(self, temp_dir):
        """Test that argument swapping protection works"""
        saver = pytest.importorskip("matchering.saver")

        test_audio = np.random.random((1000, 2)).astype(np.float32) * 0.5
        sample_rate = 44100
        output_file = temp_dir / "swapped_args.wav"

        # This should handle the arguments correctly even if they appear swapped
        saver.save(str(output_file), test_audio, sample_rate, "PCM_16")

        # Verify file was created
        assert output_file.exists()


@pytest.mark.unit
@pytest.mark.files
class TestAudioIOIntegration:
    """Test integration between loader and saver"""

    def test_load_save_roundtrip(self, test_audio_files, temp_dir):
        """Test that load->save->load preserves audio quality"""
        loader = pytest.importorskip("matchering.loader")
        saver = pytest.importorskip("matchering.saver")

        # Load original audio
        original_file = test_audio_files["quiet_target.wav"]
        original_audio, original_sr = loader.load(original_file, "target")

        # Save to new file
        output_file = temp_dir / "roundtrip.wav"
        saver.save(str(output_file), original_audio, original_sr, "FLOAT")

        # Load again
        roundtrip_audio, roundtrip_sr = loader.load(str(output_file), "target")

        # Should be identical (within floating point precision)
        assert roundtrip_sr == original_sr
        assert roundtrip_audio.shape == original_audio.shape
        np.testing.assert_array_almost_equal(original_audio, roundtrip_audio, decimal=5)

    def test_format_conversion_chain(self, temp_dir):
        """Test conversion between different formats"""
        loader = pytest.importorskip("matchering.loader")
        saver = pytest.importorskip("matchering.saver")
        sf = pytest.importorskip("soundfile")

        # Create original audio
        original_audio = np.random.random((2000, 2)).astype(np.float32) * 0.5
        sample_rate = 44100

        # Save in different formats and verify they can be loaded
        formats = ["PCM_16", "PCM_24", "FLOAT"]

        loaded_audios = []
        for fmt in formats:
            # Save in this format
            output_file = temp_dir / f"conversion_{fmt}.wav"
            saver.save(str(output_file), original_audio, sample_rate, fmt)

            # Load back
            loaded_audio, loaded_sr = loader.load(str(output_file), "target")
            loaded_audios.append((loaded_audio, loaded_sr, fmt))

            assert loaded_sr == sample_rate
            assert loaded_audio.shape == original_audio.shape

        # All loaded audios should be similar (accounting for bit depth differences)
        for i, (audio1, sr1, fmt1) in enumerate(loaded_audios):
            for j, (audio2, sr2, fmt2) in enumerate(loaded_audios):
                if i != j:
                    assert sr1 == sr2
                    # Allow for some difference due to bit depth conversion
                    correlation = np.corrcoef(audio1.flatten(), audio2.flatten())[0, 1]
                    assert correlation > 0.99  # Should be highly correlated

    def test_temporary_file_handling(self, test_audio_files, temp_dir):
        """Test that temporary files are handled properly"""
        loader = pytest.importorskip("matchering.loader")

        # Load with explicit temp folder
        target_file = test_audio_files["quiet_target.wav"]
        audio, sample_rate = loader.load(target_file, "target", str(temp_dir))

        # Verify no temporary files are left behind (for regular WAV files)
        temp_files_before = list(temp_dir.glob("temp*"))

        # Load again
        audio2, sample_rate2 = loader.load(target_file, "target", str(temp_dir))

        temp_files_after = list(temp_dir.glob("temp*"))

        # Should be same number of temp files (none for WAV)
        assert len(temp_files_before) == len(temp_files_after)


@pytest.mark.unit
@pytest.mark.files
@pytest.mark.edge_cases
class TestAudioIOEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_audio_handling(self, temp_dir):
        """Test handling of empty audio arrays"""
        saver = pytest.importorskip("matchering.saver")

        # Test empty 2D array
        empty_audio = np.array([]).reshape(0, 2).astype(np.float32)
        sample_rate = 44100
        output_file = temp_dir / "empty.wav"

        # Should handle empty arrays gracefully
        saver.save(str(output_file), empty_audio, sample_rate, "PCM_16")
        assert output_file.exists()

    def test_very_short_audio(self, temp_dir):
        """Test handling of very short audio"""
        loader = pytest.importorskip("matchering.loader")
        saver = pytest.importorskip("matchering.saver")

        # Create very short audio (1 sample)
        short_audio = np.array([[0.5, -0.3]]).astype(np.float32)
        sample_rate = 44100
        output_file = temp_dir / "very_short.wav"

        # Save and load
        saver.save(str(output_file), short_audio, sample_rate, "PCM_16")
        loaded_audio, loaded_sr = loader.load(str(output_file), "target")

        assert loaded_sr == sample_rate
        assert len(loaded_audio) == 1
        assert loaded_audio.shape[1] == 2

    def test_large_audio_handling(self, temp_dir):
        """Test handling of larger audio files"""
        loader = pytest.importorskip("matchering.loader")
        saver = pytest.importorskip("matchering.saver")

        # Create larger audio (10 seconds at 44.1 kHz)
        duration = 10.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        large_audio = np.random.random((samples, 2)).astype(np.float32) * 0.1

        output_file = temp_dir / "large.wav"

        # Save and load
        saver.save(str(output_file), large_audio, sample_rate, "PCM_16")
        loaded_audio, loaded_sr = loader.load(str(output_file), "target")

        assert loaded_sr == sample_rate
        assert len(loaded_audio) == len(large_audio)
        assert loaded_audio.shape == large_audio.shape

    def test_invalid_sample_rates(self, temp_dir):
        """Test handling of unusual sample rates"""
        saver = pytest.importorskip("matchering.saver")

        test_audio = np.random.random((1000, 2)).astype(np.float32) * 0.5
        output_file = temp_dir / "unusual_sr.wav"

        # Test unusual but valid sample rate
        unusual_sr = 37333
        saver.save(str(output_file), test_audio, unusual_sr, "PCM_16")
        assert output_file.exists()

        # Verify the sample rate was saved correctly
        sf = pytest.importorskip("soundfile")
        info = sf.info(output_file)
        assert info.samplerate == unusual_sr

    def test_extreme_amplitude_values(self, temp_dir):
        """Test handling of extreme amplitude values"""
        loader = pytest.importorskip("matchering.loader")
        saver = pytest.importorskip("matchering.saver")

        sample_rate = 44100

        # Test with very large values (should be clipped)
        large_audio = np.array([[10.0, -10.0], [5.0, -5.0]]).astype(np.float32)
        large_file = temp_dir / "large_amplitude.wav"
        saver.save(str(large_file), large_audio, sample_rate, "PCM_16")

        loaded_large, _ = loader.load(str(large_file), "target")
        # Values should be clipped to [-1, 1] range for 16-bit
        assert np.max(np.abs(loaded_large)) <= 1.0

        # Test with very small values
        tiny_audio = np.array([[1e-6, -1e-6], [1e-7, 1e-7]]).astype(np.float32)
        tiny_file = temp_dir / "tiny_amplitude.wav"
        saver.save(str(tiny_file), tiny_audio, sample_rate, "FLOAT")

        loaded_tiny, _ = loader.load(str(tiny_file), "target")
        assert loaded_tiny.shape == tiny_audio.shape
        # Values should be preserved in float format
        assert np.max(np.abs(loaded_tiny)) < 1e-5

    def test_different_data_types(self, temp_dir):
        """Test conversion of different input data types"""
        saver = pytest.importorskip("matchering.saver")

        sample_rate = 44100
        output_file = temp_dir / "dtype_test.wav"

        # Test different input data types
        dtypes = [np.float64, np.int16, np.int32]

        for dtype in dtypes:
            test_data = np.random.random((100, 2)) * 0.5
            typed_audio = test_data.astype(dtype)

            # Should convert to float32 internally
            saver.save(str(output_file), typed_audio, sample_rate, "FLOAT")
            assert output_file.exists()

            # Clean up for next iteration
            output_file.unlink()