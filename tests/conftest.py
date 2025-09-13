"""
Pytest configuration and shared fixtures for Matchering tests
"""

import pytest
import numpy as np
import sys
import os
from pathlib import Path
import tempfile
from typing import Dict, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Check for optional dependencies
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    import matchering
    HAS_MATCHERING = True
except ImportError:
    HAS_MATCHERING = False

try:
    from matchering_player.core.config import PlayerConfig
    HAS_PLAYER = True
except ImportError:
    HAS_PLAYER = False

# Pytest fixtures

@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for the test session"""
    with tempfile.TemporaryDirectory(prefix="matchering_test_") as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_rates():
    """Standard sample rates for testing"""
    return [22050, 44100, 48000, 96000]

@pytest.fixture
def bit_depths():
    """Standard bit depths for testing"""
    return ["PCM_16", "PCM_24", "FLOAT"]

@pytest.fixture
def test_config():
    """Default test configuration"""
    if not HAS_PLAYER:
        pytest.skip("Matchering player not available")
    return PlayerConfig(
        buffer_size_ms=100.0,
        enable_level_matching=True,
        enable_frequency_matching=False,
        enable_stereo_width=False
    )

@pytest.fixture
def full_config():
    """Full-featured test configuration"""
    if not HAS_PLAYER:
        pytest.skip("Matchering player not available")
    return PlayerConfig(
        buffer_size_ms=100.0,
        enable_level_matching=True,
        enable_frequency_matching=True,
        enable_stereo_width=True
    )

@pytest.fixture
def sine_wave():
    """Generate a simple sine wave for testing"""
    def _sine_wave(duration=1.0, sample_rate=44100, frequency=440.0, amplitude=0.5, stereo=True):
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)

        left = np.sin(2 * np.pi * frequency * t) * amplitude

        if stereo:
            right = np.sin(2 * np.pi * frequency * t * 1.01) * amplitude * 0.9
            audio = np.column_stack([left, right])
        else:
            audio = left[:, np.newaxis]

        return audio.astype(np.float32), sample_rate
    return _sine_wave

@pytest.fixture
def white_noise():
    """Generate white noise for testing"""
    def _white_noise(duration=1.0, sample_rate=44100, amplitude=0.3, stereo=True):
        samples = int(duration * sample_rate)

        if stereo:
            audio = np.random.normal(0, amplitude, (samples, 2))
        else:
            audio = np.random.normal(0, amplitude, (samples, 1))

        return audio.astype(np.float32), sample_rate
    return _white_noise

@pytest.fixture
def test_audio_files(temp_dir):
    """Create standard test audio files"""
    if not HAS_SOUNDFILE:
        pytest.skip("soundfile not available")

    def create_test_audio(duration, sr, freq, amplitude, characteristics="normal"):
        samples = int(duration * sr)
        t = np.linspace(0, duration, samples)

        if characteristics == "quiet":
            left = np.sin(2 * np.pi * freq * t) * amplitude * 0.2
            right = left * 0.95
        elif characteristics == "loud":
            left = np.tanh(np.sin(2 * np.pi * freq * t) * amplitude * 3) * 0.9
            right = left * 0.98
        elif characteristics == "bass_heavy":
            left = (np.sin(2 * np.pi * freq * t) * amplitude * 0.3 +
                   np.sin(2 * np.pi * (freq/4) * t) * amplitude * 0.7)
            right = left * 0.9
        elif characteristics == "treble_heavy":
            left = (np.sin(2 * np.pi * freq * t) * amplitude * 0.3 +
                   np.sin(2 * np.pi * (freq*4) * t) * amplitude * 0.7)
            right = left * 0.85
        else:  # normal
            left = np.sin(2 * np.pi * freq * t) * amplitude
            right = np.sin(2 * np.pi * freq * t * 1.01) * amplitude * 0.9

        return np.column_stack([left, right]).astype(np.float32)

    # Create test files
    test_files = {}
    test_configs = [
        ("quiet_target.wav", 3.0, 44100, 440, 0.1, "quiet"),
        ("loud_reference.wav", 3.0, 44100, 440, 0.8, "loud"),
        ("bass_heavy.wav", 3.0, 44100, 220, 0.4, "bass_heavy"),
        ("treble_heavy.wav", 3.0, 44100, 880, 0.6, "treble_heavy"),
        ("short_audio.wav", 0.5, 44100, 440, 0.3, "normal"),
        ("long_audio.wav", 10.0, 44100, 440, 0.7, "normal"),
        ("hires_audio.wav", 2.0, 48000, 440, 0.4, "normal"),
    ]

    for name, duration, sr, freq, amp, char in test_configs:
        audio = create_test_audio(duration, sr, freq, amp, char)
        filepath = temp_dir / name
        sf.write(filepath, audio, sr)
        test_files[name] = str(filepath)

    return test_files

@pytest.fixture
def audio_pair():
    """Generate a pair of test audio (quiet target, loud reference)"""
    def create_audio(duration, sr, freq, amplitude):
        samples = int(duration * sr)
        t = np.linspace(0, duration, samples)
        left = np.sin(2 * np.pi * freq * t) * amplitude
        right = np.sin(2 * np.pi * freq * t * 1.01) * amplitude * 0.9
        return np.column_stack([left, right]).astype(np.float32)

    target = create_audio(2.0, 44100, 440, 0.1)  # Quiet
    reference = create_audio(2.0, 44100, 440, 0.8)  # Loud

    return target, reference, 44100

# Pytest hooks and markers

def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests across components")
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")
    config.addinivalue_line("markers", "audio: Tests that require audio processing")
    config.addinivalue_line("markers", "files: Tests that require file I/O")
    config.addinivalue_line("markers", "player: Tests for the matchering player")
    config.addinivalue_line("markers", "core: Tests for the core matchering library")
    config.addinivalue_line("markers", "dsp: Tests for DSP functionality")
    config.addinivalue_line("markers", "performance: Performance and benchmark tests")
    config.addinivalue_line("markers", "regression: Regression tests")
    config.addinivalue_line("markers", "error: Error handling and edge case tests")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location and name"""
    for item in items:
        # Add markers based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add markers based on test name patterns
        if "performance" in item.name or "benchmark" in item.name:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        if "error" in item.name or "invalid" in item.name or "edge" in item.name:
            item.add_marker(pytest.mark.error)

        if "player" in item.name:
            item.add_marker(pytest.mark.player)

        if "dsp" in item.name:
            item.add_marker(pytest.mark.dsp)

        if "audio" in item.name or "sound" in item.name:
            item.add_marker(pytest.mark.audio)

        if "file" in item.name or "load" in item.name or "save" in item.name:
            item.add_marker(pytest.mark.files)

def pytest_runtest_setup(item):
    """Setup hook called before each test"""
    # Skip tests that require dependencies that aren't available
    markers = [mark.name for mark in item.iter_markers()]

    if "files" in markers and not HAS_SOUNDFILE:
        pytest.skip("soundfile not available")

    if "player" in markers and not HAS_PLAYER:
        pytest.skip("matchering player not available")

    if "core" in markers and not HAS_MATCHERING:
        pytest.skip("matchering core library not available")

# Utility functions for tests

def assert_audio_equal(audio1: np.ndarray, audio2: np.ndarray, tolerance=1e-6):
    """Assert that two audio arrays are approximately equal"""
    assert audio1.shape == audio2.shape, f"Shape mismatch: {audio1.shape} != {audio2.shape}"
    max_diff = np.max(np.abs(audio1 - audio2))
    assert max_diff <= tolerance, f"Max difference {max_diff} > tolerance {tolerance}"

def assert_rms_similar(audio1: np.ndarray, audio2: np.ndarray, tolerance=0.01):
    """Assert that two audio arrays have similar RMS levels"""
    rms1 = np.sqrt(np.mean(audio1**2))
    rms2 = np.sqrt(np.mean(audio2**2))

    diff = abs(rms1 - rms2)
    max_rms = max(rms1, rms2)
    relative_diff = diff / max_rms if max_rms > 0 else diff

    assert relative_diff <= tolerance, f"RMS difference {relative_diff:.6f} > tolerance {tolerance}"

# Export utility functions for use in tests
__all__ = [
    'HAS_SOUNDFILE',
    'HAS_MATCHERING',
    'HAS_PLAYER',
    'assert_audio_equal',
    'assert_rms_similar'
]