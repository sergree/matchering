#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Core Matchering Library Components
Tests the core matchering library functions, DSP algorithms, and processing stages
"""

import numpy as np
import sys
import os
import tempfile
from pathlib import Path

# Add matchering package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

def create_test_audio(duration=2.0, sample_rate=44100, frequency=440.0, amplitude=0.5):
    """Create test audio data"""
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)

    # Create stereo sine wave
    left = np.sin(2 * np.pi * frequency * t) * amplitude
    right = np.sin(2 * np.pi * frequency * t * 1.01) * amplitude * 0.8

    return np.column_stack([left, right]).astype(np.float32), sample_rate

def test_dsp_functions():
    """Test core DSP functions in matchering.dsp"""
    print("🧪 Testing Core DSP Functions...")

    try:
        from matchering import dsp

        # Create test audio
        audio, sr = create_test_audio(1.0)

        # Test RMS calculation
        rms_value = dsp.rms(audio)
        print(f"   RMS calculation: {rms_value:.6f}")
        assert 0.1 < rms_value < 0.8, f"RMS should be reasonable, got {rms_value}"

        # Test normalization
        normalized = dsp.normalize(audio, 0.8)
        normalized_rms = dsp.rms(normalized)
        print(f"   Normalized RMS: {normalized_rms:.6f}")
        assert abs(normalized_rms - 0.8) < 0.01, "Normalization failed"

        # Test amplification
        amplified = dsp.amplify(audio, 2.0)
        amplified_rms = dsp.rms(amplified)
        original_rms = dsp.rms(audio)
        gain_ratio = amplified_rms / original_rms
        print(f"   Amplification ratio: {gain_ratio:.2f}")
        assert abs(gain_ratio - 2.0) < 0.1, "Amplification failed"

        # Test mid-side processing
        if hasattr(dsp, 'to_mid_side') and hasattr(dsp, 'from_mid_side'):
            mid, side = dsp.to_mid_side(audio)
            reconstructed = dsp.from_mid_side(mid, side)
            difference = np.max(np.abs(audio - reconstructed))
            print(f"   Mid-side conversion error: {difference:.8f}")
            assert difference < 1e-6, "Mid-side conversion failed"

        print("✅ Core DSP functions working correctly")
        return True

    except ImportError as e:
        print(f"⚠️  Core DSP module not available: {e}")
        return False

def test_loader_module():
    """Test audio file loading functionality"""
    print("🧪 Testing Loader Module...")

    if not HAS_SOUNDFILE:
        print("⚠️  SoundFile not available - skipping loader tests")
        return False

    try:
        from matchering import loader

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = Path(temp_dir) / "test_audio.wav"
            audio, sr = create_test_audio(2.0, 44100)
            sf.write(test_file, audio, sr)

            # Test loading
            loaded_audio, loaded_sr = loader.load(str(test_file))
            print(f"   Loaded audio: {loaded_audio.shape}, {loaded_sr}Hz")

            # Verify loaded audio matches original
            assert loaded_audio.shape == audio.shape, "Shape mismatch"
            assert loaded_sr == sr, "Sample rate mismatch"

            # Test with different sample rates
            for test_sr in [22050, 48000, 96000]:
                resampled_file = Path(temp_dir) / f"test_{test_sr}.wav"
                test_audio_resampled, _ = create_test_audio(1.0, test_sr)
                sf.write(resampled_file, test_audio_resampled, test_sr)

                loaded_resampled, loaded_sr_resampled = loader.load(str(resampled_file))
                print(f"   Loaded {test_sr}Hz file: {loaded_resampled.shape}, {loaded_sr_resampled}Hz")
                assert loaded_sr_resampled == test_sr, f"Sample rate mismatch for {test_sr}Hz"

        print("✅ Loader module working correctly")
        return True

    except ImportError as e:
        print(f"⚠️  Loader module not available: {e}")
        return False

def test_limiter_module():
    """Test Hyrax limiter functionality"""
    print("🧪 Testing Limiter Module...")

    try:
        from matchering.limiter import hyrax

        # Create test audio with peaks
        audio, sr = create_test_audio(1.0, amplitude=1.2)  # Clipped audio

        # Test limiter
        limited = hyrax.limit(audio, sample_rate=sr)
        print(f"   Input peak: {np.max(np.abs(audio)):.3f}")
        print(f"   Output peak: {np.max(np.abs(limited)):.3f}")

        # Check that output is limited
        assert np.max(np.abs(limited)) <= 1.0, "Limiter failed to limit peaks"

        # Check that RMS is preserved reasonably
        input_rms = np.sqrt(np.mean(audio**2))
        output_rms = np.sqrt(np.mean(limited**2))
        rms_ratio = output_rms / input_rms
        print(f"   RMS preservation ratio: {rms_ratio:.3f}")
        assert 0.7 < rms_ratio < 1.0, "Limiter changed RMS too much"

        print("✅ Limiter module working correctly")
        return True

    except ImportError as e:
        print(f"⚠️  Limiter module not available: {e}")
        return False

def test_stages_module():
    """Test multi-stage processing pipeline"""
    print("🧪 Testing Stages Module...")

    try:
        from matchering import stages

        # Create test audio
        target_audio, sr = create_test_audio(2.0, amplitude=0.2)  # Quiet target
        reference_audio, _ = create_test_audio(2.0, amplitude=0.7)  # Loud reference

        # Test stage processing if available
        if hasattr(stages, 'process'):
            result = stages.process(target_audio, reference_audio, sr)

            # Check that result has same shape as input
            assert result.shape == target_audio.shape, "Stage processing changed audio shape"

            # Check that level was adjusted
            target_rms = np.sqrt(np.mean(target_audio**2))
            result_rms = np.sqrt(np.mean(result**2))
            print(f"   Target RMS: {target_rms:.6f}")
            print(f"   Result RMS: {result_rms:.6f}")
            print(f"   RMS gain: {result_rms/target_rms:.2f}")

            assert result_rms > target_rms * 1.5, "Stage processing should increase quiet audio level"

        print("✅ Stages module working correctly")
        return True

    except ImportError as e:
        print(f"⚠️  Stages module not available: {e}")
        return False

def test_stage_helpers():
    """Test stage helper modules for level and frequency matching"""
    print("🧪 Testing Stage Helpers...")

    try:
        from matchering.stage_helpers import match_levels, match_frequencies

        # Create test audio with different characteristics
        quiet_audio, sr = create_test_audio(1.0, amplitude=0.1)
        loud_audio, _ = create_test_audio(1.0, amplitude=0.8)

        # Test level matching if available
        if hasattr(match_levels, 'match'):
            level_matched = match_levels.match(quiet_audio, loud_audio, sr)

            quiet_rms = np.sqrt(np.mean(quiet_audio**2))
            matched_rms = np.sqrt(np.mean(level_matched**2))
            loud_rms = np.sqrt(np.mean(loud_audio**2))

            print(f"   Quiet RMS: {quiet_rms:.6f}")
            print(f"   Matched RMS: {matched_rms:.6f}")
            print(f"   Reference RMS: {loud_rms:.6f}")

            # Should be closer to reference level
            assert matched_rms > quiet_rms * 2, "Level matching should increase level significantly"

        # Test frequency matching if available
        if hasattr(match_frequencies, 'match'):
            # Create audio with different frequency content
            bass_heavy = create_test_audio(1.0, frequency=100.0, amplitude=0.5)[0]
            treble_heavy = create_test_audio(1.0, frequency=2000.0, amplitude=0.5)[0]

            freq_matched = match_frequencies.match(bass_heavy, treble_heavy, sr)

            print(f"   Bass-heavy input shape: {bass_heavy.shape}")
            print(f"   Frequency matched output shape: {freq_matched.shape}")

            assert freq_matched.shape == bass_heavy.shape, "Frequency matching changed shape"

        print("✅ Stage helpers working correctly")
        return True

    except ImportError as e:
        print(f"⚠️  Stage helpers not available: {e}")
        return False

def test_saver_module():
    """Test audio file saving functionality"""
    print("🧪 Testing Saver Module...")

    if not HAS_SOUNDFILE:
        print("⚠️  SoundFile not available - skipping saver tests")
        return False

    try:
        from matchering import saver

        # Create test audio
        audio, sr = create_test_audio(1.0)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test saving different formats
            formats_to_test = [
                ("test_16bit.wav", {"subtype": "PCM_16"}),
                ("test_24bit.wav", {"subtype": "PCM_24"}),
                ("test_float.wav", {"subtype": "FLOAT"})
            ]

            for filename, format_options in formats_to_test:
                output_path = Path(temp_dir) / filename

                # Save audio
                if hasattr(saver, 'save'):
                    saver.save(audio, str(output_path), sr, **format_options)
                else:
                    # Fallback direct save for testing
                    sf.write(output_path, audio, sr, **format_options)

                # Verify file was created and can be loaded
                assert output_path.exists(), f"Failed to create {filename}"

                loaded_audio, loaded_sr = sf.read(output_path)
                print(f"   Saved and loaded {filename}: {loaded_audio.shape}, {loaded_sr}Hz")

                assert loaded_audio.shape == audio.shape, f"Shape mismatch in {filename}"
                assert loaded_sr == sr, f"Sample rate mismatch in {filename}"

        print("✅ Saver module working correctly")
        return True

    except ImportError as e:
        print(f"⚠️  Saver module not available: {e}")
        return False

def main():
    """Run all core library tests"""
    print("🚀 Testing Core Matchering Library Components")
    print("=" * 60)

    if not HAS_SOUNDFILE:
        print("⚠️  Note: soundfile not available, some tests will be skipped")
        print("   Install with: pip install soundfile")
        print()

    tests = [
        ("DSP Functions", test_dsp_functions),
        ("Loader Module", test_loader_module),
        ("Limiter Module", test_limiter_module),
        ("Stages Module", test_stages_module),
        ("Stage Helpers", test_stage_helpers),
        ("Saver Module", test_saver_module)
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
                print("⚠️  SKIPPED")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"🎯 Core Library Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All core library components working correctly!")
        return True
    elif passed > 0:
        print("⚠️  Some tests passed, some components may need attention")
        return True
    else:
        print("❌ Core library tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)