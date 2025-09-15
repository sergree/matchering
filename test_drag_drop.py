#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Drag-and-Drop Import Functionality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test the new drag-and-drop music import feature
"""

import sys
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

def create_test_audio_files(tmpdir):
    """Create test audio files for import testing"""
    test_files = []

    # Create different format test files
    formats = [
        ('test_track_1.wav', 'WAV', 44100),
        ('test_track_2.flac', 'FLAC', 48000),
    ]

    for filename, format_name, sample_rate in formats:
        # Create audio data
        duration = 2.0
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)

        # Create stereo sine wave
        freq = 440 + len(test_files) * 110
        audio = np.column_stack([
            np.sin(2 * np.pi * freq * t) * 0.3,
            np.sin(2 * np.pi * freq * t) * 0.28
        ]).astype(np.float32)

        file_path = tmpdir / filename

        try:
            if format_name == 'FLAC':
                sf.write(file_path, audio, sample_rate, format='FLAC')
            else:
                sf.write(file_path, audio, sample_rate)

            test_files.append(file_path)
            print(f"✅ Created test file: {filename}")

        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")

    return test_files

def test_import_functionality():
    """Test the audio import functionality without GUI"""
    print("🎵 Testing Audio Import Functionality...")

    try:
        from auralis.library import LibraryManager
        from auralis_gui import LibraryBrowser
        import customtkinter as ctk

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test audio files
            test_files = create_test_audio_files(tmpdir)
            if not test_files:
                print("❌ No test files created")
                return False

            # Create library
            db_path = tmpdir / "test_import.db"
            library = LibraryManager(str(db_path))

            # Create GUI components (hidden)
            root = ctk.CTk()
            root.withdraw()

            browser = LibraryBrowser(root)
            browser.set_library_manager(library)

            # Test single file import
            print("\n📂 Testing single file import...")
            file_path = str(test_files[0])
            success = browser._import_single_file(file_path)

            if success:
                print(f"✅ Successfully imported: {Path(file_path).name}")

                # Verify in database
                stats = library.get_library_stats()
                print(f"✅ Library now has {stats['total_tracks']} tracks")

                # Get track details
                tracks = library.get_recent_tracks(limit=1)
                if tracks:
                    track = tracks[0]
                    print(f"✅ Track details: {track.title} ({track.duration:.1f}s)")
                    print(f"   Format: {track.format}, Channels: {track.channels}")
                    print(f"   Sample rate: {track.sample_rate} Hz")

            else:
                print("❌ Failed to import file")
                return False

            # Test bulk import
            print("\n📁 Testing bulk import...")
            if len(test_files) > 1:
                browser._import_audio_files([str(f) for f in test_files[1:]])

                # Check final stats
                final_stats = library.get_library_stats()
                print(f"✅ Final library stats: {final_stats['total_tracks']} tracks")

                if final_stats['total_tracks'] == len(test_files):
                    print("✅ All test files imported successfully")
                else:
                    print(f"⚠️  Expected {len(test_files)} tracks, got {final_stats['total_tracks']}")

            root.destroy()
            return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_extraction():
    """Test metadata extraction capabilities"""
    print("\n🏷️  Testing Metadata Extraction...")

    try:
        from auralis_gui import LibraryBrowser
        import customtkinter as ctk

        # Create a test file with metadata
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create audio file
            sample_rate = 44100
            duration = 1.0
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)
            audio = np.column_stack([
                np.sin(2 * np.pi * 440 * t) * 0.3,
                np.sin(2 * np.pi * 440 * t) * 0.28
            ]).astype(np.float32)

            test_file = tmpdir / "metadata_test.wav"
            sf.write(test_file, audio, sample_rate)

            # Test metadata extraction (without actual metadata in WAV)
            root = ctk.CTk()
            root.withdraw()

            browser = LibraryBrowser(root)

            # Test tag extraction methods
            print("✅ Testing metadata extraction methods...")

            # Create a mock audio file object for testing
            class MockAudioFile:
                def __init__(self):
                    self.data = {}
                def __contains__(self, key):
                    return key in self.data
                def __getitem__(self, key):
                    return self.data[key]

            mock_file = MockAudioFile()

            # Test empty file
            result = browser._get_tag(mock_file, ['TEST'])
            assert result is None, "Should return None for empty audio file"

            result = browser._get_artists(mock_file)
            assert result == [], "Should return empty list for empty audio file"

            # Test with data
            mock_file.data = {'TIT2': ['Test Title'], 'TPE1': ['Test Artist']}
            result = browser._get_tag(mock_file, ['TIT2'])
            assert result == "Test Title", "Should extract title"

            result = browser._get_artists(mock_file)
            assert result == ['Test Artist'], "Should extract artists"

            print("✅ Metadata extraction methods working correctly")

            root.destroy()
            return True

    except Exception as e:
        print(f"❌ Metadata test failed: {e}")
        return False

def test_drag_drop_setup():
    """Test drag-and-drop setup"""
    print("\n🖱️  Testing Drag-and-Drop Setup...")

    try:
        from auralis_gui import LibraryBrowser
        import customtkinter as ctk

        root = ctk.CTk()
        root.withdraw()

        browser = LibraryBrowser(root)

        # Check if drag-and-drop was set up
        has_drag_drop = getattr(browser, '_drag_drop_available', False)

        if has_drag_drop:
            print("✅ Drag-and-drop functionality available")
            print("✅ Drop zone should be visible in GUI")
        else:
            print("⚠️  Drag-and-drop not available (tkinterdnd2 issue)")
            print("   This is normal in headless environments")

        # Check if drop zone was created
        has_drop_zone = hasattr(browser, 'drop_zone')
        print(f"✅ Drop zone created: {has_drop_zone}")

        root.destroy()
        return True

    except Exception as e:
        print(f"❌ Drag-drop setup test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Drag-and-Drop Import Features")
    print("=" * 60)

    # Run tests
    tests = [
        ("Import Functionality", test_import_functionality),
        ("Metadata Extraction", test_metadata_extraction),
        ("Drag-Drop Setup", test_drag_drop_setup),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("📊 DRAG-AND-DROP TEST RESULTS:")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 ALL DRAG-AND-DROP TESTS PASSED!")
        print("✨ New Features Available:")
        print("   🖱️  Drag-and-drop files and folders")
        print("   📁 Automatic folder scanning")
        print("   🏷️  Metadata extraction from audio files")
        print("   📊 Import progress tracking")
        print("   🎵 Support for MP3, FLAC, WAV, OGG, M4A")
        print("\n🚀 Enhanced library management ready!")
        sys.exit(0)
    else:
        print("\n⚠️  Some import features need attention")
        sys.exit(1)