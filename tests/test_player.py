"""
Tests for audio player.
"""

import pytest
import numpy as np
import soundfile as sf
import tempfile
import os
from src.core.player import Player, PlaybackState
from src.core.engine import AudioConfig, AudioProcessor

class TestProcessor(AudioProcessor):
    """Test processor that applies gain."""
    
    def __init__(self, gain: float = 1.0):
        self.gain = gain
        
    def process(self, buffer: np.ndarray) -> np.ndarray:
        return buffer * self.gain
        
    def reset(self):
        pass

@pytest.fixture
def temp_audio_file():
    """Create temporary audio file."""
    # Create test audio data (1 second of 440Hz sine wave)
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * 440 * t)
    
    # Convert to stereo
    audio_data = np.column_stack((audio_data, audio_data))
    
    # Create temporary file
    _, path = tempfile.mkstemp(suffix='.wav')
    sf.write(path, audio_data, sample_rate)
    
    yield path
    
    # Cleanup
    os.unlink(path)

@pytest.fixture
def player():
    """Create player instance."""
    return Player(AudioConfig(
        sample_rate=44100,
        channels=2,
        buffer_size=1024,
        format=np.float32
    ))

def test_player_initialization(player):
    """Test player initialization."""
    assert player.state == PlaybackState.STOPPED
    assert player.position == 0
    assert player.duration == 0
    assert player.device_manager is not None
    assert player.engine is not None

def test_file_loading(player, temp_audio_file):
    """Test audio file loading."""
    # Load file
    success = player.load_file(temp_audio_file)
    assert success
    assert player.state == PlaybackState.STOPPED
    assert player.position == 0
    assert player.duration > 0
    
    # Try loading non-existent file
    success = player.load_file("nonexistent.wav")
    assert not success
    assert player.state == PlaybackState.ERROR

def test_playback_control(player, temp_audio_file):
    """Test playback control."""
    # Load file
    player.load_file(temp_audio_file)
    
    # Play
    player.play()
    assert player.state == PlaybackState.PLAYING
    
    # Pause
    player.pause()
    assert player.state == PlaybackState.PAUSED
    position = player.position
    
    # Resume
    player.play()
    assert player.state == PlaybackState.PLAYING
    assert player.position >= position
    
    # Stop
    player.stop()
    assert player.state == PlaybackState.STOPPED
    assert player.position == 0

def test_seeking(player, temp_audio_file):
    """Test seeking."""
    # Load file
    player.load_file(temp_audio_file)
    
    # Seek to middle
    mid_point = player.duration / 2
    player.seek(mid_point)
    assert abs(player.position - mid_point) < 0.1
    
    # Try seeking past end
    player.seek(player.duration + 1)
    assert player.position == player.duration
    
    # Try seeking before start
    player.seek(-1)
    assert player.position == 0

def test_audio_processing(player, temp_audio_file):
    """Test audio processing."""
    # Load file
    player.load_file(temp_audio_file)
    
    # Add processor
    processor = TestProcessor(gain=0.5)
    player.add_processor(processor)
    
    # Play
    player.play()
    assert player.state == PlaybackState.PLAYING
    
    # Remove processor
    player.remove_processor(processor)
    
    # Stop
    player.stop()

def test_callbacks(player, temp_audio_file):
    """Test callback functions."""
    state_changes = []
    position_updates = []
    
    def state_callback(state):
        state_changes.append(state)
        
    def position_callback(position, duration):
        position_updates.append(position)
        
    # Set callbacks
    player.set_state_callback(state_callback)
    player.set_position_callback(position_callback)
    
    # Load and play file
    player.load_file(temp_audio_file)
    player.play()
    
    # Wait a bit
    import time
    time.sleep(0.1)
    
    # Stop
    player.stop()
    
    # Check callbacks
    assert PlaybackState.LOADING in state_changes
    assert PlaybackState.STOPPED in state_changes
    assert PlaybackState.PLAYING in state_changes
    assert len(position_updates) > 0

def test_device_change(player, temp_audio_file):
    """Test device change."""
    # Load file
    player.load_file(temp_audio_file)
    
    # Get devices
    devices = player.device_manager.get_devices()
    if len(devices) > 1:
        # Change to second device
        player.set_device(devices[1])
        assert player.device_manager.current_device == devices[1]
        
        # Play
        player.play()
        assert player.state == PlaybackState.PLAYING
        
        # Stop
        player.stop()