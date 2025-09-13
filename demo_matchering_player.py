#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matchering Player MVP Demo
Test script to launch the complete audio player with GUI
"""

import sys
import os

# Add the matchering_player package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Launch Matchering Player GUI"""
    print("🚀 Starting Matchering Player MVP Demo")
    print("="*50)

    try:
        from matchering_player.ui.main_window import MatcheringPlayerGUI

        # Create and run GUI
        app = MatcheringPlayerGUI()

        print("✅ GUI initialized successfully!")
        print("\nUsage Instructions:")
        print("1. Click 'File -> Load Target Track' to load an audio file to process")
        print("2. Click 'File -> Load Reference Track' to load a reference for matching")
        print("3. Use the playback controls to play/pause/stop")
        print("4. Toggle 'Level Matching' to hear the effect in real-time")
        print("5. Watch the status area for processing information")
        print("\n🎵 Starting GUI... Close the window to exit.")
        print("="*50)

        # Start GUI main loop
        app.run()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all dependencies are installed:")
        print("- pyaudio: pip install pyaudio")
        print("- soundfile: pip install soundfile")
        print("- librosa: pip install librosa")
        return 1

    except Exception as e:
        print(f"❌ Error starting Matchering Player: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("👋 Matchering Player demo completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())