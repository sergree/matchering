"""
Unit tests for AudioFileLoader - Audio file I/O and format support
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from matchering_player.utils.file_loader import AudioFileLoader, AudioFileInfo


class TestAudioFileInfo:
    """Test the AudioFileInfo class"""

    def test_audio_file_info_initialization(self):
        """Test AudioFileInfo initialization"""
        info = AudioFileInfo("/path/to/test.wav")

        assert info.file_path == "/path/to/test.wav"
        assert info.filename == "test.wav"
        assert info.stem == "test"
        assert info.suffix == ".wav"
        assert info.sample_rate is None
        assert info.channels is None
        assert info.frames is None
        assert info.duration is None

    def test_audio_file_info_string_representation(self):
        """Test string representation of AudioFileInfo"""
        # Unanalyzed file
        info = AudioFileInfo("/path/to/test.mp3")
        assert str(info) == "test.mp3: (not analyzed)"

        # Analyzed file
        info.sample_rate = 44100
        info.channels = 2
        info.duration = 3.5
        info.format_info = "MP3"
        expected = "test.mp3: 3.5s, 44100Hz, 2ch, MP3"
        assert str(info) == expected

    def test_audio_file_info_different_extensions(self):
        """Test handling of different file extensions"""
        test_cases = [
            ("/music/song.WAV", ".wav"),
            ("/music/song.FLAC", ".flac"),
            ("/music/song.Mp3", ".mp3"),
            ("/music/song.M4A", ".m4a"),
        ]

        for file_path, expected_suffix in test_cases:
            info = AudioFileInfo(file_path)
            assert info.suffix == expected_suffix


class TestAudioFileLoader:
    """Test the AudioFileLoader class"""

    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Create simple test audio data
            sample_rate = 44100
            duration = 0.1  # 0.1 seconds
            samples = int(sample_rate * duration)

            # Generate simple sine wave
            t = np.linspace(0, duration, samples)
            left = np.sin(2 * np.pi * 440 * t) * 0.5  # A4
            right = np.sin(2 * np.pi * 880 * t) * 0.4  # A5
            audio = np.column_stack([left, right]).astype(np.float32)

            # Save as mock file data (would normally use soundfile)
            temp_path = f.name

        yield temp_path, audio, sample_rate

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_loader_initialization_with_soundfile(self):
        """Test loader initialization when soundfile is available"""
        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', False):
                loader = AudioFileLoader(target_sample_rate=48000, target_channels=2)

                assert loader.target_sample_rate == 48000
                assert loader.target_channels == 2
                assert 'soundfile' in loader.available_loaders
                assert 'librosa' not in loader.available_loaders

    def test_loader_initialization_with_librosa(self):
        """Test loader initialization when only librosa is available"""
        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', False):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
                loader = AudioFileLoader()

                assert 'librosa' in loader.available_loaders
                assert 'soundfile' not in loader.available_loaders

    def test_loader_initialization_no_libraries(self):
        """Test loader raises error when no libraries available"""
        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', False):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', False):
                with pytest.raises(RuntimeError, match="No audio loading libraries available"):
                    AudioFileLoader()

    def test_get_file_info_nonexistent_file(self):
        """Test getting info for nonexistent file"""
        loader = AudioFileLoader()

        with pytest.raises(FileNotFoundError):
            loader.get_file_info("/nonexistent/file.wav")

    def test_get_file_info_soundfile_format(self):
        """Test getting file info using soundfile"""
        loader = AudioFileLoader()

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('matchering_player.utils.file_loader.sf.SoundFile') as mock_sf:
                # Mock soundfile object
                mock_file = MagicMock()
                mock_file.samplerate = 44100
                mock_file.channels = 2
                mock_file.frames = 88200
                mock_file.format = "WAV"
                mock_file.subtype = "PCM_16"
                mock_sf.return_value.__enter__.return_value = mock_file

                # Mock file existence
                with patch('os.path.exists', return_value=True):
                    info = loader.get_file_info("/fake/test.wav")

                assert info.sample_rate == 44100
                assert info.channels == 2
                assert info.frames == 88200
                assert info.duration == 2.0  # 88200 / 44100
                assert info.format_info == "WAV PCM_16"

    def test_get_file_info_librosa_format(self):
        """Test getting file info using librosa"""
        loader = AudioFileLoader()

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', False):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
                with patch('matchering_player.utils.file_loader.librosa.get_duration', return_value=3.5):
                    with patch('os.path.exists', return_value=True):
                        info = loader.get_file_info("/fake/test.mp3")

                assert info.duration == 3.5
                assert info.format_info == "Librosa-supported .mp3"

    def test_get_file_info_unsupported_format(self):
        """Test error for unsupported format"""
        loader = AudioFileLoader()

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', False):
                with patch('os.path.exists', return_value=True):
                    with pytest.raises(ValueError, match="Unsupported audio format"):
                        loader.get_file_info("/fake/test.xyz")

    def test_load_audio_file_nonexistent(self):
        """Test loading nonexistent file"""
        loader = AudioFileLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_audio_file("/nonexistent/file.wav")

    def test_load_raw_audio_soundfile(self):
        """Test loading raw audio with soundfile"""
        loader = AudioFileLoader()

        # Mock audio data
        mock_audio = np.random.rand(4410, 2).astype(np.float32) * 0.5
        mock_sample_rate = 44100

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('matchering_player.utils.file_loader.sf.read', return_value=(mock_audio, mock_sample_rate)):
                audio_data, sample_rate = loader._load_raw_audio("/fake/test.wav", ".wav")

                np.testing.assert_array_equal(audio_data, mock_audio)
                assert sample_rate == mock_sample_rate

    def test_load_raw_audio_librosa(self):
        """Test loading raw audio with librosa"""
        loader = AudioFileLoader()

        # Mock stereo audio data (librosa format: channels first)
        mock_audio_librosa = np.random.rand(2, 4410).astype(np.float32) * 0.5
        mock_sample_rate = 44100

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', False):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
                with patch('matchering_player.utils.file_loader.librosa.load', return_value=(mock_audio_librosa, mock_sample_rate)):
                    audio_data, sample_rate = loader._load_raw_audio("/fake/test.mp3", ".mp3")

                    # Should transpose to (samples, channels)
                    assert audio_data.shape == (4410, 2)
                    assert sample_rate == mock_sample_rate

    def test_load_raw_audio_librosa_mono(self):
        """Test loading mono audio with librosa"""
        loader = AudioFileLoader()

        # Mock mono audio data
        mock_audio_mono = np.random.rand(4410).astype(np.float32) * 0.5
        mock_sample_rate = 44100

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', False):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
                with patch('matchering_player.utils.file_loader.librosa.load', return_value=(mock_audio_mono, mock_sample_rate)):
                    audio_data, sample_rate = loader._load_raw_audio("/fake/mono.mp3", ".mp3")

                    # Should reshape to (samples, 1)
                    assert audio_data.shape == (4410, 1)
                    assert sample_rate == mock_sample_rate

    def test_load_raw_audio_soundfile_permission_error(self):
        """Test soundfile permission error handling"""
        loader = AudioFileLoader()

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', False):
                # Mock soundfile LibsndfileError with system error
                class MockLibsndfileError(Exception):
                    pass

                with patch('matchering_player.utils.file_loader.sf.LibsndfileError', MockLibsndfileError):
                    with patch('matchering_player.utils.file_loader.sf.read', side_effect=MockLibsndfileError("System error")):
                        with pytest.raises(PermissionError):
                            loader._load_raw_audio("/fake/protected.wav", ".wav")

    def test_process_audio_mono_to_stereo(self):
        """Test converting mono audio to stereo"""
        loader = AudioFileLoader(target_sample_rate=44100, target_channels=2)

        # Mono audio
        mono_audio = np.random.rand(1000, 1).astype(np.float32) * 0.5

        processed = loader._process_audio(mono_audio, 44100)

        assert processed.shape == (1000, 2)
        # Both channels should be the same (mono to stereo)
        np.testing.assert_array_equal(processed[:, 0], processed[:, 1])

    def test_process_audio_stereo_to_mono(self):
        """Test converting stereo audio to mono"""
        loader = AudioFileLoader(target_sample_rate=44100, target_channels=1)

        # Stereo audio
        stereo_audio = np.random.rand(1000, 2).astype(np.float32) * 0.5

        processed = loader._process_audio(stereo_audio, 44100)

        assert processed.shape == (1000, 1)

    def test_process_audio_resampling(self):
        """Test audio resampling"""
        loader = AudioFileLoader(target_sample_rate=22050, target_channels=2)

        # 44100Hz stereo audio
        original_audio = np.random.rand(4410, 2).astype(np.float32) * 0.5  # 0.1s at 44100Hz

        with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
            with patch('matchering_player.utils.file_loader.librosa.resample') as mock_resample:
                # Mock resampling to return half the samples
                mock_resample.side_effect = lambda x, orig_sr, target_sr: x[::2] if target_sr < orig_sr else x

                processed = loader._process_audio(original_audio, 44100)

                # Should have been resampled
                assert processed.shape[0] < original_audio.shape[0]
                assert processed.shape[1] == 2

    def test_process_audio_no_resampling_needed(self):
        """Test audio processing when no resampling needed"""
        loader = AudioFileLoader(target_sample_rate=44100, target_channels=2)

        # Audio already at target format
        audio = np.random.rand(1000, 2).astype(np.float32) * 0.5

        processed = loader._process_audio(audio, 44100)

        # Should be unchanged
        np.testing.assert_array_equal(processed, audio)

    def test_process_audio_1d_input(self):
        """Test processing 1D audio input"""
        loader = AudioFileLoader(target_sample_rate=44100, target_channels=2)

        # 1D audio array
        audio_1d = np.random.rand(1000).astype(np.float32) * 0.5

        processed = loader._process_audio(audio_1d, 44100)

        # Should be reshaped to (samples, channels)
        assert processed.shape == (1000, 2)

    @pytest.mark.integration
    def test_complete_loading_workflow_soundfile(self):
        """Test complete audio loading workflow with soundfile"""
        loader = AudioFileLoader(target_sample_rate=48000, target_channels=2)

        # Mock complete workflow
        mock_audio = np.random.rand(2205, 2).astype(np.float32) * 0.3  # 0.05s at 44100Hz

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('os.path.exists', return_value=True):
                with patch('matchering_player.utils.file_loader.sf.read', return_value=(mock_audio, 44100)):
                    with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
                        with patch('matchering_player.utils.file_loader.librosa.resample') as mock_resample:
                            # Mock resampling behavior
                            def resample_func(audio, orig_sr, target_sr):
                                ratio = target_sr / orig_sr
                                new_length = int(len(audio) * ratio)
                                if new_length <= len(audio):
                                    return audio[:new_length]
                                else:
                                    # Handle different array dimensions
                                    if audio.ndim == 1:
                                        padding = ((0, new_length - len(audio)),)
                                    else:
                                        padding = ((0, new_length - len(audio)), (0, 0))
                                    return np.pad(audio, padding)

                            mock_resample.side_effect = resample_func

                            processed_audio, sample_rate = loader.load_audio_file("/fake/test.wav")

                            assert sample_rate == 48000
                            assert processed_audio.shape[1] == 2
                            assert processed_audio.dtype == np.float32

    @pytest.mark.integration
    def test_complete_loading_workflow_librosa(self):
        """Test complete audio loading workflow with librosa only"""
        loader = AudioFileLoader(target_sample_rate=44100, target_channels=1)

        # Mock stereo audio data (librosa format)
        mock_audio_librosa = np.random.rand(2, 4410).astype(np.float32) * 0.3

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', False):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
                with patch('os.path.exists', return_value=True):
                    with patch('matchering_player.utils.file_loader.librosa.load', return_value=(mock_audio_librosa, 44100)):
                        processed_audio, sample_rate = loader.load_audio_file("/fake/test.mp3")

                        assert sample_rate == 44100
                        assert processed_audio.shape[1] == 1  # Converted to mono
                        assert processed_audio.dtype == np.float32

    @pytest.mark.error
    def test_load_audio_error_handling(self):
        """Test error handling in audio loading"""
        loader = AudioFileLoader()

        # Test with both libraries failing
        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('matchering_player.utils.file_loader.HAS_LIBROSA', True):
                with patch('os.path.exists', return_value=True):
                    with patch('matchering_player.utils.file_loader.sf.read', side_effect=Exception("Soundfile error")):
                        with patch('matchering_player.utils.file_loader.librosa.load', side_effect=Exception("Librosa error")):
                            with pytest.raises(Exception, match="Librosa error"):
                                loader.load_audio_file("/fake/problematic.wav")

    @pytest.mark.edge_cases
    def test_edge_cases(self):
        """Test various edge cases"""
        loader = AudioFileLoader()

        # Empty filename
        with pytest.raises((FileNotFoundError, ValueError)):
            loader.get_file_info("")

        # Very long filename
        long_path = "/fake/" + "a" * 1000 + ".wav"
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                loader.get_file_info(long_path)

    def test_format_detection(self):
        """Test audio format detection"""
        loader = AudioFileLoader()

        # Test format classification
        assert ".wav" in loader.SOUNDFILE_FORMATS
        assert ".flac" in loader.SOUNDFILE_FORMATS
        assert ".mp3" in loader.LIBROSA_FORMATS
        assert ".m4a" in loader.LIBROSA_FORMATS

    def test_channel_conversion_edge_cases(self):
        """Test edge cases in channel conversion"""
        loader = AudioFileLoader(target_sample_rate=44100, target_channels=6)  # 5.1 surround

        # Stereo to 6-channel
        stereo_audio = np.random.rand(1000, 2).astype(np.float32) * 0.5

        processed = loader._process_audio(stereo_audio, 44100)

        # Should be converted to 6 channels
        assert processed.shape == (1000, 6)

    @pytest.mark.performance
    def test_loading_performance(self):
        """Test loading performance with reasonable-sized audio"""
        loader = AudioFileLoader()

        # Simulate loading 10 seconds of audio
        audio_duration = 1.0  # Keep test fast
        sample_rate = 44100
        samples = int(sample_rate * audio_duration)
        mock_audio = np.random.rand(samples, 2).astype(np.float32) * 0.3

        with patch('matchering_player.utils.file_loader.HAS_SOUNDFILE', True):
            with patch('os.path.exists', return_value=True):
                with patch('matchering_player.utils.file_loader.sf.read', return_value=(mock_audio, sample_rate)):

                    import time
                    start_time = time.perf_counter()

                    processed_audio, sr = loader.load_audio_file("/fake/performance_test.wav")

                    end_time = time.perf_counter()
                    loading_time = end_time - start_time

                    # Should load reasonably quickly
                    assert loading_time < 1.0  # Should take less than 1 second
                    assert processed_audio.shape[0] == samples
                    assert sr == sample_rate