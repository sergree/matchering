"""
Tests for core audio engine functionality.
"""

import pytest
import numpy as np
import asyncio
from src.core.engine import AudioConfig, AudioBuffer, AudioProcessor, AudioEngine

class TestProcessor(AudioProcessor):
    """Test processor that applies gain to audio."""
    
    def __init__(self, gain: float = 1.0):
        self.gain = gain
        
    def process(self, buffer: np.ndarray) -> np.ndarray:
        return buffer * self.gain
        
    def reset(self):
        pass

@pytest.fixture
def audio_config():
    """Create test audio configuration."""
    return AudioConfig(
        sample_rate=44100,
        channels=2,
        buffer_size=512,
        format=np.float32
    )

@pytest.fixture
def audio_buffer():
    """Create test audio buffer."""
    return AudioBuffer(1024, 2, np.float32)

@pytest.fixture
def audio_engine(audio_config):
    """Create test audio engine."""
    return AudioEngine(audio_config)

def test_audio_buffer_write_read():
    """Test basic buffer write/read operations."""
    buffer = AudioBuffer(1024, 2, np.float32)
    
    # Create test data
    test_data = np.ones((512, 2), dtype=np.float32)
    
    # Write data
    written = buffer.write(test_data)
    assert written == len(test_data)
    
    # Read data
    read_data = buffer.read(512)
    assert np.array_equal(read_data, test_data)
    
    # Check empty read
    empty_data = buffer.read(512)
    assert len(empty_data) == 0

def test_audio_buffer_reset():
    """Test buffer reset functionality."""
    buffer = AudioBuffer(1024, 2, np.float32)
    
    # Write some data
    test_data = np.ones((512, 2), dtype=np.float32)
    buffer.write(test_data)
    
    # Read some data
    buffer.read(256)
    
    # Reset buffer should clear all state
    buffer.reset()
    assert buffer.position == 0
    
    # Read after reset should return empty array
    read_data = buffer.read(512)
    assert len(read_data) == 0

@pytest.mark.asyncio
async def test_audio_engine_processing():
    """Test audio engine processing chain."""
    engine = AudioEngine(AudioConfig())
    
    # Add test processor
    processor = TestProcessor(gain=2.0)
    engine.add_processor(processor)
    
    # Start engine
    await engine.start()
    
    # Write test data
    test_data = np.ones((512, 2), dtype=np.float32)
    written = engine.write_input(test_data)
    assert written == len(test_data)
    
    # Small wait for processing
    await asyncio.sleep(0.01)
    
    # Read processed data
    output_data = engine.read_output(512)
    assert np.array_equal(output_data, test_data * 2.0)
    
    # Stop engine
    await engine.stop()

def test_audio_engine_processor_management():
    """Test adding/removing processors."""
    engine = AudioEngine(AudioConfig())
    
    # Add processors
    processor1 = TestProcessor(gain=2.0)
    processor2 = TestProcessor(gain=0.5)
    
    engine.add_processor(processor1)
    engine.add_processor(processor2)
    assert len(engine.processors) == 2
    
    # Remove processor
    engine.remove_processor(processor1)
    assert len(engine.processors) == 1
    assert engine.processors[0] == processor2

@pytest.mark.asyncio
async def test_audio_engine_reset():
    """Test engine reset functionality."""
    engine = AudioEngine(AudioConfig())
    
    # Add processor
    processor = TestProcessor(gain=2.0)
    engine.add_processor(processor)
    
    # Start engine
    await engine.start()
    
    # Write some data
    test_data = np.ones((512, 2), dtype=np.float32)
    engine.write_input(test_data)
    
    # Reset engine
    engine.reset()
    
    # Verify buffers are reset
    assert engine._input_buffer.position == 0
    assert engine._output_buffer.position == 0
    
    # Stop engine
    await engine.stop()