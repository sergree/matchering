#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Configuration and Utilities
Shared configuration, fixtures, and utilities for all test files
"""

import numpy as np
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any

@dataclass
class TestConfig:
    """Configuration for test runs"""
    # Audio settings
    default_sample_rate: int = 44100
    default_duration: float = 2.0
    default_amplitude: float = 0.5

    # Buffer settings
    default_buffer_size_ms: float = 100.0

    # Tolerance settings for numerical comparisons
    rms_tolerance: float = 0.01
    amplitude_tolerance: float = 0.001
    frequency_tolerance: float = 1.0  # Hz

    # Performance thresholds
    cpu_usage_excellent: float = 0.1    # 10%
    cpu_usage_good: float = 0.5         # 50%
    cpu_usage_acceptable: float = 1.0   # 100%

    # Test timeouts
    test_timeout_seconds: float = 30.0

    # Memory limits
    max_memory_mb: int = 1024  # 1GB

    # File format settings
    supported_sample_rates = [22050, 44100, 48000, 96000]
    supported_bit_depths = ["PCM_16", "PCM_24", "FLOAT"]

class AudioTestData:
    """Generator for various types of test audio"""

    @staticmethod
    def sine_wave(duration: float = 2.0,
                  sample_rate: int = 44100,
                  frequency: float = 440.0,
                  amplitude: float = 0.5,
                  stereo: bool = True) -> Tuple[np.ndarray, int]:
        """Generate a sine wave test signal"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)

        left = np.sin(2 * np.pi * frequency * t) * amplitude

        if stereo:
            # Slightly different frequency for right channel
            right = np.sin(2 * np.pi * frequency * t * 1.01) * amplitude * 0.9
            audio = np.column_stack([left, right])
        else:
            audio = left[:, np.newaxis]

        return audio.astype(np.float32), sample_rate

    @staticmethod
    def white_noise(duration: float = 2.0,
                   sample_rate: int = 44100,
                   amplitude: float = 0.5,
                   stereo: bool = True) -> Tuple[np.ndarray, int]:
        """Generate white noise test signal"""
        samples = int(duration * sample_rate)

        if stereo:
            audio = np.random.normal(0, amplitude, (samples, 2))
        else:
            audio = np.random.normal(0, amplitude, (samples, 1))

        return audio.astype(np.float32), sample_rate

    @staticmethod
    def sweep(duration: float = 2.0,
              sample_rate: int = 44100,
              start_freq: float = 20.0,
              end_freq: float = 20000.0,
              amplitude: float = 0.5,
              stereo: bool = True) -> Tuple[np.ndarray, int]:
        """Generate a frequency sweep test signal"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)

        # Logarithmic frequency sweep
        freq = start_freq * (end_freq / start_freq) ** (t / duration)
        phase = 2 * np.pi * np.cumsum(freq) / sample_rate

        left = np.sin(phase) * amplitude

        if stereo:
            # Slightly different sweep for right channel
            right_freq = freq * 1.01
            right_phase = 2 * np.pi * np.cumsum(right_freq) / sample_rate
            right = np.sin(right_phase) * amplitude * 0.9
            audio = np.column_stack([left, right])
        else:
            audio = left[:, np.newaxis]

        return audio.astype(np.float32), sample_rate

    @staticmethod
    def impulse(duration: float = 2.0,
                sample_rate: int = 44100,
                amplitude: float = 1.0,
                stereo: bool = True) -> Tuple[np.ndarray, int]:
        """Generate an impulse test signal"""
        samples = int(duration * sample_rate)

        if stereo:
            audio = np.zeros((samples, 2), dtype=np.float32)
            audio[0, :] = amplitude
        else:
            audio = np.zeros((samples, 1), dtype=np.float32)
            audio[0, 0] = amplitude

        return audio, sample_rate

    @staticmethod
    def multi_tone(duration: float = 2.0,
                   sample_rate: int = 44100,
                   frequencies: list = None,
                   amplitudes: list = None,
                   stereo: bool = True) -> Tuple[np.ndarray, int]:
        """Generate a multi-tone test signal"""
        if frequencies is None:
            frequencies = [220, 440, 880, 1760]  # Musical intervals
        if amplitudes is None:
            amplitudes = [0.25] * len(frequencies)  # Equal amplitudes

        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)

        left = np.zeros(samples)
        for freq, amp in zip(frequencies, amplitudes):
            left += np.sin(2 * np.pi * freq * t) * amp

        if stereo:
            # Slightly different mix for right channel
            right = np.zeros(samples)
            for i, (freq, amp) in enumerate(zip(frequencies, amplitudes)):
                # Vary the phase and amplitude slightly per frequency
                phase_shift = i * np.pi / 4
                amp_factor = 0.8 + 0.2 * (i % 2)
                right += np.sin(2 * np.pi * freq * t + phase_shift) * amp * amp_factor

            audio = np.column_stack([left, right])
        else:
            audio = left[:, np.newaxis]

        return audio.astype(np.float32), sample_rate

class TestFixtures:
    """Pre-generated test fixtures and utilities"""

    def __init__(self, config: TestConfig = None):
        self.config = config or TestConfig()
        self._temp_dir = None

    def get_temp_dir(self) -> Path:
        """Get or create temporary directory for test files"""
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="matchering_test_")
        return Path(self._temp_dir)

    def create_test_files(self) -> Dict[str, str]:
        """Create a set of standard test audio files"""
        try:
            import soundfile as sf
        except ImportError:
            return {}

        temp_dir = self.get_temp_dir()
        test_files = {}

        # Standard test files
        test_definitions = [
            ("quiet_mono.wav", AudioTestData.sine_wave(2.0, 44100, 440, 0.1, False)),
            ("quiet_stereo.wav", AudioTestData.sine_wave(2.0, 44100, 440, 0.1, True)),
            ("loud_mono.wav", AudioTestData.sine_wave(2.0, 44100, 440, 0.8, False)),
            ("loud_stereo.wav", AudioTestData.sine_wave(2.0, 44100, 440, 0.8, True)),
            ("bass_heavy.wav", AudioTestData.sine_wave(2.0, 44100, 80, 0.6, True)),
            ("treble_heavy.wav", AudioTestData.sine_wave(2.0, 44100, 4000, 0.6, True)),
            ("white_noise.wav", AudioTestData.white_noise(2.0, 44100, 0.3, True)),
            ("frequency_sweep.wav", AudioTestData.sweep(3.0, 44100, 20, 20000, 0.4, True)),
            ("impulse.wav", AudioTestData.impulse(1.0, 44100, 0.8, True)),
            ("multi_tone.wav", AudioTestData.multi_tone(2.0, 44100, stereo=True)),
        ]

        for filename, (audio, sample_rate) in test_definitions:
            filepath = temp_dir / filename
            try:
                sf.write(filepath, audio, sample_rate)
                test_files[filename] = str(filepath)
            except Exception as e:
                print(f"Failed to create {filename}: {e}")

        return test_files

    def cleanup(self):
        """Clean up temporary files"""
        if self._temp_dir:
            import shutil
            try:
                shutil.rmtree(self._temp_dir)
                self._temp_dir = None
            except Exception as e:
                print(f"Warning: Could not clean up temp directory: {e}")

class TestUtils:
    """Utility functions for testing"""

    @staticmethod
    def assert_audio_equal(audio1: np.ndarray,
                          audio2: np.ndarray,
                          tolerance: float = 1e-6,
                          message: str = "Audio arrays should be equal"):
        """Assert that two audio arrays are approximately equal"""
        assert audio1.shape == audio2.shape, f"{message}: Shape mismatch {audio1.shape} != {audio2.shape}"

        max_diff = np.max(np.abs(audio1 - audio2))
        assert max_diff <= tolerance, f"{message}: Max difference {max_diff} > tolerance {tolerance}"

    @staticmethod
    def assert_rms_similar(audio1: np.ndarray,
                          audio2: np.ndarray,
                          tolerance: float = 0.01,
                          message: str = "RMS levels should be similar"):
        """Assert that two audio arrays have similar RMS levels"""
        rms1 = np.sqrt(np.mean(audio1**2))
        rms2 = np.sqrt(np.mean(audio2**2))

        diff = abs(rms1 - rms2)
        max_rms = max(rms1, rms2)
        relative_diff = diff / max_rms if max_rms > 0 else diff

        assert relative_diff <= tolerance, f"{message}: RMS difference {relative_diff:.6f} > tolerance {tolerance}"

    @staticmethod
    def measure_performance(func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure the performance of a function call"""
        import time

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        duration = end_time - start_time
        return result, duration

    @staticmethod
    def check_cpu_usage(duration: float, real_time: float, config: TestConfig = None) -> str:
        """Categorize CPU usage performance"""
        if config is None:
            config = TestConfig()

        cpu_ratio = duration / real_time

        if cpu_ratio <= config.cpu_usage_excellent:
            return "excellent"
        elif cpu_ratio <= config.cpu_usage_good:
            return "good"
        elif cpu_ratio <= config.cpu_usage_acceptable:
            return "acceptable"
        else:
            return "poor"

    @staticmethod
    def format_audio_info(audio: np.ndarray, sample_rate: int) -> str:
        """Format audio information for display"""
        if len(audio.shape) == 1:
            channels = "mono"
            shape_str = f"{len(audio)}"
        else:
            channels = f"{audio.shape[1]}ch"
            shape_str = f"{audio.shape[0]}x{audio.shape[1]}"

        duration = len(audio) / sample_rate
        rms = np.sqrt(np.mean(audio**2))
        peak = np.max(np.abs(audio))

        return f"{shape_str} ({channels}), {duration:.2f}s, {sample_rate}Hz, RMS:{rms:.4f}, Peak:{peak:.4f}"

# Global test configuration instance
TEST_CONFIG = TestConfig()

# Global test fixtures instance
TEST_FIXTURES = TestFixtures(TEST_CONFIG)

# Example usage functions
def get_test_audio_simple(duration=2.0, sample_rate=44100):
    """Quick function to get simple test audio for basic tests"""
    return AudioTestData.sine_wave(duration, sample_rate)

def get_test_audio_pair():
    """Get a pair of test audio (quiet target, loud reference) for matching tests"""
    target, sr = AudioTestData.sine_wave(2.0, 44100, 440, 0.1, True)  # Quiet
    reference, _ = AudioTestData.sine_wave(2.0, 44100, 440, 0.8, True)  # Loud
    return target, reference, sr

if __name__ == "__main__":
    # Demonstrate test configuration usage
    print("🧪 Matchering Test Configuration")
    print("=" * 50)

    config = TestConfig()
    print(f"Default sample rate: {config.default_sample_rate}")
    print(f"Default buffer size: {config.default_buffer_size_ms}ms")
    print(f"RMS tolerance: {config.rms_tolerance}")

    print(f"\nSupported sample rates: {config.supported_sample_rates}")
    print(f"Supported bit depths: {config.supported_bit_depths}")

    # Demonstrate audio generation
    print(f"\n🎵 Test Audio Generation:")
    sine_audio, sr = AudioTestData.sine_wave(1.0, 44100, 440, 0.5)
    print(f"Sine wave: {TestUtils.format_audio_info(sine_audio, sr)}")

    noise_audio, sr = AudioTestData.white_noise(1.0, 44100, 0.3)
    print(f"White noise: {TestUtils.format_audio_info(noise_audio, sr)}")

    sweep_audio, sr = AudioTestData.sweep(2.0, 44100, 20, 20000, 0.4)
    print(f"Frequency sweep: {TestUtils.format_audio_info(sweep_audio, sr)}")

    print("\n✅ Test configuration ready for use!")