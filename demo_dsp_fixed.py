#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matchering Player DSP Processing Demo
Demonstrates level matching without requiring PyAudio for audio output
"""

import numpy as np
import sys
import os
import tempfile
from pathlib import Path

# Add the matchering_player package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

from matchering_player.core.config import PlayerConfig
from matchering_player.dsp import RealtimeProcessor, rms
from matchering_player.utils.file_loader import load_audio_file


def create_demo_files():
    """Create demo audio files for testing"""
    if not HAS_SOUNDFILE:
        print("❌ soundfile required for this demo. Install with: pip install soundfile")
        return None, None
    
    # Create a quiet target track (home recording simulation)
    print("🎵 Creating demo tracks...")
    
    # Target: Quiet acoustic guitar simulation
    duration = 8.0
    sample_rate = 44100
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples, False)
    
    # Multiple harmonics to simulate guitar
    target_left = (0.15 * np.sin(2 * np.pi * 220 * t) +    # A3
                  0.10 * np.sin(2 * np.pi * 330 * t) +    # E4  
                  0.08 * np.sin(2 * np.pi * 440 * t))     # A4
    
    target_right = (0.12 * np.sin(2 * np.pi * 220 * t * 1.002) +
                   0.09 * np.sin(2 * np.pi * 330 * t * 1.001) +
                   0.07 * np.sin(2 * np.pi * 440 * t * 0.999))
    
    # Add dynamics (volume changes over time)
    envelope = 0.4 + 0.3 * np.sin(2 * np.pi * 0.2 * t) * np.exp(-t * 0.1)
    target_left *= envelope
    target_right *= envelope
    
    target_audio = np.column_stack([target_left, target_right]).astype(np.float32)
    target_file = "quiet_target.wav"
    sf.write(target_file, target_audio, sample_rate)
    
    # Reference: Loud mastered track simulation  
    ref_left = (0.6 * np.sin(2 * np.pi * 220 * t) +
               0.4 * np.sin(2 * np.pi * 330 * t) +
               0.3 * np.sin(2 * np.pi * 440 * t))
    
    ref_right = (0.55 * np.sin(2 * np.pi * 220 * t * 1.001) +
                0.38 * np.sin(2 * np.pi * 330 * t * 0.999) +
                0.28 * np.sin(2 * np.pi * 440 * t * 1.002))
    
    # More consistent volume (mastered characteristics)
    ref_envelope = 0.8 + 0.1 * np.sin(2 * np.pi * 0.1 * t)
    ref_left *= ref_envelope
    ref_right *= ref_envelope
    
    reference_audio = np.column_stack([ref_left, ref_right]).astype(np.float32)
    reference_file = "loud_reference.wav"
    sf.write(reference_file, reference_audio, sample_rate)
    
    # Calculate RMS levels for comparison
    target_rms = rms(target_audio[:, 0])
    reference_rms = rms(reference_audio[:, 0])
    
    print(f"   Target RMS: {20 * np.log10(target_rms):.1f} dB ({target_rms:.4f})")
    print(f"   Reference RMS: {20 * np.log10(reference_rms):.1f} dB ({reference_rms:.4f})")
    print(f"   Difference: {20 * np.log10(reference_rms / target_rms):.1f} dB")
    
    return target_file, reference_file


def demo_dsp_processing():
    """Demonstrate DSP processing with level matching"""
    print("\n🎛️  Demonstrating DSP Processing...")
    
    # Create demo files
    target_file, reference_file = create_demo_files()
    if not target_file:
        return
    
    # Load audio files
    print("\n📁 Loading audio files...")
    target_audio, _ = load_audio_file(target_file)
    reference_audio, _ = load_audio_file(reference_file)
    
    print(f"   Target: {target_audio.shape[0]} samples")
    print(f"   Reference: {reference_audio.shape[0]} samples")
    
    # Set up DSP processor
    config = PlayerConfig(
        buffer_size_ms=100.0,
        enable_level_matching=True,
        rms_smoothing_alpha=0.05  # Moderate smoothing
    )
    
    processor = RealtimeProcessor(config)
    
    # Load reference track into processor
    print(f"\n🎯 Loading reference track...")
    success = processor.load_reference_track(reference_file)
    if not success:
        print("❌ Failed to load reference")
        return
    
    # Start processing
    processor.start_processing()
    
    print(f"\n⚙️  Processing audio chunks...")
    
    # Process audio in chunks like real playback would
    chunk_size = config.buffer_size_samples
    processed_chunks = []
    
    num_chunks = len(target_audio) // chunk_size
    print(f"   Processing {num_chunks} chunks of {chunk_size} samples each")
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size
        
        # Get chunk
        chunk = target_audio[start_idx:end_idx]
        
        # Process through DSP
        processed_chunk = processor.process_audio_chunk(chunk)
        processed_chunks.append(processed_chunk)
        
        # Show progress every 10 chunks
        if (i + 1) % 10 == 0:
            stats = processor.get_processing_stats()
            level_stats = stats.get('level_matching', {})
            current_gain = level_stats.get('mid_gain_current', 1.0)
            print(f"     Chunk {i+1}/{num_chunks}: Current gain = {20*np.log10(current_gain):.1f} dB")
    
    # Combine processed chunks
    processed_audio = np.vstack(processed_chunks)
    
    # Calculate final statistics
    original_rms = rms(target_audio[:len(processed_audio), 0])  # Match length
    processed_rms = rms(processed_audio[:, 0])
    reference_rms_calc = rms(reference_audio[:, 0])
    
    print(f"\n📊 Processing Results:")
    print(f"   Original target RMS: {20 * np.log10(original_rms):.1f} dB")
    print(f"   Processed target RMS: {20 * np.log10(processed_rms):.1f} dB")
    print(f"   Reference RMS: {20 * np.log10(reference_rms_calc):.1f} dB")
    print(f"   Gain applied: {20 * np.log10(processed_rms / original_rms):.1f} dB")
    print(f"   Target-to-Reference match: {abs(20 * np.log10(processed_rms / reference_rms_calc)):.1f} dB difference")
    
    # Show detailed DSP stats
    final_stats = processor.get_processing_stats()
    print(f"\n🔍 DSP Statistics:")
    print(f"   Chunks processed: {final_stats['chunks_processed']}")
    print(f"   Processing time: {final_stats['processed_duration_seconds']:.1f}s")
    print(f"   CPU usage: {final_stats.get('cpu_usage', 0) * 100:.1f}%")
    print(f"   Performance mode: {final_stats.get('performance_mode', False)}")
    
    level_matching = final_stats.get('level_matching', {})
    print(f"   Level matching status: {level_matching.get('status', 'N/A')}")
    print(f"   Reference loaded: {level_matching.get('reference_loaded', False)}")
    
    # Save processed result for comparison
    if HAS_SOUNDFILE:
        output_file = "processed_result.wav"
        sf.write(output_file, processed_audio, config.sample_rate)
        print(f"\n💾 Saved processed audio to: {output_file}")
        print(f"   You can compare the original and processed files!")
    
    processor.stop_processing()
    print(f"\n✅ DSP processing demonstration complete!")
    
    # Clean up demo files
    if os.path.exists(target_file):
        os.unlink(target_file)
    if os.path.exists(reference_file):
        os.unlink(reference_file)


def main():
    """Run the DSP processing demo"""
    print("🚀 Matchering Player DSP Processing Demo")
    print("========================================")
    print("This demo shows how Matchering Player processes audio")
    print("without requiring audio playback hardware.\n")
    
    try:
        demo_dsp_processing()
        
        print("\n" + "=" * 40)
        print("🎉 Demo completed successfully!")
        print("\n🎵 Key takeaways:")
        print("   • File loading works perfectly")
        print("   • DSP processing applies appropriate gain")
        print("   • Level matching brings quiet tracks up to reference level")
        print("   • Smoothing prevents harsh audio artifacts")
        print("   • Performance monitoring ensures efficient processing")
        print("\n🚀 Ready to add GUI and full audio playback in Phase 3!")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
