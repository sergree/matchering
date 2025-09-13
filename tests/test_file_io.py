"""
Tests for audio file loading and saving functionality
"""

import os
import pytest
import numpy as np
import soundfile as sf
import tempfile
import shutil
import subprocess
from pathlib import Path

from matchering.loader import load


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_audio():
    """Generate test audio data"""
    duration = 1.0  # second
    sample_rate = 44100
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Create stereo signal
    left = np.sin(2 * np.pi * 440 * t)
    right = np.sin(2 * np.pi * 880 * t)
    return np.column_stack([left, right]), sample_rate


class TestAudioLoading:
    """Test audio file loading functionality"""

    def test_wav_loading(self, test_audio, temp_dir):
        """Test loading WAV files"""
        audio, sr = test_audio
        file_path = os.path.join(temp_dir, "test.wav")
        
        # Save and load WAV file
        sf.write(file_path, audio, sr)
        loaded_audio, loaded_sr = load(file_path, "target", temp_dir)
        
        # Check properties
        assert loaded_sr == sr
        assert loaded_audio.shape == audio.shape
        
        # Allow for quantization differences
        assert np.allclose(loaded_audio, audio, atol=2/32768)

    @pytest.mark.skipif(shutil.which("ffmpeg") is None,
                       reason="ffmpeg not available")
    def test_mp3_loading(self, test_audio, temp_dir):
        """Test loading MP3 files (requires ffmpeg)"""
        audio, sr = test_audio
        wav_path = os.path.join(temp_dir, "test.wav")
        mp3_path = os.path.join(temp_dir, "test.mp3")
        
        # Create MP3 file using ffmpeg
        sf.write(wav_path, audio, sr)
        subprocess.run([
            "ffmpeg", "-y",
            "-i", wav_path,
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            mp3_path
        ], capture_output=True)
        
        # Load MP3
        loaded_audio, loaded_sr = load(mp3_path, "reference", temp_dir)
        
        # Check basic properties (MP3 is lossy, so don't check exact equality)
        assert loaded_sr == sr
        assert loaded_audio.shape[1] in (1, 2)  # Accept mono or stereo
        assert loaded_audio.shape[0] == int(sr)  # Should be 1 second
        assert np.max(np.abs(loaded_audio)) > 0

    def test_corrupt_file(self, temp_dir):
        """Test handling of corrupt audio files"""
        # Create corrupt file
        corrupt_path = os.path.join(temp_dir, "corrupt.wav")
        with open(corrupt_path, "wb") as f:
            f.write(b"Not a valid WAV file")
        
        with pytest.raises(Exception):
            load(corrupt_path, "target", temp_dir)

    def test_missing_file(self, temp_dir):
        """Test handling of missing files"""
        missing_path = os.path.join(temp_dir, "nonexistent.wav")
        
        with pytest.raises(Exception):
            load(missing_path, "reference", temp_dir)

    def test_mono_file(self, temp_dir):
        """Test loading mono files"""
        # Create mono file
        duration = 1.0
        sr = 44100
        t = np.linspace(0, duration, int(duration * sr))
        mono_audio = np.sin(2 * np.pi * 440 * t)
        
        file_path = os.path.join(temp_dir, "mono.wav")
        sf.write(file_path, mono_audio, sr)
        
        # Load mono file
        loaded_audio, loaded_sr = load(file_path, "target", temp_dir)
        
        # Should be 2D array with 1 or 2 channels
        assert loaded_audio.ndim == 2
        assert loaded_audio.shape[1] in (1, 2)
        assert loaded_sr == sr

    def test_different_sample_rates(self, temp_dir):
        """Test loading files with different sample rates"""
        durations = [1.0, 1.0]
        sample_rates = [44100, 48000]
        files = []
        
        for duration, sr in zip(durations, sample_rates):
            t = np.linspace(0, duration, int(duration * sr))
            audio = np.column_stack([
                np.sin(2 * np.pi * 440 * t),
                np.sin(2 * np.pi * 880 * t)
            ])
            
            file_path = os.path.join(temp_dir, f"test_{sr}.wav")
            sf.write(file_path, audio, sr)
            files.append(file_path)
        
        # Load files with different sample rates
        for file_path, expected_sr in zip(files, sample_rates):
            audio, sr = load(file_path, "target", temp_dir)
            assert sr == expected_sr
            assert audio.ndim == 2
            assert audio.shape[1] in (1, 2)