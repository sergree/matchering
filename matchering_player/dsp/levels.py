# -*- coding: utf-8 -*-

"""
Realtime Level Matching for Matchering Player
Adapted from Matchering 2.0's level analysis for streaming chunks
"""

import numpy as np
from typing import Optional, Tuple
import json
import os
from pathlib import Path

from .basic import (
    rms, amplify, lr_to_ms, ms_to_lr, 
    ExponentialSmoother, is_stereo
)
from ..core.config import PlayerConfig


class ReferenceProfile:
    """Stores analyzed characteristics of a reference track"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = Path(file_path).stem
        
        # Level characteristics
        self.target_rms_mid = None
        self.target_rms_side = None
        self.peak_amplitude = None
        self.dynamic_range = None
        
        # Metadata
        self.sample_rate = None
        self.duration = None
        self.analysis_complete = False
        
    def to_dict(self) -> dict:
        """Serialize to dictionary for caching"""
        return {
            'file_path': self.file_path,
            'filename': self.filename,
            'target_rms_mid': float(self.target_rms_mid) if self.target_rms_mid is not None else None,
            'target_rms_side': float(self.target_rms_side) if self.target_rms_side is not None else None,
            'peak_amplitude': float(self.peak_amplitude) if self.peak_amplitude is not None else None,
            'dynamic_range': float(self.dynamic_range) if self.dynamic_range is not None else None,
            'sample_rate': int(self.sample_rate) if self.sample_rate is not None else None,
            'duration': float(self.duration) if self.duration is not None else None,
            'analysis_complete': self.analysis_complete,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReferenceProfile':
        """Deserialize from dictionary"""
        profile = cls(data['file_path'])
        profile.filename = data['filename']
        profile.target_rms_mid = data.get('target_rms_mid')
        profile.target_rms_side = data.get('target_rms_side')
        profile.peak_amplitude = data.get('peak_amplitude')
        profile.dynamic_range = data.get('dynamic_range')
        profile.sample_rate = data.get('sample_rate')
        profile.duration = data.get('duration')
        profile.analysis_complete = data.get('analysis_complete', False)
        return profile


class ReferenceCache:
    """Manages caching of reference track analyses"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / '.matchering_player' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'references.json'
        self._cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load reference cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_cache(self):
        """Save reference cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save reference cache: {e}")
    
    def get_reference(self, file_path: str) -> Optional[ReferenceProfile]:
        """Get cached reference profile"""
        key = str(Path(file_path).resolve())
        if key in self._cache:
            return ReferenceProfile.from_dict(self._cache[key])
        return None
    
    def set_reference(self, profile: ReferenceProfile):
        """Cache reference profile"""
        key = str(Path(profile.file_path).resolve())
        self._cache[key] = profile.to_dict()
        self._save_cache()
    
    def clear_cache(self):
        """Clear all cached references"""
        self._cache = {}
        self._save_cache()


class RealtimeLevelMatcher:
    """
    Realtime level matching engine
    Adapts Matchering's RMS analysis for streaming audio chunks
    """
    
    def __init__(self, config: PlayerConfig):
        self.config = config
        
        # Reference management
        self.reference_profile: Optional[ReferenceProfile] = None
        self.reference_cache = ReferenceCache(config.reference_cache_dir)
        
        # Smoothing for realtime adjustments
        self.mid_gain_smoother = ExponentialSmoother(config.rms_smoothing_alpha)
        self.side_gain_smoother = ExponentialSmoother(config.rms_smoothing_alpha)
        
        # Running statistics for adaptive reference learning
        self.chunk_count = 0
        self.rms_history_mid = []
        self.rms_history_side = []
        self.max_history_length = 1000  # Keep last ~100 seconds at 100ms chunks
        
        # Processing state
        self.enabled = True
        self.bypass_mode = False
        
    def load_reference(self, reference_file_path: str) -> bool:
        """
        Load and analyze reference track
        Returns True if successful, False otherwise
        """
        try:
            # Try to load from cache first
            cached_profile = self.reference_cache.get_reference(reference_file_path)
            if cached_profile and cached_profile.analysis_complete:
                self.reference_profile = cached_profile
                print(f"Loaded cached reference: {cached_profile.filename}")
                return True
            
            # Need to analyze the reference track
            print(f"🔍 Analyzing reference track: {Path(reference_file_path).name}")
            self.reference_profile = self._analyze_reference_track(reference_file_path)
            if not self.reference_profile:
                return False

            print(f"✅ Reference analysis complete:")
            print(f"   Mid RMS: {self.reference_profile.target_rms_mid:.1f} dB")
            print(f"   Side RMS: {self.reference_profile.target_rms_side:.1f} dB")
            
            # Cache the profile
            self.reference_cache.set_reference(self.reference_profile)
            return True
            
        except Exception as e:
            print(f"Error loading reference: {e}")
            return False
    
    def _calculate_target_gain(self, current_rms: float, target_rms: float) -> float:
        """Calculate gain needed to match target RMS"""
        if current_rms < self.config.min_value:
            return 1.0  # Avoid division by zero
        
        # Convert dB to linear (target_rms is in dB, current_rms is linear)
        target_linear = 10 ** (target_rms / 20.0)
        return target_linear / current_rms
    
    def process_chunk(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Process a single audio chunk with level matching
        
        Args:
            audio_chunk: Stereo audio chunk (shape: [samples, 2])
            
        Returns:
            Processed audio chunk with level matching applied
        """
        if not self.enabled or self.bypass_mode or self.reference_profile is None:
            return audio_chunk
        
        if not is_stereo(audio_chunk):
            print("Warning: Level matching requires stereo input")
            return audio_chunk
        
        try:
            # Convert to Mid-Side for processing
            mid, side = lr_to_ms(audio_chunk)
            
            # Calculate RMS for this chunk
            current_rms_mid = rms(mid)
            current_rms_side = rms(side)
            
            # Update running statistics
            self.chunk_count += 1
            self.rms_history_mid.append(current_rms_mid)
            self.rms_history_side.append(current_rms_side)
            
            # Limit history length
            if len(self.rms_history_mid) > self.max_history_length:
                self.rms_history_mid.pop(0)
                self.rms_history_side.pop(0)
            
            # Calculate target gains
            mid_gain = self._calculate_target_gain(
                current_rms_mid, 
                self.reference_profile.target_rms_mid
            )
            side_gain = self._calculate_target_gain(
                current_rms_side,
                self.reference_profile.target_rms_side
            )
            
            # Apply smoothing to prevent audio artifacts
            smooth_mid_gain = self.mid_gain_smoother.update(mid_gain)
            smooth_side_gain = self.side_gain_smoother.update(side_gain)
            
            # Limit gain changes for safety
            max_gain = 4.0  # Max +12dB boost
            min_gain = 0.1  # Max -20dB cut
            
            smooth_mid_gain = np.clip(smooth_mid_gain, min_gain, max_gain)
            smooth_side_gain = np.clip(smooth_side_gain, min_gain, max_gain)
            
            # Apply gain adjustments
            processed_mid = amplify(mid, smooth_mid_gain)
            processed_side = amplify(side, smooth_side_gain)
            
            # Convert back to L/R
            processed_audio = ms_to_lr(processed_mid, processed_side)
            
            return processed_audio.astype(audio_chunk.dtype)
            
        except Exception as e:
            print(f"Error in level matching: {e}")
            return audio_chunk
    
    def get_current_stats(self) -> dict:
        """Get current processing statistics"""
        if not self.rms_history_mid:
            return {'status': 'no_data'}
        
        recent_mid = np.mean(self.rms_history_mid[-10:])  # Last 1 second
        recent_side = np.mean(self.rms_history_side[-10:])
        
        stats = {
            'status': 'active' if self.enabled and not self.bypass_mode else 'bypassed',
            'reference_loaded': self.reference_profile is not None,
            'current_rms_mid_db': 20 * np.log10(max(recent_mid, self.config.min_value)),
            'current_rms_side_db': 20 * np.log10(max(recent_side, self.config.min_value)),
            'chunks_processed': self.chunk_count,
            'mid_gain_current': self.mid_gain_smoother.current_value or 1.0,
            'side_gain_current': self.side_gain_smoother.current_value or 1.0,
        }
        
        if self.reference_profile:
            stats.update({
                'target_rms_mid_db': self.reference_profile.target_rms_mid,
                'target_rms_side_db': self.reference_profile.target_rms_side,
                'reference_name': self.reference_profile.filename,
            })
        
        return stats
    
    def set_enabled(self, enabled: bool):
        """Enable or disable level matching"""
        self.enabled = enabled
        if not enabled:
            # Reset smoothers when disabled
            self.mid_gain_smoother.reset()
            self.side_gain_smoother.reset()
    
    def set_bypass(self, bypass: bool):
        """Set bypass mode (temporary disable without resetting state)"""
        self.bypass_mode = bypass
    
    def reset_smoothing(self):
        """Reset gain smoothing (useful when changing references)"""
        self.mid_gain_smoother.reset()
        self.side_gain_smoother.reset()
        self.chunk_count = 0
        self.rms_history_mid.clear()
        self.rms_history_side.clear()

    def _analyze_reference_track(self, reference_file_path: str) -> Optional[ReferenceProfile]:
        """
        Analyze a reference track to extract target levels

        Args:
            reference_file_path: Path to reference audio file

        Returns:
            ReferenceProfile with analysis results, or None if failed
        """
        try:
            # Import the file loader here to avoid circular imports
            from ..utils.file_loader import AudioFileLoader

            # Create file loader
            loader = AudioFileLoader(
                target_sample_rate=self.config.sample_rate,
                target_channels=2
            )

            # Load the reference audio file
            print(f"📁 Loading reference file...")
            reference_audio, sample_rate = loader.load_audio_file(reference_file_path)

            print(f"🎵 Analyzing {len(reference_audio)} samples ({len(reference_audio)/sample_rate:.1f}s)")

            # Create reference profile
            profile = ReferenceProfile(reference_file_path)

            # Convert entire track to Mid-Side for analysis
            mid, side = lr_to_ms(reference_audio)

            # Calculate overall RMS levels
            rms_mid = rms(mid)
            rms_side = rms(side)

            # Convert to dB (with minimum floor to prevent log(0))
            min_value = 1e-8
            profile.target_rms_mid = 20 * np.log10(max(rms_mid, min_value))
            profile.target_rms_side = 20 * np.log10(max(rms_side, min_value))

            # Calculate additional statistics
            profile.peak_amplitude = np.max(np.abs(reference_audio))
            profile.dynamic_range = profile.peak_amplitude - rms(reference_audio.flatten())

            # Analyze chunks for dynamic characteristics
            chunk_size = self.config.buffer_size_samples
            chunk_rms_values = []

            for i in range(0, len(reference_audio) - chunk_size, chunk_size):
                chunk = reference_audio[i:i + chunk_size]
                chunk_rms_mid, _ = lr_to_ms(chunk)
                chunk_rms = rms(chunk_rms_mid)
                if chunk_rms > min_value:  # Filter out silence
                    chunk_rms_values.append(chunk_rms)

            # Calculate dynamic characteristics
            if chunk_rms_values:
                chunk_rms_array = np.array(chunk_rms_values)
                profile.rms_variance = np.var(chunk_rms_array)
                profile.rms_percentiles = {
                    'p10': np.percentile(chunk_rms_array, 10),
                    'p50': np.percentile(chunk_rms_array, 50),
                    'p90': np.percentile(chunk_rms_array, 90),
                }

            profile.analysis_complete = True

            # Log analysis results
            print(f"📊 Reference analysis results:")
            print(f"   Overall Mid RMS: {profile.target_rms_mid:.1f} dB")
            print(f"   Overall Side RMS: {profile.target_rms_side:.1f} dB")
            print(f"   Peak amplitude: {profile.peak_amplitude:.3f}")
            print(f"   Dynamic range: {profile.dynamic_range:.3f}")
            if hasattr(profile, 'rms_variance'):
                print(f"   RMS variance: {profile.rms_variance:.6f}")

            return profile

        except Exception as e:
            print(f"❌ Error analyzing reference track: {e}")
            import traceback
            traceback.print_exc()
            return None
