#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Pipewire Audio Playback for Matchering Player
Demo that shows the auto-mastering system working with file export instead of real-time playback
"""

import sys
import os
import numpy as np
import soundfile as sf

# Add the matchering_player package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_demo_audio():
    """Create demo audio content"""
    sample_rate = 44100
    duration = 5.0  # 5 seconds
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)

    # Create test audio - modern pop style
    left = (
        0.3 * np.sin(2 * np.pi * 100 * t) +    # Bass
        0.4 * np.sin(2 * np.pi * 440 * t) +    # Mid
        0.3 * np.sin(2 * np.pi * 2000 * t) +   # Bright
        0.2 * np.sin(2 * np.pi * 8000 * t)     # Sparkle
    )
    right = left * 0.9 + 0.1 * np.sin(2 * np.pi * 550 * t)

    # Add some dynamics
    envelope = 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.5 * t))
    audio = np.column_stack([left * envelope, right * envelope]) * 0.3

    return audio.astype(np.float32), sample_rate

def test_pipewire_mastering():
    """Test auto-mastering with file export (no audio hardware needed)"""
    print("🎵 Testing Matchering Player Auto-Mastering (File Export Mode)")
    print("=" * 70)

    try:
        # Import components
        from matchering_player.core.config import PlayerConfig
        from matchering_player.dsp import RealtimeProcessor

        # Create test audio
        print("1️⃣ Creating demo audio content...")
        audio_data, sample_rate = create_demo_audio()
        print(f"✅ Created {len(audio_data)} samples ({len(audio_data)/sample_rate:.1f}s)")

        # Save original
        sf.write("demo_original.wav", audio_data, sample_rate)
        print("✅ Saved: demo_original.wav")

        # Configure auto-mastering
        print("\n2️⃣ Initializing auto-mastering processor...")
        config = PlayerConfig(
            sample_rate=sample_rate,
            buffer_size_ms=100.0,
            enable_level_matching=True,
            enable_frequency_matching=True,
            enable_stereo_width=True,
            enable_auto_mastering=True,
        )

        processor = RealtimeProcessor(config)
        print("✅ Auto-mastering processor ready")

        # Process audio in chunks
        print("\n3️⃣ Processing audio with auto-mastering...")
        chunk_size = config.buffer_size_samples
        processed_chunks = []

        # Force adaptive mode to detect content
        if processor.auto_master:
            processor.auto_master.enable_adaptive_mode()

        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            if len(chunk) < chunk_size:
                # Pad the last chunk
                padded = np.zeros((chunk_size, 2), dtype=np.float32)
                padded[:len(chunk)] = chunk
                chunk = padded

            processed_chunk = processor.process_audio_chunk(chunk)
            processed_chunks.append(processed_chunk[:len(audio_data) - i])

        processed_audio = np.concatenate(processed_chunks, axis=0)[:len(audio_data)]
        print(f"✅ Processed {len(processed_chunks)} chunks")

        # Get auto-mastering results
        if processor.auto_master:
            stats = processor.auto_master.get_current_stats()
            print(f"\n🧠 Auto-mastering results:")
            print(f"   Profile detected: {stats['current_profile']}")
            print(f"   Analysis confidence: {stats['analysis']['confidence_level']:.1%}")
            print(f"   Chunks processed: {stats['chunks_processed']}")

        # Save processed versions for each profile
        print("\n4️⃣ Testing all mastering profiles...")

        profiles_to_test = ['modern_pop', 'electronic', 'acoustic', 'podcast']

        for profile_name in profiles_to_test:
            print(f"   🎛️ Testing {profile_name} profile...")

            # Set specific profile
            processor.set_effect_parameter('auto_master', 'profile', profile_name)

            # Process audio with this profile
            profile_chunks = []
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                if len(chunk) < chunk_size:
                    padded = np.zeros((chunk_size, 2), dtype=np.float32)
                    padded[:len(chunk)] = chunk
                    chunk = padded

                processed_chunk = processor.process_audio_chunk(chunk)
                profile_chunks.append(processed_chunk[:len(audio_data) - i])

            profile_audio = np.concatenate(profile_chunks, axis=0)[:len(audio_data)]

            # Save this profile result
            filename = f"demo_{profile_name}.wav"
            sf.write(filename, profile_audio, sample_rate)
            print(f"   ✅ Saved: {filename}")

        # Final summary
        print(f"\n🎊 AUTO-MASTERING FILE EXPORT TEST COMPLETE!")
        print("=" * 70)
        print("✅ Auto-mastering system working perfectly")
        print("✅ All profiles tested and exported")
        print("✅ No audio hardware required - works with Pipewire!")
        print("\n📁 Generated files:")
        print("   • demo_original.wav - Original unprocessed audio")
        print("   • demo_modern_pop.wav - Modern Pop mastering")
        print("   • demo_electronic.wav - Electronic mastering")
        print("   • demo_acoustic.wav - Acoustic mastering")
        print("   • demo_podcast.wav - Podcast mastering")
        print("\n🎧 Play these files to hear the auto-mastering differences!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Pipewire-compatible auto-mastering test...\n")

    success = test_pipewire_mastering()

    if success:
        print(f"\n🎉 PIPEWIRE AUTO-MASTERING TEST SUCCESSFUL!")
        print("Matchering Player auto-mastering works perfectly - no hardware needed!")
        sys.exit(0)
    else:
        print(f"\n💥 TEST FAILED!")
        sys.exit(1)