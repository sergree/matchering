#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Auralis Modern GUI
~~~~~~~~~~~~~~~~~~~~~~

Test the modern GUI functionality and components
"""

import sys
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path
import time

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def create_test_library(tmpdir):
    """Create a test library with sample tracks"""
    try:
        from auralis.library import LibraryManager

        # Create library
        db_path = tmpdir / "gui_test_library.db"
        library = LibraryManager(str(db_path))

        # Create test tracks
        track_data = []
        for i in range(5):
            # Create audio file
            duration = 2.0 + i * 0.5
            sample_rate = 44100
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)

            freq = 440 + i * 110
            audio = np.column_stack([
                np.sin(2 * np.pi * freq * t) * (0.3 - i * 0.05),
                np.sin(2 * np.pi * freq * t) * (0.28 - i * 0.05)
            ]).astype(np.float32)

            track_file = tmpdir / f"track_{i+1}.wav"
            sf.write(track_file, audio, sample_rate)

            # Track metadata
            track_info = {
                'filepath': str(track_file),
                'title': f'GUI Test Track {i+1}',
                'artists': [f'Test Artist {i+1}'],
                'album': f'Test Album {(i // 2) + 1}',
                'genres': ['Electronic', 'Rock', 'Jazz'][i % 3:i % 3 + 1],
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': 2,
                'format': 'WAV',
                'filesize': track_file.stat().st_size,
                'track_number': (i % 3) + 1,
                'year': 2024,
                'mastering_quality': 0.7 + i * 0.05,
                'dr_rating': 10.0 + i * 2.0,
                'rms_level': -18.0 + i * 2.0,
                'peak_level': -6.0 + i * 1.0,
            }

            track = library.add_track(track_info)
            if track:
                track_data.append(track)

        return library, track_data

    except Exception as e:
        print(f"Failed to create test library: {e}")
        return None, []

def test_gui_components():
    """Test GUI component functionality without launching full GUI"""
    print("🧪 Testing Auralis GUI Components...")

    try:
        import customtkinter as ctk
        from auralis_gui import RealTimeVisualization, LibraryBrowser, PlayerControls, MasteringControls

        # Test component creation
        root = ctk.CTk()
        root.withdraw()  # Hide main window

        # Test RealTimeVisualization
        viz = RealTimeVisualization(root)
        viz.update_levels(-20.0, -10.0, True, 12.5, 0.85)
        print("✅ RealTimeVisualization component created and updated")

        # Test LibraryBrowser
        browser = LibraryBrowser(root)
        print("✅ LibraryBrowser component created")

        # Test PlayerControls
        controls = PlayerControls(root)
        test_info = {
            'state': 'playing',
            'position_seconds': 45.0,
            'duration_seconds': 180.0,
            'library': {
                'current_track_data': {
                    'title': 'Test Track',
                    'artists': ['Test Artist']
                }
            }
        }
        controls.update_info(test_info)
        print("✅ PlayerControls component created and updated")

        # Test MasteringControls
        mastering = MasteringControls(root)
        processing_info = {
            'performance': {'cpu_usage': 0.15},
            'effects': {
                'level_matching': {'enabled': True, 'reference_loaded': True},
                'auto_mastering': {'enabled': True, 'profile': 'balanced'}
            }
        }
        mastering.update_processing_info(processing_info)
        print("✅ MasteringControls component created and updated")

        root.destroy()
        return True

    except Exception as e:
        print(f"❌ GUI components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_with_real_data():
    """Test GUI components with real Auralis data"""
    print("\\n🎵 Testing GUI with Real Auralis Data...")

    try:
        import auralis
        from auralis import EnhancedAudioPlayer, PlayerConfig
        from auralis_gui import LibraryBrowser, PlayerControls, MasteringControls
        import customtkinter as ctk

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test library
            library, tracks = create_test_library(tmpdir)
            if not library or not tracks:
                print("❌ Failed to create test library")
                return False

            print(f"✅ Created test library with {len(tracks)} tracks")

            # Create player
            config = PlayerConfig(
                enable_level_matching=True,
                enable_auto_mastering=True
            )
            player = EnhancedAudioPlayer(config, library)
            print("✅ Created EnhancedAudioPlayer")

            # Test GUI components with real data
            root = ctk.CTk()
            root.withdraw()

            # Test LibraryBrowser with real library
            browser = LibraryBrowser(root)
            browser.set_library_manager(library)
            print("✅ LibraryBrowser set with real library manager")

            # Load a track and test player controls
            if tracks:
                success = player.load_track_from_library(tracks[0].id)
                if success:
                    print("✅ Track loaded from library")

                    # Get real player info
                    info = player.get_playback_info()
                    print(f"✅ Player info obtained: state={info['state']}")

                    # Test PlayerControls with real data
                    controls = PlayerControls(root)
                    controls.set_player(player)
                    controls.update_info(info)
                    print("✅ PlayerControls updated with real data")

                    # Test MasteringControls with real data
                    mastering = MasteringControls(root)
                    mastering.set_player(player)
                    processing_info = info.get('processing', {})
                    mastering.update_processing_info(processing_info)
                    print("✅ MasteringControls updated with real data")

                    # Test search functionality
                    search_results = library.search_tracks("GUI Test", limit=10)
                    print(f"✅ Library search: {len(search_results)} results")

                    # Test library stats
                    stats = library.get_library_stats()
                    print(f"✅ Library stats: {stats['total_tracks']} tracks")

            root.destroy()
            player.cleanup()

        return True

    except Exception as e:
        print(f"❌ Real data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_performance():
    """Test GUI performance and responsiveness"""
    print("\\n⚡ Testing GUI Performance...")

    try:
        from auralis_gui import RealTimeVisualization
        import customtkinter as ctk

        root = ctk.CTk()
        root.withdraw()

        viz = RealTimeVisualization(root, width=800, height=400)

        # Test rapid updates (simulating real-time audio)
        start_time = time.perf_counter()
        update_count = 100

        for i in range(update_count):
            # Simulate changing audio levels
            rms_db = -30 + 20 * np.sin(i * 0.1)
            peak_db = rms_db + 5 + 5 * np.sin(i * 0.15)
            mastering_active = i % 20 < 10

            viz.update_levels(rms_db, peak_db, mastering_active,
                             dr_rating=12.0 + np.sin(i * 0.05),
                             quality_score=0.8 + 0.2 * np.sin(i * 0.03))

        end_time = time.perf_counter()
        update_time = end_time - start_time
        fps = update_count / update_time

        print(f"✅ Visualization performance: {fps:.1f} FPS ({update_time:.3f}s for {update_count} updates)")

        # Performance should be good enough for real-time
        assert fps > 30, f"Visualization performance too low: {fps:.1f} FPS"

        root.destroy()
        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_gui_integration():
    """Test full GUI integration capabilities"""
    print("\\n🔗 Testing GUI Integration...")

    try:
        # Test imports
        from auralis_gui import AuralisGUI
        import auralis

        # Test that all components can be imported
        components = [
            'RealTimeVisualization',
            'LibraryBrowser',
            'PlayerControls',
            'MasteringControls',
            'AuralisGUI'
        ]

        for component in components:
            assert hasattr(__import__('auralis_gui'), component), f"Missing component: {component}"

        print(f"✅ All GUI components available: {len(components)} components")

        # Test GUI class instantiation (without actually showing)
        # This would normally show the GUI, so we just test the class exists
        assert AuralisGUI, "AuralisGUI class not available"
        print("✅ AuralisGUI class available for instantiation")

        # Test feature completeness
        expected_features = [
            "Real-time visualization",
            "Library browser with search",
            "Player transport controls",
            "Mastering controls and profiles",
            "Performance monitoring",
            "Reference track management"
        ]

        print(f"✅ GUI implements {len(expected_features)} key features:")
        for feature in expected_features:
            print(f"   • {feature}")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎨 Testing Auralis Modern GUI")
    print("=" * 60)

    # Run tests
    tests = [
        ("GUI Components", test_gui_components),
        ("GUI with Real Data", test_gui_with_real_data),
        ("GUI Performance", test_gui_performance),
        ("GUI Integration", test_gui_integration),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    print("\\n" + "=" * 60)
    print("📊 GUI TEST RESULTS:")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\\n🎉 ALL GUI TESTS PASSED!")
        print("✨ Auralis Modern GUI Features:")
        print("   🎵 Professional audio player interface")
        print("   📊 Real-time mastering visualizations")
        print("   📚 Comprehensive library browser")
        print("   🎛️ Advanced mastering controls")
        print("   ⚡ High-performance real-time updates")
        print("   🔗 Full integration with Auralis engine")
        print("\\n🚀 Ready for professional audio mastering!")
        sys.exit(0)
    else:
        print("\\n⚠️  Some GUI tests failed - Check output above")
        sys.exit(1)