#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate Test Audio Files for Matchering Player Demo
Creates sample target and reference tracks for testing
"""

import numpy as np
import soundfile as sf
import os

def generate_test_audio():
    """Generate test audio files for demo"""

    # Audio parameters
    sample_rate = 44100
    duration = 10.0  # 10 seconds
    samples = int(duration * sample_rate)

    print("🎵 Generating test audio files...")

    # === TARGET TRACK (quiet, home recording style) ===
    print("Creating target track (quiet home recording)...")

    # Generate a simple melody with some harmonics
    t = np.linspace(0, duration, samples)

    # Base frequency (A4 = 440 Hz)
    freq1 = 440.0  # A4
    freq2 = 554.37  # C#5 (major third)
    freq3 = 659.25  # E5 (perfect fifth)

    # Create a simple chord progression with some variation
    target_left = (
        0.3 * np.sin(2 * np.pi * freq1 * t) +
        0.2 * np.sin(2 * np.pi * freq2 * t) +
        0.15 * np.sin(2 * np.pi * freq3 * t) +
        0.1 * np.sin(2 * np.pi * freq1 * 2 * t)  # Harmonic
    )

    # Slightly different right channel (stereo effect)
    target_right = (
        0.25 * np.sin(2 * np.pi * freq1 * t * 1.001) +  # Slight detune
        0.22 * np.sin(2 * np.pi * freq2 * t * 1.002) +
        0.12 * np.sin(2 * np.pi * freq3 * t * 0.999) +
        0.08 * np.sin(2 * np.pi * freq1 * 2 * t)
    )

    # Add some amplitude variation (dynamics)
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t)  # Slow tremolo
    target_left *= envelope
    target_right *= envelope

    # Make it quiet (home recording style) - around -24 dB RMS
    target_left *= 0.05
    target_right *= 0.05

    # Add some noise (home recording character)
    noise_level = 0.002
    target_left += noise_level * np.random.normal(0, 1, len(target_left))
    target_right += noise_level * np.random.normal(0, 1, len(target_right))

    # Combine to stereo
    target_audio = np.column_stack([target_left, target_right]).astype(np.float32)

    # === REFERENCE TRACK (loud, professional master) ===
    print("Creating reference track (loud professional master)...")

    # Similar harmonic content but different arrangement
    freq1_ref = 440.0 * 1.5  # Up a fifth
    freq2_ref = 554.37 * 1.5
    freq3_ref = 659.25 * 1.5

    ref_left = (
        0.4 * np.sin(2 * np.pi * freq1_ref * t) +
        0.35 * np.sin(2 * np.pi * freq2_ref * t) +
        0.3 * np.sin(2 * np.pi * freq3_ref * t) +
        0.2 * np.sin(2 * np.pi * freq1_ref * 0.5 * t)  # Sub-harmonic
    )

    ref_right = (
        0.38 * np.sin(2 * np.pi * freq1_ref * t * 0.998) +  # Slight detune
        0.33 * np.sin(2 * np.pi * freq2_ref * t * 1.003) +
        0.28 * np.sin(2 * np.pi * freq3_ref * t * 0.997) +
        0.18 * np.sin(2 * np.pi * freq1_ref * 0.5 * t)
    )

    # Professional level dynamics
    envelope_ref = 0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t)  # Subtle dynamics
    ref_left *= envelope_ref
    ref_right *= envelope_ref

    # Make it loud (professional master) - around -12 dB RMS
    ref_left *= 0.25
    ref_right *= 0.25

    # Apply gentle limiting/compression (simulated)
    ref_left = np.tanh(ref_left * 1.2) * 0.8
    ref_right = np.tanh(ref_right * 1.2) * 0.8

    # Combine to stereo
    reference_audio = np.column_stack([ref_left, ref_right]).astype(np.float32)

    # === SAVE FILES ===
    print("Saving audio files...")

    # Create test_files directory
    os.makedirs("test_files", exist_ok=True)

    # Save target track
    target_path = "test_files/target_demo.wav"
    sf.write(target_path, target_audio, sample_rate)
    print(f"✅ Saved target track: {target_path}")

    # Save reference track
    reference_path = "test_files/reference_master.wav"
    sf.write(reference_path, reference_audio, sample_rate)
    print(f"✅ Saved reference track: {reference_path}")

    # === ANALYSIS ===
    print("\n📊 Audio Analysis:")

    # Calculate RMS levels
    target_rms = np.sqrt(np.mean(target_audio**2))
    target_rms_db = 20 * np.log10(target_rms)

    reference_rms = np.sqrt(np.mean(reference_audio**2))
    reference_rms_db = 20 * np.log10(reference_rms)

    print(f"Target RMS: {target_rms_db:.1f} dB (quiet home recording)")
    print(f"Reference RMS: {reference_rms_db:.1f} dB (loud professional master)")
    print(f"Difference: {reference_rms_db - target_rms_db:.1f} dB")

    print(f"\n✨ Expected Result:")
    print(f"When you load both files and enable level matching,")
    print(f"the target should be boosted by ~{reference_rms_db - target_rms_db:.1f} dB in real-time!")

    print(f"\n🎯 Demo Instructions:")
    print(f"1. Run: python demo_matchering_player.py")
    print(f"2. Load '{target_path}' as target")
    print(f"3. Load '{reference_path}' as reference")
    print(f"4. Press play and toggle 'Level Matching' to hear the effect!")

if __name__ == "__main__":
    generate_test_audio()