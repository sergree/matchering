"""
Tests for audio format handling.
"""

import pytest
import numpy as np
import os
import tempfile
from pathlib import Path
from src.formats.handler import (
    AudioFile, AudioFormatError, FormatFactory,
    MP3Format, FLACFormat, OggFormat
)

@pytest.fixture
def test_data():
    """Create test audio data."""
    # Create 1 second of 440Hz sine wave
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    mono = np.sin(2 * np.pi * 440 * t)
    return np.column_stack((mono, mono)), sample_rate  # Convert to stereo

@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    path = tempfile.mkdtemp()
    yield path
    try:
        import shutil
        shutil.rmtree(path)
    except:
        pass

def create_test_file(temp_dir: str, data: np.ndarray, sample_rate: int,
                    format: str = 'wav') -> str:
    """Create test audio file.
    
    Args:
        temp_dir: Temporary directory
        data: Audio data
        sample_rate: Sample rate
        format: Audio format
        
    Returns:
        Path to created file
    """
    import soundfile as sf
    path = os.path.join(temp_dir, f'test.{format}')
    sf.write(path, data, sample_rate)
    return path

def test_format_factory():
    """Test format factory."""
    # Check supported formats
    formats = FormatFactory.get_supported_formats()
    assert len(formats) > 0
    assert '.wav' in formats
    assert '.mp3' in formats
    assert '.flac' in formats
    
    # Test invalid format
    with pytest.raises(AudioFormatError):
        FormatFactory.create_handler('test.xyz')

def test_wav_format(test_data, temp_dir):
    """Test WAV format handling."""
    data, sample_rate = test_data
    path = create_test_file(temp_dir, data, sample_rate, 'wav')
    
    # Open file
    with AudioFile(path) as audio:
        # Check info
        assert audio.info.sample_rate == sample_rate
        assert audio.info.channels == 2
        assert audio.info.duration == 1.0
        
        # Read data
        read_data = audio.read()
        np.testing.assert_allclose(read_data, data, rtol=1e-7)
        
        # Test partial read
        part_data = audio.read(0.5, 0.1)  # Read 100ms at 500ms
        assert len(part_data) == int(0.1 * sample_rate)
        
        # Write data
        out_path = os.path.join(temp_dir, 'output.wav')
        audio.write(out_path, data)
        assert os.path.exists(out_path)

def test_mp3_format(test_data, temp_dir):
    """Test MP3 format handling."""
    data, sample_rate = test_data
    
    # Create MP3 file using ffmpeg
    import subprocess
    wav_path = create_test_file(temp_dir, data, sample_rate, 'wav')
    mp3_path = os.path.join(temp_dir, 'test.mp3')
    subprocess.run([
        'ffmpeg', '-y',
        '-i', wav_path,
        '-codec:a', 'libmp3lame',
        '-qscale:a', '2',
        mp3_path
    ], check=True)
    
    # Open file
    with AudioFile(mp3_path) as audio:
        # Check info
        assert audio.info.sample_rate == sample_rate
        assert audio.info.channels == 2
        assert abs(audio.info.duration - 1.0) < 0.1  # MP3 duration might be slightly off
        
        # Read data (allow some difference due to MP3 compression)
        read_data = audio.read()
        assert read_data.shape == data.shape
        
        # Write data
        out_path = os.path.join(temp_dir, 'output.mp3')
        audio.write(out_path, data)
        assert os.path.exists(out_path)

def test_flac_format(test_data, temp_dir):
    """Test FLAC format handling."""
    data, sample_rate = test_data
    path = create_test_file(temp_dir, data, sample_rate, 'flac')
    
    # Open file
    with AudioFile(path) as audio:
        # Check info
        assert audio.info.sample_rate == sample_rate
        assert audio.info.channels == 2
        assert audio.info.duration == 1.0
        
        # Read data
        read_data = audio.read()
        np.testing.assert_allclose(read_data, data, rtol=1e-7)
        
        # Write data
        out_path = os.path.join(temp_dir, 'output.flac')
        audio.write(out_path, data)
        assert os.path.exists(out_path)

def test_ogg_format(test_data, temp_dir):
    """Test Ogg format handling."""
    data, sample_rate = test_data
    path = create_test_file(temp_dir, data, sample_rate, 'ogg')
    
    # Open file
    with AudioFile(path) as audio:
        # Check info
        assert audio.info.sample_rate == sample_rate
        assert audio.info.channels == 2
        assert abs(audio.info.duration - 1.0) < 0.1  # OGG duration might be slightly off
        
        # Read data (allow some difference due to OGG compression)
        read_data = audio.read()
        assert read_data.shape == data.shape
        
        # Write data
        out_path = os.path.join(temp_dir, 'output.ogg')
        audio.write(out_path, data)
        assert os.path.exists(out_path)

def test_file_info(test_data, temp_dir):
    """Test audio file info."""
    data, sample_rate = test_data
    path = create_test_file(temp_dir, data, sample_rate, 'wav')
    
    # Get file info
    info = AudioFile(path).info
    
    # Check basic properties
    assert info.sample_rate == sample_rate
    assert info.channels == 2
    assert info.duration == 1.0
    assert info.format == '.wav'
    
    # Check string representation
    info_str = str(info)
    assert 'Audio File:' in info_str
    assert 'Sample Rate: 44100 Hz' in info_str
    assert 'Channels: 2' in info_str
    assert 'Duration: 1.00 seconds' in info_str

def test_metadata(test_data, temp_dir):
    """Test metadata handling."""
    data, sample_rate = test_data
    
    # Create FLAC file with metadata
    import soundfile as sf
    from mutagen.flac import FLAC
    path = os.path.join(temp_dir, 'test.flac')
    sf.write(path, data, sample_rate)
    
    flac = FLAC(path)
    flac['title'] = ['Test Track']
    flac['artist'] = ['Test Artist']
    flac['album'] = ['Test Album']
    flac.save()
    
    # Check metadata
    with AudioFile(path) as audio:
        assert 'title' in audio.info.metadata
        assert audio.info.metadata['title'] == ['Test Track']
        assert audio.info.metadata['artist'] == ['Test Artist']
        assert audio.info.metadata['album'] == ['Test Album']

def test_error_handling(temp_dir):
    """Test error handling."""
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        AudioFile('nonexistent.wav')
    
    # Test invalid format
    invalid_path = os.path.join(temp_dir, 'test.xyz')
    with open(invalid_path, 'w') as f:
        f.write('invalid data')
    with pytest.raises(AudioFormatError):
        AudioFile(invalid_path)
    
    # Test invalid audio data
    corrupt_path = os.path.join(temp_dir, 'corrupt.wav')
    with open(corrupt_path, 'wb') as f:
        f.write(b'RIFF1234WAVEfmt corrupt data')