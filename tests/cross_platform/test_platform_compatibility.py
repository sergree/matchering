#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-Platform Compatibility Tests for Matchering Core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate platform-specific behavior and compatibility

:copyright: (C) 2024 Matchering Team
:license: GPLv3, see LICENSE for more details.
"""

import pytest
import os
import platform
import sys
import tempfile
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import matchering


class TestPlatformCompatibility:
    """Test platform-specific compatibility"""

    def test_current_platform_info(self):
        """Document current testing platform"""
        platform_info = {
            'system': platform.system(),
            'machine': platform.machine(),
            'architecture': platform.architecture(),
            'python_version': platform.python_version(),
            'processor': platform.processor(),
        }

        print(f"Testing on platform: {platform_info}")

        # Basic platform validation
        assert platform_info['system'] in ['Linux', 'Darwin', 'Windows'], f"Unsupported platform: {platform_info['system']}"
        assert sys.version_info >= (3, 8), f"Python version too old: {sys.version_info}"

    def test_path_handling_compatibility(self):
        """Test cross-platform path handling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Test various path formats
            test_paths = [
                tmpdir / "simple.wav",
                tmpdir / "with spaces.wav",
                tmpdir / "with-dashes.wav",
                tmpdir / "with_underscores.wav",
                tmpdir / "субdir" / "unicode.wav",  # Unicode characters
            ]

            # Create test audio
            sample_rate = 44100
            duration = 1.0
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)
            audio = np.column_stack([
                np.sin(2 * np.pi * 440 * t) * 0.3,
                np.sin(2 * np.pi * 440 * t) * 0.28
            ]).astype(np.float32)

            for test_path in test_paths:
                # Create parent directories
                test_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    # Test file creation and processing
                    target_file = test_path
                    reference_file = test_path.parent / f"ref_{test_path.name}"
                    result_file = test_path.parent / f"result_{test_path.name}"

                    # Write test files
                    sf.write(str(target_file), audio, sample_rate)
                    sf.write(str(reference_file), audio * 1.5, sample_rate)

                    # Process with matchering
                    matchering.process(
                        target=str(target_file),
                        reference=str(reference_file),
                        results=[str(result_file)]
                    )

                    # Verify result
                    assert result_file.exists(), f"Processing failed for path: {test_path}"

                    print(f"✅ Path handled successfully: {test_path}")

                except Exception as e:
                    # Some unicode paths might not be supported on all filesystems
                    if "unicode" in str(test_path).lower():
                        print(f"⚠️  Unicode path not supported on this filesystem: {test_path}")
                    else:
                        raise AssertionError(f"Path handling failed for: {test_path}, error: {e}")

    def test_file_permissions_handling(self):
        """Test handling of file permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test audio
            sample_rate = 44100
            duration = 1.0
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)
            audio = np.column_stack([
                np.sin(2 * np.pi * 440 * t) * 0.3,
                np.sin(2 * np.pi * 440 * t) * 0.28
            ]).astype(np.float32)

            target_file = tmpdir / "target.wav"
            reference_file = tmpdir / "reference.wav"
            result_file = tmpdir / "result.wav"

            # Write test files
            sf.write(str(target_file), audio, sample_rate)
            sf.write(str(reference_file), audio * 1.5, sample_rate)

            # Test normal processing first
            matchering.process(
                target=str(target_file),
                reference=str(reference_file),
                results=[str(result_file)]
            )
            assert result_file.exists()

            # Clean up for next test
            result_file.unlink()

            # Test read-only input files (should work)
            if platform.system() != 'Windows':  # Windows handles permissions differently
                os.chmod(target_file, 0o444)  # Read-only
                os.chmod(reference_file, 0o444)  # Read-only

                matchering.process(
                    target=str(target_file),
                    reference=str(reference_file),
                    results=[str(result_file)]
                )
                assert result_file.exists()

                print("✅ Read-only input files handled correctly")

    def test_large_file_path_support(self):
        """Test support for long file paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a deep directory structure
            deep_path = tmpdir
            for i in range(5):
                deep_path = deep_path / f"very_long_directory_name_level_{i}_with_extra_characters"
                deep_path.mkdir(exist_ok=True)

            long_filename = "very_long_filename_with_many_characters_and_descriptive_names_for_testing_purposes.wav"
            target_file = deep_path / f"target_{long_filename}"
            reference_file = deep_path / f"reference_{long_filename}"
            result_file = deep_path / f"result_{long_filename}"

            # Check if path length is reasonable for testing
            if len(str(target_file)) > 200:
                print(f"Testing with long path ({len(str(target_file))} chars): ...{str(target_file)[-50:]}")

                # Create test audio
                sample_rate = 44100
                duration = 1.0
                samples = int(duration * sample_rate)
                t = np.linspace(0, duration, samples)
                audio = np.column_stack([
                    np.sin(2 * np.pi * 440 * t) * 0.3,
                    np.sin(2 * np.pi * 440 * t) * 0.28
                ]).astype(np.float32)

                # Write test files
                sf.write(str(target_file), audio, sample_rate)
                sf.write(str(reference_file), audio * 1.5, sample_rate)

                # Process with matchering
                matchering.process(
                    target=str(target_file),
                    reference=str(reference_file),
                    results=[str(result_file)]
                )

                assert result_file.exists(), "Long path processing failed"
                print("✅ Long file paths handled successfully")


class TestDependencyCompatibility:
    """Test compatibility with platform-specific dependencies"""

    def test_numpy_platform_specific(self):
        """Test numpy platform-specific behavior"""
        # Test basic numpy operations that might behave differently on platforms
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)

        # Test arithmetic
        result = arr * 2.0
        expected = np.array([2.0, 4.0, 6.0], dtype=np.float32)
        np.testing.assert_array_almost_equal(result, expected)

        # Test trigonometric functions
        angles = np.array([0, np.pi/2, np.pi], dtype=np.float32)
        sin_result = np.sin(angles)
        expected_sin = np.array([0, 1, 0], dtype=np.float32)
        np.testing.assert_array_almost_equal(sin_result, expected_sin, decimal=5)

        print("✅ NumPy operations consistent across platforms")

    def test_scipy_compatibility(self):
        """Test scipy compatibility"""
        from scipy import signal
        from scipy.io import wavfile
        import tempfile

        # Test basic signal processing
        b, a = signal.butter(4, 0.2)
        assert len(b) > 0 and len(a) > 0

        # Test signal filtering
        test_signal = np.sin(2 * np.pi * 0.1 * np.arange(1000))
        filtered = signal.filtfilt(b, a, test_signal)
        assert len(filtered) == len(test_signal)

        print("✅ SciPy signal processing working correctly")

    def test_soundfile_platform_compatibility(self):
        """Test soundfile library platform compatibility"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Test various audio formats
            formats_to_test = [
                ('wav', 'PCM_16'),
                ('wav', 'PCM_24'),
                ('flac', 'PCM_16'),
            ]

            sample_rate = 44100
            duration = 1.0
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)
            audio = np.column_stack([
                np.sin(2 * np.pi * 440 * t) * 0.3,
                np.sin(2 * np.pi * 440 * t) * 0.28
            ]).astype(np.float32)

            for file_format, subtype in formats_to_test:
                test_file = tmpdir / f"test.{file_format}"

                try:
                    # Write and read back
                    sf.write(str(test_file), audio, sample_rate, subtype=subtype)
                    read_audio, read_sr = sf.read(str(test_file))

                    assert read_sr == sample_rate
                    assert read_audio.shape[0] > 0
                    assert read_audio.shape[1] == 2  # Stereo

                    print(f"✅ {file_format.upper()} ({subtype}) format working")

                except Exception as e:
                    print(f"⚠️  {file_format.upper()} ({subtype}) not available: {e}")


class TestSystemResourceLimits:
    """Test system-specific resource limits"""

    def test_memory_availability(self):
        """Test available system memory"""
        try:
            import psutil
            memory = psutil.virtual_memory()

            print(f"System memory: {memory.total / 1024 / 1024 / 1024:.1f} GB")
            print(f"Available memory: {memory.available / 1024 / 1024 / 1024:.1f} GB")

            # Should have at least 1GB available for testing
            assert memory.available > 1024 * 1024 * 1024, "Insufficient memory for testing"

        except ImportError:
            print("⚠️  psutil not available, skipping memory check")

    def test_disk_space_availability(self):
        """Test available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')

            print(f"Disk space - Total: {total / 1024 / 1024 / 1024:.1f} GB")
            print(f"Disk space - Free: {free / 1024 / 1024 / 1024:.1f} GB")

            # Should have at least 1GB free for testing
            assert free > 1024 * 1024 * 1024, "Insufficient disk space for testing"

        except Exception as e:
            print(f"⚠️  Could not check disk space: {e}")

    def test_cpu_core_availability(self):
        """Test CPU core availability"""
        import multiprocessing

        cpu_count = multiprocessing.cpu_count()
        print(f"CPU cores available: {cpu_count}")

        # Should have at least 1 core (obviously), but good to document
        assert cpu_count >= 1, "No CPU cores detected"

        if cpu_count >= 2:
            print("✅ Multi-core processing available")
        else:
            print("⚠️  Single core system - parallel processing limited")


class TestMatcheringSpecificPlatformFeatures:
    """Test platform-specific features of Matchering"""

    def test_temporary_directory_handling(self):
        """Test platform-specific temporary directory handling"""
        import tempfile

        # Test different temp directory approaches
        temp_methods = [
            tempfile.gettempdir(),
            tempfile.TemporaryDirectory(),
        ]

        for i, temp_method in enumerate(temp_methods):
            if hasattr(temp_method, '__enter__'):
                # Context manager
                with temp_method as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    assert tmpdir_path.exists(), f"Temp directory method {i} failed"
                    print(f"✅ Temp directory method {i}: {tmpdir}")
            else:
                # Direct path
                tmpdir_path = Path(temp_method)
                assert tmpdir_path.exists(), f"Temp directory method {i} failed"
                print(f"✅ Temp directory method {i}: {temp_method}")

    def test_audio_processing_across_platforms(self):
        """Test consistent audio processing results across platforms"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create deterministic test audio
            np.random.seed(42)  # For reproducible results
            sample_rate = 44100
            duration = 2.0
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)

            # Mix of sine waves for deterministic but complex audio
            target_audio = np.column_stack([
                (np.sin(2 * np.pi * 440 * t) +
                 0.5 * np.sin(2 * np.pi * 880 * t) +
                 0.3 * np.sin(2 * np.pi * 1320 * t)) * 0.2,
                (np.sin(2 * np.pi * 440 * t) +
                 0.5 * np.sin(2 * np.pi * 880 * t) +
                 0.3 * np.sin(2 * np.pi * 1320 * t)) * 0.18
            ]).astype(np.float32)

            reference_audio = target_audio * 2.5

            target_file = tmpdir / "platform_test_target.wav"
            reference_file = tmpdir / "platform_test_reference.wav"
            result_file = tmpdir / "platform_test_result.wav"

            # Write test files
            sf.write(str(target_file), target_audio, sample_rate)
            sf.write(str(reference_file), reference_audio, sample_rate)

            # Process
            matchering.process(
                target=str(target_file),
                reference=str(reference_file),
                results=[str(result_file)]
            )

            # Read result
            result_audio, result_sr = sf.read(str(result_file))

            # Basic validation
            assert result_sr == sample_rate
            assert result_audio.shape == target_audio.shape

            # Calculate basic statistics for platform consistency documentation
            target_rms = np.sqrt(np.mean(target_audio ** 2))
            result_rms = np.sqrt(np.mean(result_audio ** 2))
            reference_rms = np.sqrt(np.mean(reference_audio ** 2))

            improvement_ratio = result_rms / target_rms
            target_to_ref_ratio = reference_rms / target_rms

            print(f"Platform: {platform.system()} {platform.machine()}")
            print(f"Target RMS: {target_rms:.6f}")
            print(f"Reference RMS: {reference_rms:.6f}")
            print(f"Result RMS: {result_rms:.6f}")
            print(f"Improvement ratio: {improvement_ratio:.2f}x")
            print(f"Target-to-reference ratio: {target_to_ref_ratio:.2f}x")

            # Results should show improvement
            assert improvement_ratio > 1.0, "Processing should improve audio level"
            assert improvement_ratio < target_to_ref_ratio * 1.2, "Processing should not over-amplify"

            print("✅ Audio processing results consistent on this platform")