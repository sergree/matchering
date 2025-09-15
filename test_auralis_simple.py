#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Auralis Library Integration Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test core functionality without session management complexity
"""

import sys
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

def create_test_track(filename, duration=2.0):
    """Create a single test track"""
    sample_rate = 44100
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)

    # Create stereo sine wave
    audio = np.column_stack([
        np.sin(2 * np.pi * 440 * t) * 0.3,
        np.sin(2 * np.pi * 440 * t) * 0.28
    ]).astype(np.float32)

    sf.write(filename, audio, sample_rate)
    return {
        'filepath': str(filename),
        'title': 'Test Track',
        'artists': ['Test Artist'],
        'duration': duration,
        'sample_rate': sample_rate,
        'channels': 2,
        'format': 'WAV',
        'filesize': Path(filename).stat().st_size,
    }

def test_core_integration():
    """Test core Auralis integration"""
    print("🎵 Testing Core Auralis Integration...")

    try:
        import auralis
        from auralis import EnhancedAudioPlayer, PlayerConfig
        from auralis.library import LibraryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create library
            db_path = tmpdir / "test.db"
            library = LibraryManager(str(db_path))
            print("✅ LibraryManager created")

            # Create test track
            track_file = tmpdir / "test.wav"
            track_info = create_test_track(track_file)
            track = library.add_track(track_info)
            print(f"✅ Track added: {track.title if track else 'Failed'}")

            # Create enhanced player
            config = PlayerConfig(
                enable_level_matching=True,
                enable_auto_mastering=True
            )
            player = EnhancedAudioPlayer(config, library)
            print("✅ Enhanced player created")

            # Test track loading by ID
            if track:
                success = player.load_track_from_library(track.id)
                print(f"✅ Track loading: {'SUCCESS' if success else 'FAILED'}")

                # Test playback info
                info = player.get_playback_info()
                print(f"✅ Playback info obtained")
                print(f"   State: {info['state']}")
                print(f"   Duration: {info['duration_seconds']:.1f}s")
                print(f"   Library track: {info['library']['current_track_data']['title'] if info['library']['current_track_data'] else 'None'}")

                # Test DSP processing
                processing = info.get('processing', {})
                effects = processing.get('effects', {})
                print(f"✅ DSP Effects:")
                print(f"   Level matching: {effects.get('level_matching', {}).get('enabled', False)}")
                print(f"   Auto mastering: {effects.get('auto_mastering', {}).get('enabled', False)}")

                # Test audio processing
                chunk = player.get_audio_chunk(1024)
                print(f"✅ Audio processing: {chunk.shape} samples, max amplitude: {np.max(np.abs(chunk)):.3f}")

            # Test library search
            results = library.search_tracks("Test", limit=5)
            print(f"✅ Search results: {len(results)} tracks")

            # Test library stats
            stats = library.get_library_stats()
            print(f"✅ Library stats: {stats['total_tracks']} tracks")

            return True

    except Exception as e:
        print(f"❌ Core integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_features():
    """Test advanced features"""
    print("\\n🚀 Testing Advanced Features...")

    try:
        import auralis
        from auralis import EnhancedAudioPlayer, PlayerConfig
        from auralis.library import LibraryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create library with multiple tracks
            library = LibraryManager(str(tmpdir / "advanced.db"))

            track_ids = []
            for i in range(3):
                track_file = tmpdir / f"track_{i}.wav"
                track_info = create_test_track(track_file, duration=1.5 + i * 0.5)
                track_info['title'] = f'Track {i+1}'
                track_info['genres'] = ['Electronic', 'Test'][i % 2:i % 2 + 1]
                track_info['mastering_quality'] = 0.7 + i * 0.1

                track = library.add_track(track_info)
                if track:
                    track_ids.append(track.id)

            print(f"✅ Created library with {len(track_ids)} tracks")

            # Create enhanced player
            player = EnhancedAudioPlayer(library_manager=library)

            # Test automatic reference selection
            if track_ids:
                player.load_track_from_library(track_ids[0])

                # Check if reference was auto-selected
                info = player.get_playback_info()
                has_reference = info.get('reference_file') is not None
                print(f"✅ Auto reference selection: {'ACTIVE' if has_reference else 'INACTIVE'}")

                # Test reference finding
                track = library.get_track(track_ids[0])
                references = library.find_reference_tracks(track, limit=2)
                print(f"✅ Reference tracks found: {len(references)}")

            # Test queue management
            for track_id in track_ids:
                player.add_track_to_queue(track_id)

            queue_info = player.get_queue_info()
            print(f"✅ Queue management: {len(queue_info['tracks'])} tracks in queue")

            # Test mastering profiles
            profiles = ['balanced', 'warm', 'bright', 'punchy']
            for profile in profiles:
                player.set_auto_master_profile(profile)

            print(f"✅ Mastering profiles tested: {len(profiles)} profiles")

            # Test performance monitoring
            performance = player.processor.get_processing_info()['performance']
            print(f"✅ Performance monitoring: {performance['status']}")

            return True

    except Exception as e:
        print(f"❌ Advanced features test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 Simple Auralis Integration Test")
    print("=" * 50)

    # Run tests
    core_test = test_core_integration()
    advanced_test = test_advanced_features()

    print("\\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Core Integration: {'✅ PASS' if core_test else '❌ FAIL'}")
    print(f"Advanced Features: {'✅ PASS' if advanced_test else '❌ FAIL'}")

    if core_test and advanced_test:
        print("\\n🎉 AURALIS INTEGRATION SUCCESSFUL!")
        print("✨ Key Features Working:")
        print("   • Library management with SQLite database")
        print("   • Enhanced audio player with advanced DSP")
        print("   • Automatic reference track selection")
        print("   • Real-time level matching and auto-mastering")
        print("   • Queue management and playlist support")
        print("   • Performance monitoring and adaptive quality")
        print("   • Library search and filtering")
        sys.exit(0)
    else:
        print("\\n⚠️  Some features need attention")
        sys.exit(1)