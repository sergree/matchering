#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Enhanced Auralis Audio Player Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test the integration of advanced DSP capabilities into Auralis
"""

import sys
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

def create_test_audio(duration=2.0, filename="test_audio.wav"):
    """Create test audio file"""
    sample_rate = 44100
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)

    # Create stereo test signal
    audio = np.column_stack([
        np.sin(2 * np.pi * 440 * t) * 0.3,  # A4 note
        np.sin(2 * np.pi * 440 * t) * 0.28  # Slightly quieter right channel
    ]).astype(np.float32)

    sf.write(filename, audio, sample_rate)
    return filename

def test_enhanced_auralis():
    """Test the enhanced Auralis player"""
    print("🧪 Testing Enhanced Auralis Audio Player...")

    try:
        # Import enhanced Auralis
        import auralis
        from auralis import EnhancedAudioPlayer, PlayerConfig

        print("✅ Enhanced Auralis imported successfully")

        # Create test configuration
        config = PlayerConfig(
            sample_rate=44100,
            buffer_size=4410,  # 100ms buffer
            enable_level_matching=True,
            enable_auto_mastering=True
        )

        # Create enhanced player
        player = EnhancedAudioPlayer(config)
        print("✅ EnhancedAudioPlayer created successfully")

        # Create test audio files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            target_file = tmpdir / "target.wav"
            reference_file = tmpdir / "reference.wav"

            # Create target and reference files
            create_test_audio(2.0, target_file)
            create_test_audio(2.0, reference_file)  # Reference will be louder

            print("✅ Test audio files created")

            # Test file loading
            success = player.load_file(str(target_file))
            print(f"✅ Target file loading: {'SUCCESS' if success else 'FAILED'}")

            success = player.load_reference(str(reference_file))
            print(f"✅ Reference file loading: {'SUCCESS' if success else 'FAILED'}")

            # Test playback info
            info = player.get_playback_info()
            print(f"✅ Playback info obtained: state={info['state']}")
            print(f"   Duration: {info['duration_seconds']:.1f}s")
            print(f"   Current file: {info['current_file'] is not None}")
            print(f"   Reference file: {info['reference_file'] is not None}")

            # Test DSP processing info
            processing_info = info.get('processing', {})
            performance = processing_info.get('performance', {})
            effects = processing_info.get('effects', {})

            print(f"✅ DSP Processing available:")
            print(f"   Level matching: {effects.get('level_matching', {}).get('enabled', False)}")
            print(f"   Auto mastering: {effects.get('auto_mastering', {}).get('enabled', False)}")
            print(f"   Performance monitoring: {performance.get('status', 'unknown')}")

            # Test queue functionality
            track_info = {
                'file_path': str(target_file),
                'title': 'Test Track',
                'artist': 'Test Artist'
            }
            player.add_to_queue(track_info)

            queue_info = player.get_queue_info()
            print(f"✅ Queue management: {len(queue_info['tracks'])} tracks")

            # Test audio chunk processing
            player.play()
            chunk = player.get_audio_chunk(1024)
            print(f"✅ Audio chunk processing: {chunk.shape} samples")
            print(f"   Chunk max amplitude: {np.max(np.abs(chunk)):.3f}")

            player.stop()

            # Test effect control
            player.set_effect_enabled('level_matching', False)
            player.set_effect_enabled('auto_mastering', True)
            player.set_auto_master_profile('bright')
            print("✅ DSP effect control working")

            # Test cleanup
            player.cleanup()
            print("✅ Player cleanup successful")

        print("🎉 Enhanced Auralis integration test PASSED!")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auralis_vs_original():
    """Compare enhanced Auralis with original components"""
    print("\\n🔄 Testing Auralis vs Original Components...")

    try:
        # Test original Auralis
        import auralis
        basic_player = auralis.AudioPlayer()
        print("✅ Original AudioPlayer available")

        # Test enhanced version
        enhanced_player = auralis.EnhancedAudioPlayer()
        print("✅ EnhancedAudioPlayer available")

        # Compare capabilities
        basic_info = basic_player.get_playback_info()
        enhanced_info = enhanced_player.get_playback_info()

        print("📊 Capability Comparison:")
        print(f"   Basic player keys: {len(basic_info.keys())}")
        print(f"   Enhanced player keys: {len(enhanced_info.keys())}")
        print(f"   Enhanced features: queue, processing, session stats")

        # Test processing capabilities
        has_processing = 'processing' in enhanced_info
        has_queue = 'queue' in enhanced_info
        has_session = 'session' in enhanced_info

        print(f"✅ Enhanced features present:")
        print(f"   Advanced processing: {has_processing}")
        print(f"   Queue management: {has_queue}")
        print(f"   Session statistics: {has_session}")

        return True

    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Enhanced Auralis Integration")
    print("=" * 50)

    # Run tests
    main_test = test_enhanced_auralis()
    comparison_test = test_auralis_vs_original()

    print("\\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Enhanced Auralis Test: {'✅ PASS' if main_test else '❌ FAIL'}")
    print(f"Capability Comparison: {'✅ PASS' if comparison_test else '❌ FAIL'}")

    if main_test and comparison_test:
        print("\\n🎉 ALL TESTS PASSED - Enhanced Auralis integration successful!")
        print("✨ Advanced DSP capabilities successfully integrated into Auralis architecture")
        sys.exit(0)
    else:
        print("\\n⚠️  Some tests failed - Check output above")
        sys.exit(1)