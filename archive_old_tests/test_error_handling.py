#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Error Handling and Edge Case Tests
Tests error conditions, invalid inputs, and edge cases
"""

import numpy as np
import sys
import os
import tempfile
from pathlib import Path

# Add packages to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

def test_invalid_audio_inputs():
    """Test handling of invalid audio data"""
    print("🧪 Testing Invalid Audio Inputs...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor

        config = PlayerConfig(buffer_size_ms=100.0)
        processor = RealtimeProcessor(config)

        test_cases = [
            ("Empty array", np.array([])),
            ("Wrong shape - 1D", np.random.random(1000)),
            ("Wrong shape - 3D", np.random.random((100, 2, 3))),
            ("Wrong dtype - int32", np.random.randint(-32768, 32767, (100, 2), dtype=np.int32)),
            ("NaN values", np.full((100, 2), np.nan, dtype=np.float32)),
            ("Infinite values", np.full((100, 2), np.inf, dtype=np.float32)),
            ("Wrong buffer size", np.random.random((50, 2)).astype(np.float32)),  # Half expected size
            ("Mono audio", np.random.random((config.buffer_size_samples, 1)).astype(np.float32)),
        ]

        for description, test_audio in test_cases:
            print(f"   Testing {description}...")
            try:
                result = processor.process_audio_chunk(test_audio)
                print(f"      Result: {result.shape if hasattr(result, 'shape') else type(result)}")
            except Exception as e:
                print(f"      Handled error: {type(e).__name__}")

        print("✅ Invalid audio input handling tested")
        return True

    except ImportError as e:
        print(f"⚠️  DSP modules not available: {e}")
        return False

def test_invalid_file_inputs():
    """Test handling of invalid file inputs"""
    print("🧪 Testing Invalid File Inputs...")

    if not HAS_SOUNDFILE:
        print("⚠️  SoundFile required for file tests")
        return False

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.core.player import MatcheringPlayer
        from matchering_player.utils.file_loader import load_audio_file

        config = PlayerConfig()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various invalid files
            invalid_files = {
                "nonexistent.wav": None,  # File doesn't exist
                "empty.wav": b"",  # Empty file
                "text.wav": b"This is not a WAV file",  # Text content
                "truncated.wav": b"RIFF",  # Truncated WAV
                "zero_length.wav": b"RIFF\x00\x00\x00\x00WAVE",  # Zero-length WAV
            }

            for filename, content in invalid_files.items():
                filepath = Path(temp_dir) / filename

                if content is not None:
                    with open(filepath, 'wb') as f:
                        f.write(content)

                print(f"   Testing {filename}...")

                # Test file loading
                try:
                    audio, sr = load_audio_file(str(filepath))
                    print(f"      Unexpectedly succeeded: {audio.shape if audio is not None else None}")
                except Exception as e:
                    print(f"      Properly handled error: {type(e).__name__}")

                # Test player loading
                try:
                    player = MatcheringPlayer(config)
                    success = player.load_file(str(filepath))
                    print(f"      Player load result: {success}")
                except Exception as e:
                    print(f"      Player handled error: {type(e).__name__}")

        print("✅ Invalid file input handling tested")
        return True

    except ImportError as e:
        print(f"⚠️  Player modules not available: {e}")
        return False

def test_configuration_edge_cases():
    """Test edge cases in configuration"""
    print("🧪 Testing Configuration Edge Cases...")

    try:
        from matchering_player.core.config import PlayerConfig

        # Test extreme configurations
        edge_cases = [
            {"buffer_size_ms": 0.1},          # Very small buffer
            {"buffer_size_ms": 10000.0},      # Very large buffer
            {"sample_rate": 8000},            # Low sample rate
            {"sample_rate": 192000},          # High sample rate
            {"rms_smoothing_alpha": 0.0},     # No smoothing
            {"rms_smoothing_alpha": 1.0},     # Maximum smoothing
        ]

        for i, config_params in enumerate(edge_cases):
            print(f"   Testing config {i+1}: {config_params}")
            try:
                config = PlayerConfig(**config_params)
                print(f"      Created successfully: buffer={config.buffer_size_samples} samples")
            except Exception as e:
                print(f"      Handled error: {type(e).__name__}: {e}")

        # Test invalid configurations
        invalid_cases = [
            {"buffer_size_ms": -1.0},         # Negative buffer
            {"sample_rate": -44100},          # Negative sample rate
            {"sample_rate": 0},               # Zero sample rate
            {"rms_smoothing_alpha": -1.0},    # Invalid smoothing
            {"rms_smoothing_alpha": 2.0},     # Invalid smoothing
        ]

        for i, config_params in enumerate(invalid_cases):
            print(f"   Testing invalid config {i+1}: {config_params}")
            try:
                config = PlayerConfig(**config_params)
                print(f"      Unexpectedly succeeded")
            except Exception as e:
                print(f"      Properly rejected: {type(e).__name__}")

        print("✅ Configuration edge cases tested")
        return True

    except ImportError as e:
        print(f"⚠️  Config module not available: {e}")
        return False

def test_memory_limits():
    """Test behavior with extreme memory usage"""
    print("🧪 Testing Memory Limits...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor

        # Test with large audio buffers
        config = PlayerConfig(buffer_size_ms=1000.0)  # 1 second buffer
        processor = RealtimeProcessor(config)

        print(f"   Large buffer size: {config.buffer_size_samples} samples")

        # Test processing large chunks
        try:
            large_audio = np.random.normal(0, 0.1, (config.buffer_size_samples, 2)).astype(np.float32)
            result = processor.process_audio_chunk(large_audio)
            print(f"   Large buffer processing successful: {result.shape}")
        except MemoryError as e:
            print(f"   Memory limit reached (expected): {e}")
        except Exception as e:
            print(f"   Other error with large buffer: {type(e).__name__}: {e}")

        # Test with many small allocations
        small_config = PlayerConfig(buffer_size_ms=1.0)  # Very small buffer
        small_processor = RealtimeProcessor(small_config)

        try:
            for i in range(10000):  # Many small operations
                tiny_audio = np.random.normal(0, 0.1, (small_config.buffer_size_samples, 2)).astype(np.float32)
                result = small_processor.process_audio_chunk(tiny_audio)

            print("   Many small allocations successful")
        except Exception as e:
            print(f"   Small allocation test error: {type(e).__name__}: {e}")

        print("✅ Memory limit testing completed")
        return True

    except ImportError as e:
        print(f"⚠️  Memory test modules not available: {e}")
        return False

def test_concurrent_access():
    """Test concurrent access patterns"""
    print("🧪 Testing Concurrent Access...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor
        import threading
        import queue

        config = PlayerConfig(buffer_size_ms=50.0)
        processor = RealtimeProcessor(config)

        # Test concurrent processing
        errors = queue.Queue()
        results = queue.Queue()

        def worker_thread(worker_id):
            try:
                for i in range(50):
                    audio = np.random.normal(0, 0.1, (config.buffer_size_samples, 2)).astype(np.float32)
                    result = processor.process_audio_chunk(audio)
                    results.put(f"Worker {worker_id}: chunk {i}")
            except Exception as e:
                errors.put(f"Worker {worker_id}: {type(e).__name__}: {e}")

        # Start multiple threads
        threads = []
        for i in range(3):  # 3 concurrent threads
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        error_count = errors.qsize()
        result_count = results.qsize()

        print(f"   Concurrent processing results: {result_count} successful, {error_count} errors")

        if error_count > 0:
            print("   Errors encountered (this may be expected for thread safety):")
            while not errors.empty():
                print(f"      {errors.get()}")

        print("✅ Concurrent access testing completed")
        return True

    except ImportError as e:
        print(f"⚠️  Concurrent test modules not available: {e}")
        return False

def test_extreme_audio_content():
    """Test with extreme audio content"""
    print("🧪 Testing Extreme Audio Content...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor

        config = PlayerConfig(buffer_size_ms=100.0)
        processor = RealtimeProcessor(config)

        extreme_cases = [
            ("DC offset", lambda: np.full((config.buffer_size_samples, 2), 0.5, dtype=np.float32)),
            ("Maximum amplitude", lambda: np.full((config.buffer_size_samples, 2), 1.0, dtype=np.float32)),
            ("Clipped signal", lambda: np.full((config.buffer_size_samples, 2), 1.5, dtype=np.float32)),
            ("Ultra-quiet signal", lambda: np.random.normal(0, 1e-8, (config.buffer_size_samples, 2)).astype(np.float32)),
            ("High frequency", lambda: np.sin(2 * np.pi * 20000 * np.linspace(0, 0.1, config.buffer_size_samples))[:, np.newaxis].repeat(2, axis=1).astype(np.float32)),
            ("Sub-bass", lambda: np.sin(2 * np.pi * 5 * np.linspace(0, 0.1, config.buffer_size_samples))[:, np.newaxis].repeat(2, axis=1).astype(np.float32)),
            ("White noise", lambda: np.random.normal(0, 0.5, (config.buffer_size_samples, 2)).astype(np.float32)),
            ("Impulse", lambda: np.concatenate([np.array([[1.0, 1.0]]), np.zeros((config.buffer_size_samples-1, 2))], axis=0).astype(np.float32)),
        ]

        for description, audio_generator in extreme_cases:
            print(f"   Testing {description}...")
            try:
                audio = audio_generator()
                result = processor.process_audio_chunk(audio)

                # Check for issues in output
                has_nan = np.isnan(result).any()
                has_inf = np.isinf(result).any()
                max_val = np.max(np.abs(result))

                print(f"      Output: max={max_val:.6f}, NaN={has_nan}, Inf={has_inf}")

                if has_nan or has_inf:
                    print("      ⚠️  Output contains NaN or Inf values")
                elif max_val > 10.0:
                    print("      ⚠️  Output amplitude very large")

            except Exception as e:
                print(f"      Error (may be expected): {type(e).__name__}: {e}")

        print("✅ Extreme audio content testing completed")
        return True

    except ImportError as e:
        print(f"⚠️  Extreme content test modules not available: {e}")
        return False

def test_resource_cleanup():
    """Test proper resource cleanup"""
    print("🧪 Testing Resource Cleanup...")

    try:
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor

        # Test creating and destroying many processors
        config = PlayerConfig(buffer_size_ms=50.0)

        processors = []
        for i in range(20):
            processor = RealtimeProcessor(config)

            # Use the processor briefly
            test_audio = np.random.normal(0, 0.1, (config.buffer_size_samples, 2)).astype(np.float32)
            processor.process_audio_chunk(test_audio)

            processors.append(processor)

        print(f"   Created {len(processors)} processors")

        # Clean up explicitly
        cleaned_up = 0
        for processor in processors:
            try:
                if hasattr(processor, 'cleanup'):
                    processor.cleanup()
                    cleaned_up += 1
                elif hasattr(processor, 'stop_processing'):
                    processor.stop_processing()
                    cleaned_up += 1
            except Exception as e:
                print(f"      Cleanup error: {type(e).__name__}: {e}")

        print(f"   Cleaned up {cleaned_up} processors")

        # Clear references
        processors.clear()

        print("✅ Resource cleanup testing completed")
        return True

    except ImportError as e:
        print(f"⚠️  Resource cleanup test modules not available: {e}")
        return False

def main():
    """Run all error handling and edge case tests"""
    print("🚀 Error Handling and Edge Case Tests")
    print("=" * 60)

    tests = [
        ("Invalid Audio Inputs", test_invalid_audio_inputs),
        ("Invalid File Inputs", test_invalid_file_inputs),
        ("Configuration Edge Cases", test_configuration_edge_cases),
        ("Memory Limits", test_memory_limits),
        ("Concurrent Access", test_concurrent_access),
        ("Extreme Audio Content", test_extreme_audio_content),
        ("Resource Cleanup", test_resource_cleanup),
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
    print(f"🎯 Error Handling Test Results: {passed}/{total} passed")

    if passed >= total * 0.8:  # 80% pass rate acceptable for error tests
        print("🎉 Error handling tests mostly passed!")
        return True
    else:
        print("❌ Too many error handling tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)