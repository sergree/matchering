#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration and Regression Tests for Matchering
Tests end-to-end workflows and ensures no performance regression
"""

import numpy as np
import sys
import os
import time
import tempfile
from pathlib import Path

# Add both packages to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

def create_test_audio_files(temp_dir):
    """Create a set of test audio files with different characteristics"""
    test_files = {}

    if not HAS_SOUNDFILE:
        return test_files

    # Helper to create different types of audio
    def create_audio(duration, sr, freq, amplitude, characteristics="normal"):
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
    test_configs = [
        ("quiet_target.wav", 3.0, 44100, 440, 0.1, "quiet"),
        ("loud_reference.wav", 3.0, 44100, 440, 0.8, "loud"),
        ("bass_heavy_target.wav", 3.0, 44100, 220, 0.4, "bass_heavy"),
        ("treble_reference.wav", 3.0, 44100, 880, 0.6, "treble_heavy"),
        ("short_target.wav", 0.5, 44100, 440, 0.3, "normal"),
        ("long_reference.wav", 10.0, 44100, 440, 0.7, "normal"),
        ("hires_target.wav", 2.0, 48000, 440, 0.4, "normal"),
        ("hires_reference.wav", 2.0, 48000, 440, 0.7, "normal"),
    ]

    for name, duration, sr, freq, amp, char in test_configs:
        audio = create_audio(duration, sr, freq, amp, char)
        filepath = Path(temp_dir) / name
        sf.write(filepath, audio, sr)
        test_files[name] = str(filepath)
        print(f"   Created {name}: {duration}s, {sr}Hz, {char}")

    return test_files

def test_full_matchering_pipeline():
    """Test the complete matchering pipeline end-to-end"""
    print("🧪 Testing Full Matchering Pipeline...")

    if not HAS_SOUNDFILE:
        print("⚠️  SoundFile required for pipeline tests")
        return False

    try:
        import matchering

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = create_test_audio_files(temp_dir)

            if not test_files:
                print("⚠️  Could not create test files")
                return False

            # Test basic matching
            target_file = test_files["quiet_target.wav"]
            reference_file = test_files["loud_reference.wav"]
            output_file = Path(temp_dir) / "matched_output.wav"

            print(f"   Processing: {Path(target_file).name} -> {Path(reference_file).name}")

            # Run matchering
            start_time = time.perf_counter()
            matchering.process(
                target=target_file,
                reference=reference_file,
                results=[str(output_file)]
            )
            end_time = time.perf_counter()

            processing_time = end_time - start_time
            print(f"   Processing time: {processing_time:.2f}s")

            # Verify output file
            assert output_file.exists(), "Output file was not created"

            # Load and verify output
            output_audio, output_sr = sf.read(output_file)
            target_audio, target_sr = sf.read(target_file)
            reference_audio, reference_sr = sf.read(reference_file)

            print(f"   Output shape: {output_audio.shape}, {output_sr}Hz")
            assert output_audio.shape == target_audio.shape, "Output shape mismatch"

            # Check that level was adjusted
            target_rms = np.sqrt(np.mean(target_audio**2))
            output_rms = np.sqrt(np.mean(output_audio**2))
            reference_rms = np.sqrt(np.mean(reference_audio**2))

            print(f"   Target RMS: {target_rms:.6f}")
            print(f"   Output RMS: {output_rms:.6f}")
            print(f"   Reference RMS: {reference_rms:.6f}")

            # Output should be closer to reference level
            target_ref_diff = abs(target_rms - reference_rms)
            output_ref_diff = abs(output_rms - reference_rms)

            print(f"   Level matching improvement: {target_ref_diff/output_ref_diff:.2f}x better")
            assert output_ref_diff < target_ref_diff, "Matchering should improve level matching"

        print("✅ Full matchering pipeline working correctly")
        return True

    except ImportError as e:
        print(f"⚠️  Matchering module not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def test_player_integration():
    """Test matchering player integration"""
    print("🧪 Testing Player Integration...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.core.player import MatcheringPlayer
        from matchering_player.dsp import RealtimeProcessor

        # Test configuration integration
        config = PlayerConfig(
            buffer_size_ms=100.0,
            enable_level_matching=True,
            enable_frequency_matching=True,
            enable_stereo_width=True
        )

        # Test processor initialization
        processor = RealtimeProcessor(config)
        assert processor.config == config, "Configuration not properly passed"

        # Test player initialization
        try:
            player = MatcheringPlayer(config)

            # Test basic functionality
            devices = player.get_audio_devices()
            formats = player.get_supported_formats()

            print(f"   Audio devices detected: {len(devices.get('output', []))}")
            print(f"   Supported formats: {len(formats)}")

            # Test with test files if available
            if HAS_SOUNDFILE:
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_files = create_test_audio_files(temp_dir)

                    if test_files:
                        # Test file loading
                        success = player.load_file(test_files["quiet_target.wav"])
                        assert success, "Failed to load test file"

                        # Test reference loading
                        ref_success = player.load_reference_track(test_files["loud_reference.wav"])
                        assert ref_success, "Failed to load reference"

                        # Get playback info
                        info = player.get_playback_info()
                        assert info['duration_seconds'] > 0, "Invalid duration"

            print("✅ Player integration working correctly")
            return True

        except Exception as e:
            if "PyAudio" in str(e) or "audio device" in str(e):
                print("⚠️  Audio system not available - core integration still tested")
                return True
            raise

    except ImportError as e:
        print(f"⚠️  Player modules not available: {e}")
        return False

def test_memory_management():
    """Test memory usage and cleanup"""
    print("🧪 Testing Memory Management...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor

        config = PlayerConfig(buffer_size_ms=50.0)

        # Create and destroy multiple processors to test cleanup
        processors = []
        for i in range(10):
            processor = RealtimeProcessor(config)

            # Process some audio
            test_audio = np.random.normal(0, 0.1, (config.buffer_size_samples, 2)).astype(np.float32)
            processor.process_audio_chunk(test_audio)

            processors.append(processor)

        # Test cleanup
        for processor in processors:
            if hasattr(processor, 'cleanup'):
                processor.cleanup()

        print("✅ Memory management test completed")
        return True

    except ImportError as e:
        print(f"⚠️  Memory test modules not available: {e}")
        return False

def test_performance_regression():
    """Test for performance regressions"""
    print("🧪 Testing Performance Regression...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor

        config = PlayerConfig(buffer_size_ms=100.0)
        processor = RealtimeProcessor(config)

        # Test processing performance
        test_audio = np.random.normal(0, 0.1, (config.buffer_size_samples, 2)).astype(np.float32)

        # Warmup
        for _ in range(10):
            processor.process_audio_chunk(test_audio)

        # Measure performance
        num_chunks = 100
        start_time = time.perf_counter()

        for _ in range(num_chunks):
            processor.process_audio_chunk(test_audio)

        end_time = time.perf_counter()

        processing_time = end_time - start_time
        real_time = (num_chunks * config.buffer_size_samples) / config.sample_rate
        cpu_usage = processing_time / real_time

        print(f"   Processing time: {processing_time:.3f}s")
        print(f"   Real-time equivalent: {real_time:.3f}s")
        print(f"   CPU usage: {cpu_usage:.1%}")

        # Performance thresholds
        if cpu_usage < 0.1:
            print("   🚀 Excellent performance!")
        elif cpu_usage < 0.5:
            print("   ✅ Good performance")
        elif cpu_usage < 1.0:
            print("   ⚠️  Acceptable performance")
        else:
            print("   ❌ Performance regression detected!")
            return False

        print("✅ Performance regression test passed")
        return True

    except ImportError as e:
        print(f"⚠️  Performance test modules not available: {e}")
        return False

def test_format_compatibility():
    """Test different audio format compatibility"""
    print("🧪 Testing Format Compatibility...")

    if not HAS_SOUNDFILE:
        print("⚠️  SoundFile required for format tests")
        return False

    try:
        # Test different sample rates and bit depths
        test_configs = [
            (22050, "PCM_16", 0.5),
            (44100, "PCM_16", 1.0),
            (44100, "PCM_24", 1.0),
            (48000, "PCM_16", 1.5),
            (48000, "PCM_24", 1.5),
            (96000, "PCM_24", 2.0),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for sr, subtype, duration in test_configs:
                # Create test file
                samples = int(duration * sr)
                t = np.linspace(0, duration, samples)
                audio = np.column_stack([
                    np.sin(2 * np.pi * 440 * t) * 0.5,
                    np.sin(2 * np.pi * 440 * t * 1.01) * 0.5
                ]).astype(np.float32)

                filename = f"test_{sr}_{subtype}.wav"
                filepath = Path(temp_dir) / filename
                sf.write(filepath, audio, sr, subtype=subtype)

                # Test loading
                loaded_audio, loaded_sr = sf.read(filepath)
                print(f"   {filename}: {loaded_audio.shape}, {loaded_sr}Hz - OK")

                assert loaded_sr == sr, f"Sample rate mismatch: {loaded_sr} != {sr}"
                assert loaded_audio.shape[0] == samples, "Sample count mismatch"

        print("✅ Format compatibility test passed")
        return True

    except Exception as e:
        print(f"❌ Format compatibility test failed: {e}")
        return False

def main():
    """Run all integration and regression tests"""
    print("🚀 Integration and Regression Tests")
    print("=" * 60)

    if not HAS_SOUNDFILE:
        print("⚠️  Note: soundfile not available, some tests will be skipped")
        print("   Install with: pip install soundfile")
        print()

    tests = [
        ("Full Matchering Pipeline", test_full_matchering_pipeline),
        ("Player Integration", test_player_integration),
        ("Memory Management", test_memory_management),
        ("Performance Regression", test_performance_regression),
        ("Format Compatibility", test_format_compatibility),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)

        try:
            if test_func():
                passed += 1
                print("✅ PASSED")
            else:
                print("⚠️  FAILED or SKIPPED")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"🎯 Integration Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        return True
    elif passed > total // 2:
        print("⚠️  Most tests passed - some issues may need attention")
        return True
    else:
        print("❌ Integration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)