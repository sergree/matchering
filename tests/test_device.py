"""
Tests for audio device management.
"""

import pytest
import numpy as np
import sounddevice as sd
from src.core.device import DeviceManager
from src.core.engine import AudioConfig

@pytest.fixture
def device_manager():
    """Create device manager instance."""
    return DeviceManager()

@pytest.fixture
def audio_config():
    """Create audio configuration."""
    return AudioConfig(
        sample_rate=44100,
        channels=2,
        buffer_size=1024,
        format=np.float32
    )

def test_device_enumeration(device_manager):
    """Test device enumeration."""
    devices = device_manager.get_devices()
    assert len(devices) > 0
    
    # Check default device
    default = device_manager.get_default_device()
    assert default is not None
    assert default in devices
    
    # Verify device info
    for device in devices:
        assert device.id >= 0
        assert device.name
        assert device.max_output_channels >= 0
        assert len(device.supported_sample_rates) > 0
        assert device.output_latency[0] >= 0
        assert device.output_latency[1] >= device.output_latency[0]

def test_stream_management(device_manager, audio_config):
    """Test stream management."""
    # Initially no device selected
    assert device_manager.current_device is None
    
    # Open stream
    device_manager.open_output_stream(audio_config)
    assert device_manager.current_device is not None
    assert device_manager.get_buffer_size() > 0
    
    # Write some data
    data = np.zeros((1024, 2), dtype=np.float32)
    written = device_manager.write(data)
    assert written == len(data)
    
    # Check latency
    latency = device_manager.get_output_latency()
    assert latency >= 0
    
    # Close stream
    device_manager.close()
    assert device_manager.current_device is None
    assert device_manager.get_buffer_size() == 0

def test_buffer_underrun(device_manager, audio_config):
    """Test buffer underrun handling."""
    device_manager.open_output_stream(audio_config)
    
    # Write less data than buffer size
    data = np.zeros((512, 2), dtype=np.float32)
    written = device_manager.write(data)
    assert written == len(data)
    
    # Buffer should pad with silence
    device_manager.close()

def test_device_selection(device_manager, audio_config):
    """Test device selection."""
    devices = device_manager.get_devices()
    if len(devices) > 1:
        # Try to open stream with specific device
        device = devices[1]  # Use second device if available
        device_manager.open_output_stream(audio_config, device)
        assert device_manager.current_device == device
        device_manager.close()

def test_sample_rate_support(device_manager):
    """Test sample rate support detection."""
    device = device_manager.get_default_device()
    assert device is not None
    
    # Common rates should be supported
    assert 44100 in device.supported_sample_rates
    assert 48000 in device.supported_sample_rates