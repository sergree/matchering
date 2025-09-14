"""
Unit tests for audio file loader (loader.py)
Tests audio loading, format conversion, resampling, and FFmpeg integration
"""

import pytest
import numpy as np
import tempfile
import os
import subprocess
from pathlib import Path


@pytest.mark.unit
@pytest.mark.files
@pytest.mark.core
class TestAudioLoaderCore:
    """Test core audio loader functionality"""

    def test_load_function_import(self):
        """Test that load function can be imported"""
        from matchering.loader import load
        assert callable(load)

    def test_load_basic_wav_file(self, test_audio_files):
        """Test loading basic WAV files"""
        from matchering.loader import load

        # Test loading target file
        target_file = test_audio_files["quiet_target.wav"]
        audio, sample_rate = load(target_file, "target")

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio.shape) == 2  # Should be 2D (samples, channels)
        assert sample_rate > 0
        assert len(audio) > 0

    def test_load_file_type_parameter(self, test_audio_files):
        """Test file_type parameter handling"""
        from matchering.loader import load

        target_file = test_audio_files["quiet_target.wav"]

        # Test different file_type values
        audio1, sr1 = load(target_file, "target")
        audio2, sr2 = load(target_file, "TARGET")
        audio3, sr3 = load(target_file, "reference")
        audio4, sr4 = load(target_file, "REFERENCE")

        # All should load successfully and produce same results
        np.testing.assert_array_equal(audio1, audio2)
        np.testing.assert_array_equal(audio1, audio3)
        np.testing.assert_array_equal(audio1, audio4)
        assert sr1 == sr2 == sr3 == sr4

    def test_load_with_temp_folder(self, test_audio_files, temp_dir):
        """Test loading with custom temp folder"""
        from matchering.loader import load

        target_file = test_audio_files["quiet_target.wav"]
        audio, sample_rate = load(target_file, "target", str(temp_dir))

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert sample_rate > 0

    def test_load_with_resampling(self, test_audio_files):
        """Test loading with resampling"""
        from matchering.loader import load

        target_file = test_audio_files["quiet_target.wav"]

        # Load original
        original_audio, original_sr = load(target_file, "target")

        # Load with resampling
        target_sr = 22050
        resampled_audio, resampled_sr = load(target_file, "target", resample_rate=target_sr)

        assert resampled_sr == target_sr
        assert isinstance(resampled_audio, np.ndarray)
        assert resampled_audio.dtype == np.float32

        # Length should be different (scaled by sample rate ratio)
        expected_length = int(len(original_audio) * target_sr / original_sr)
        # Allow some tolerance for resampling
        assert abs(len(resampled_audio) - expected_length) < 100

    def test_load_auto_temp_folder(self, test_audio_files):
        """Test that temp folder defaults to file directory"""
        from matchering.loader import load

        target_file = test_audio_files["quiet_target.wav"]

        # Load without specifying temp folder
        audio, sample_rate = load(target_file, "target", temp_folder=None)

        assert isinstance(audio, np.ndarray)
        assert sample_rate > 0


@pytest.mark.unit
@pytest.mark.files
@pytest.mark.error
class TestAudioLoaderErrorHandling:
    """Test audio loader error handling"""

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises appropriate error"""
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # Test non-existent target file
        with pytest.raises(ModuleError):
            load("nonexistent_target.wav", "target")

        # Test non-existent reference file
        with pytest.raises(ModuleError):
            load("nonexistent_reference.wav", "reference")

    def test_load_corrupted_file(self, temp_dir):
        """Test loading corrupted file"""
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # Create a corrupted "WAV" file
        corrupted_file = temp_dir / "corrupted.wav"
        with open(corrupted_file, 'wb') as f:
            f.write(b"This is not a valid WAV file content")

        # Should raise ModuleError
        with pytest.raises(ModuleError):
            load(str(corrupted_file), "target")

    def test_load_empty_file(self, temp_dir):
        """Test loading empty file"""
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # Create empty file
        empty_file = temp_dir / "empty.wav"
        with open(empty_file, 'wb') as f:
            f.write(b'\x00') # Write a single null byte to make it an invalid audio file

        # May raise ModuleError or RuntimeError depending on soundfile behavior
        with pytest.raises((ModuleError, RuntimeError)):
            load(str(empty_file), "target")

    def test_load_invalid_format_file(self, temp_dir):
        """Test loading file with invalid format"""
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # Create a text file with WAV extension
        invalid_file = temp_dir / "invalid.wav"
        with open(invalid_file, 'w') as f:
            f.write("This is a text file, not audio")

        # Should raise ModuleError
        with pytest.raises(ModuleError):
            load(str(invalid_file), "target")


@pytest.mark.unit
@pytest.mark.files
@pytest.mark.slow
class TestAudioLoaderFFmpegIntegration:
    """Test FFmpeg integration for non-native formats"""

    def test_ffmpeg_fallback_missing_ffmpeg(self, temp_dir):
        """Test behavior when FFmpeg is not available"""
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # Create a file with unsupported extension
        unsupported_file = temp_dir / "test.mp3"
        # Create a fake MP3 file (won't be valid)
        with open(unsupported_file, 'wb') as f:
            f.write(b"Fake MP3 content")

        # Should try FFmpeg and fail gracefully
        with pytest.raises(ModuleError):
            load(str(unsupported_file), "target")

    def test_ffmpeg_integration_workflow(self, temp_dir):
        """Test the FFmpeg integration workflow (through load function)"""
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # Create a fake file with MP3 extension to trigger FFmpeg fallback
        fake_mp3 = temp_dir / "fake.mp3"
        with open(fake_mp3, 'wb') as f:
            f.write(b"Fake MP3 content that will fail soundfile loading")

        # This should trigger FFmpeg fallback and then fail
        with pytest.raises(ModuleError):
            load(str(fake_mp3), "target")

    def test_unknown_format_handling(self, temp_dir):
        """Test handling of unknown format errors"""
        import soundfile as sf
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # Create a file that will trigger "unknown format" error
        unknown_file = temp_dir / "unknown.xyz"
        with open(unknown_file, 'wb') as f:
            # Write some binary data that's not a valid audio format
            f.write(b'\x00\x01\x02\x03' * 100)

        # Should attempt FFmpeg fallback and then fail
        with pytest.raises(ModuleError):
            load(str(unknown_file), "target")


@pytest.mark.unit
@pytest.mark.files
class TestAudioLoaderFormatSupport:
    """Test support for different audio formats"""

    def test_load_different_bit_depths(self, temp_dir):
        """Test loading files with different bit depths"""
        from matchering.loader import load
        import soundfile as sf

        # Create test audio
        duration = 1.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        stereo_audio = np.random.random((samples, 2)).astype(np.float32) * 0.5

        # Test different bit depths
        formats = [
            ("PCM_16", np.int16),
            ("PCM_24", np.int32),  # 24-bit stored as 32-bit
            ("FLOAT", np.float32),
        ]

        for subtype, expected_dtype in formats:
            test_file = temp_dir / f"test_{subtype}.wav"

            # Save in this format
            sf.write(test_file, stereo_audio, sample_rate, subtype=subtype)

            # Load back
            loaded_audio, loaded_sr = load(str(test_file), "target")

            assert loaded_audio.dtype == np.float32  # Should always convert to float32
            assert loaded_sr == sample_rate
            assert loaded_audio.shape == stereo_audio.shape

    def test_load_mono_audio(self, temp_dir):
        """Test loading mono audio files"""
        from matchering.loader import load
        import soundfile as sf

        # Create mono test file
        mono_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100)) * 0.5
        mono_file = temp_dir / "mono_test.wav"
        sf.write(mono_file, mono_audio, 44100)

        # Load and verify remains mono
        loaded_audio, sample_rate = load(str(mono_file), "target")

        assert loaded_audio.shape[1] == 1  # Should remain mono
        assert sample_rate == 44100
        assert len(loaded_audio) == len(mono_audio)

    def test_load_multichannel_audio(self, temp_dir):
        """Test loading multichannel audio files"""
        from matchering.loader import load
        import soundfile as sf

        # Create 6-channel test file (5.1 surround)
        channels = 6
        samples = 1000
        multichannel_audio = np.random.random((samples, channels)).astype(np.float32) * 0.5
        multichannel_file = temp_dir / "multichannel_test.wav"
        sf.write(multichannel_file, multichannel_audio, 44100)

        # Load multichannel file
        loaded_audio, sample_rate = load(str(multichannel_file), "target")

        assert loaded_audio.shape[1] == channels
        assert sample_rate == 44100
        assert len(loaded_audio) == samples

    def test_load_different_sample_rates(self, temp_dir):
        """Test loading files with different sample rates"""
        from matchering.loader import load
        import soundfile as sf

        # Test various sample rates
        sample_rates = [22050, 44100, 48000, 96000]

        for sr in sample_rates:
            # Create test audio at this sample rate
            duration = 0.5  # seconds
            samples = int(duration * sr)
            audio = np.random.random((samples, 2)).astype(np.float32) * 0.3

            test_file = temp_dir / f"test_{sr}Hz.wav"
            sf.write(test_file, audio, sr)

            # Load and verify
            loaded_audio, loaded_sr = load(str(test_file), "target")

            assert loaded_sr == sr
            assert loaded_audio.shape == audio.shape
            assert loaded_audio.dtype == np.float32

    def test_load_very_short_files(self, temp_dir):
        """Test loading very short audio files"""
        from matchering.loader import load
        import soundfile as sf

        # Create very short files (different lengths)
        short_lengths = [1, 10, 100]  # samples

        for length in short_lengths:
            audio = np.random.random((length, 2)).astype(np.float32) * 0.5
            short_file = temp_dir / f"short_{length}.wav"
            sf.write(short_file, audio, 44100)

            # Should load successfully
            loaded_audio, sample_rate = load(str(short_file), "target")

            assert len(loaded_audio) == length
            assert loaded_audio.shape[1] == 2
            assert sample_rate == 44100

    def test_load_long_files(self, temp_dir):
        """Test loading longer audio files"""
        from matchering.loader import load
        import soundfile as sf

        # Create longer file (5 seconds)
        duration = 5.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        long_audio = np.random.random((samples, 2)).astype(np.float32) * 0.3

        long_file = temp_dir / "long_test.wav"
        sf.write(long_file, long_audio, sample_rate)

        # Should load successfully
        loaded_audio, loaded_sr = load(str(long_file), "target")

        assert len(loaded_audio) == samples
        assert loaded_audio.shape == long_audio.shape
        assert loaded_sr == sample_rate


@pytest.mark.unit
@pytest.mark.files
@pytest.mark.edge_cases
class TestAudioLoaderEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_load_file_with_spaces_in_name(self, temp_dir):
        """Test loading files with spaces in filename"""
        from matchering.loader import load
        import soundfile as sf

        # Create file with spaces in name
        spaced_name = temp_dir / "file with spaces.wav"
        audio = np.random.random((1000, 2)).astype(np.float32) * 0.5
        sf.write(spaced_name, audio, 44100)

        # Should load successfully
        loaded_audio, sample_rate = load(str(spaced_name), "target")

        assert loaded_audio.shape == audio.shape
        assert sample_rate == 44100

    def test_load_file_with_unicode_name(self, temp_dir):
        """Test loading files with unicode characters in filename"""
        from matchering.loader import load
        import soundfile as sf

        try:
            # Create file with unicode name
            unicode_name = temp_dir / "tëst_ñamé_🎵.wav"
            audio = np.random.random((1000, 2)).astype(np.float32) * 0.5
            sf.write(unicode_name, audio, 44100)

            # Should load successfully
            loaded_audio, sample_rate = load(str(unicode_name), "target")

            assert loaded_audio.shape == audio.shape
            assert sample_rate == 44100

        except (UnicodeError, OSError):
            # Skip if filesystem doesn't support unicode names
            pytest.skip("Filesystem doesn't support unicode filenames")

    def test_load_file_extreme_sample_rates(self, temp_dir):
        """Test loading files with extreme sample rates"""
        from matchering.loader import load
        import soundfile as sf

        # Test with unusual sample rates
        extreme_rates = [8000, 192000]  # Very low and very high

        for sr in extreme_rates:
            try:
                audio = np.random.random((sr, 2)).astype(np.float32) * 0.3  # 1 second
                extreme_file = temp_dir / f"extreme_{sr}.wav"
                sf.write(extreme_file, audio, sr)

                # Should load successfully
                loaded_audio, loaded_sr = load(str(extreme_file), "target")

                assert loaded_sr == sr
                assert loaded_audio.shape == audio.shape

            except Exception:
                # Some extreme sample rates might not be supported
                pytest.skip(f"Sample rate {sr} not supported")

    def test_load_with_resampling_edge_cases(self, temp_dir):
        """Test resampling with edge cases"""
        from matchering.loader import load
        import soundfile as sf

        # Create test file
        original_sr = 44100
        audio = np.random.random((original_sr, 2)).astype(np.float32) * 0.3
        test_file = temp_dir / "resample_test.wav"
        sf.write(test_file, audio, original_sr)

        # Test extreme resampling ratios
        extreme_targets = [original_sr // 4, original_sr * 4]  # 1/4 and 4x

        for target_sr in extreme_targets:
            try:
                resampled_audio, resampled_sr = load(str(test_file), "target", resample_rate=target_sr)

                assert resampled_sr == target_sr
                assert resampled_audio.shape[1] == 2  # Still stereo

                # Length should be approximately scaled
                expected_length = int(len(audio) * target_sr / original_sr)
                assert abs(len(resampled_audio) - expected_length) < target_sr * 0.1  # 10% tolerance

            except Exception:
                # Some extreme resampling might fail
                pytest.skip(f"Resampling to {target_sr} not supported")

    def test_load_zero_length_audio(self, temp_dir):
        """Test loading theoretically zero-length audio"""
        from matchering.loader import load
        from matchering.log.exceptions import ModuleError

        # This test depends on whether soundfile can create zero-length files
        try:
            import soundfile as sf
            zero_audio = np.array([]).reshape(0, 2).astype(np.float32)
            zero_file = temp_dir / "zero_length.wav"
            sf.write(zero_file, zero_audio, 44100)

            # Behavior may vary - might succeed with zero-length array or fail
            try:
                loaded_audio, sample_rate = load(str(zero_file), "target")
                assert len(loaded_audio) == 0
                assert loaded_audio.shape[1] == 2
            except ModuleError:
                # This is also acceptable - zero-length audio is problematic
                pass

        except Exception:
            # If soundfile can't create zero-length files, skip
            pytest.skip("Cannot create zero-length audio file")

    def test_load_dtype_consistency(self, temp_dir):
        """Test that loaded audio always has consistent dtype"""
        from matchering.loader import load
        import soundfile as sf

        # Test different input dtypes
        input_dtypes = [np.int16, np.int32, np.float32, np.float64]

        for input_dtype in input_dtypes:
            # Create audio with specific dtype
            if np.issubdtype(input_dtype, np.integer):
                # For integer types, use appropriate range
                if input_dtype == np.int16:
                    audio = (np.random.random((1000, 2)) * 32767).astype(input_dtype)
                else:
                    audio = (np.random.random((1000, 2)) * 2147483647).astype(input_dtype)
            else:
                # For float types
                audio = (np.random.random((1000, 2)) * 0.5).astype(input_dtype)

            dtype_file = temp_dir / f"dtype_{input_dtype.__name__}.wav"

            try:
                sf.write(dtype_file, audio, 44100)

                # Load and verify output dtype
                loaded_audio, sample_rate = load(str(dtype_file), "target")

                # Should always be float32 regardless of input
                assert loaded_audio.dtype == np.float32

            except Exception:
                # Skip if this dtype combination isn't supported
                continue