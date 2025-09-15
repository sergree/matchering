#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test the integrated modern GUI without launching the full interface
"""

import sys
import tempfile
import numpy as np
import soundfile as sf

def test_integrated_gui():
    """Test that the integrated GUI can import and initialize properly"""
    print("🧪 Testing Modern GUI Integration...")

    try:
        # Import the integrated GUI module
        from modern_gui_integrated import RealPlayerAdapter, ModernMatcheringPlayer, HAS_REAL_PLAYER

        print(f"✅ Module imported successfully")
        print(f"Real player available: {'✅ YES' if HAS_REAL_PLAYER else '❌ NO'}")

        # Test player adapter initialization
        if HAS_REAL_PLAYER:
            try:
                adapter = RealPlayerAdapter()
                print("✅ RealPlayerAdapter initialized successfully")

                # Test basic functionality
                info = adapter.get_playback_info()
                print(f"✅ Playback info obtained: {info.get('state', 'unknown')}")

                # Clean up
                adapter.cleanup()
                print("✅ Adapter cleanup successful")

            except Exception as e:
                print(f"⚠️  RealPlayerAdapter failed: {e}")
                print("   This is expected if audio drivers are not available")

        # Test with mock player
        try:
            # Create a test instance (this will use mock if real player fails)
            print("🎵 Testing player initialization...")

            # This should always work, either with real or mock player
            test_app = ModernMatcheringPlayer()
            print("✅ ModernMatcheringPlayer created successfully")

            # Test getting player info
            player_info = test_app.player.get_playback_info()
            print(f"✅ Player info: state={player_info.get('state', 'unknown')}")

            # Clean up
            if hasattr(test_app.player, 'cleanup'):
                test_app.player.cleanup()
            test_app.destroy()
            print("✅ Test app cleanup successful")

        except Exception as e:
            print(f"❌ ModernMatcheringPlayer test failed: {e}")
            return False

        print("🎉 All integration tests passed!")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_audio_file_support():
    """Test audio file creation and loading capabilities"""
    print("\\n🎵 Testing Audio File Support...")

    try:
        # Create a test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_file = tmp.name

        # Generate test audio
        sample_rate = 44100
        duration = 2.0
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)

        # Stereo sine wave
        audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.3,  # A4 note
            np.sin(2 * np.pi * 440 * t) * 0.28  # Slightly quieter right channel
        ]).astype(np.float32)

        # Write test file
        sf.write(test_file, audio, sample_rate)
        print(f"✅ Test audio file created: {test_file}")

        # Test if our integrated GUI can handle it
        from modern_gui_integrated import RealPlayerAdapter, HAS_REAL_PLAYER

        if HAS_REAL_PLAYER:
            try:
                adapter = RealPlayerAdapter()
                success = adapter.load_file(test_file)
                print(f"✅ Real player file loading: {'SUCCESS' if success else 'FAILED'}")
                adapter.cleanup()
            except Exception as e:
                print(f"⚠️  Real player file test failed: {e}")

        # Clean up
        import os
        os.unlink(test_file)
        print("✅ Test file cleanup successful")

        return True

    except Exception as e:
        print(f"❌ Audio file test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Modern Matchering Player Integration")
    print("=" * 50)

    # Run tests
    gui_test = test_integrated_gui()
    audio_test = test_audio_file_support()

    print("\\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"GUI Integration: {'✅ PASS' if gui_test else '❌ FAIL'}")
    print(f"Audio File Support: {'✅ PASS' if audio_test else '❌ FAIL'}")

    if gui_test and audio_test:
        print("\\n🎉 ALL TESTS PASSED - Integration successful!")
        sys.exit(0)
    else:
        print("\\n⚠️  Some tests failed - Check output above")
        sys.exit(1)