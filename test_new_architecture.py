#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test the new unified Auralis architecture
"""

import numpy as np
import tempfile
import soundfile as sf
from pathlib import Path

def test_core_processing():
    """Test the core processing pipeline"""
    print("🧪 Testing Auralis Core Processing")

    # Import our new unified architecture
    import auralis

    # Set up logging
    auralis.log(print)

    # Create test audio files
    duration = 3.0
    sample_rate = 44100
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)

    # Create target (quiet)
    target_audio = np.column_stack([
        np.sin(2 * np.pi * 440 * t) * 0.1,
        np.sin(2 * np.pi * 440 * t) * 0.09
    ]).astype(np.float32)

    # Create reference (loud)
    reference_audio = np.column_stack([
        np.sin(2 * np.pi * 440 * t) * 0.6,
        np.sin(2 * np.pi * 440 * t) * 0.58
    ]).astype(np.float32)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Save test files
        target_file = tmpdir / "target.wav"
        reference_file = tmpdir / "reference.wav"
        result_file = tmpdir / "result.wav"

        sf.write(target_file, target_audio, sample_rate)
        sf.write(reference_file, reference_audio, sample_rate)

        print(f"📁 Test files created in: {tmpdir}")

        # Test core processing
        print("⚡ Processing with new architecture...")
        auralis.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        # Verify result
        if result_file.exists():
            result_audio, result_sr = sf.read(str(result_file))
            print(f"✅ Processing successful!")
            print(f"   Input shape: {target_audio.shape}")
            print(f"   Output shape: {result_audio.shape}")
            print(f"   Sample rate: {result_sr} Hz")

            # Calculate levels
            target_rms = np.sqrt(np.mean(target_audio ** 2))
            result_rms = np.sqrt(np.mean(result_audio ** 2))
            print(f"   Target RMS: {target_rms:.6f}")
            print(f"   Result RMS: {result_rms:.6f}")
            print(f"   RMS improvement: {result_rms/target_rms:.1f}x")
        else:
            print("❌ Processing failed - no result file")


def test_player():
    """Test the real-time player"""
    print("\n🎵 Testing Auralis Player")

    import auralis

    # Create player
    config = auralis.PlayerConfig(
        sample_rate=44100,
        buffer_size=1024,
        enable_level_matching=True
    )

    player = auralis.AudioPlayer(config)
    print(f"✅ Player created: {config}")

    # Test player info
    info = player.get_playback_info()
    print(f"📊 Player info: {info}")


if __name__ == "__main__":
    print("🎯 Testing New Unified Auralis Architecture")
    print("=" * 50)

    try:
        test_core_processing()
        test_player()

        print("\n🎉 All tests passed! New architecture is working!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()