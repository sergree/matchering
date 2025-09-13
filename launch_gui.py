#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matchering Player GUI Launcher
Simple launcher for the Matchering Player GUI application
"""

import sys
import os

# Add the matchering_player package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Launch the Matchering Player GUI"""
    print("🚀 Starting Matchering Player GUI...")
    
    try:
        from matchering_player.ui.main_window import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install soundfile numpy scipy")
        print("  (PyAudio optional for audio playback)")
        return False
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
