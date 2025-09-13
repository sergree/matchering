# -*- coding: utf-8 -*-

"""
Real-time Stereo Width Control for Matchering Player
Controls stereo imaging using Mid-Side processing
"""

import numpy as np
from typing import Optional, Dict, Any
from threading import Lock

from .basic import lr_to_ms, ms_to_lr, is_stereo, ExponentialSmoother
from ..core.config import PlayerConfig


class StereoProfile:
    """Stores stereo characteristics of a reference track"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = file_path.split('/')[-1] if '/' in file_path else file_path

        # Stereo characteristics
        self.mid_rms: Optional[float] = None
        self.side_rms: Optional[float] = None
        self.stereo_width: Optional[float] = None  # Calculated width factor
        self.correlation: Optional[float] = None  # L/R correlation

        # Metadata
        self.analysis_complete = False

    def to_dict(self) -> dict:
        """Serialize for caching"""
        return {
            'file_path': self.file_path,
            'filename': self.filename,
            'mid_rms': float(self.mid_rms) if self.mid_rms is not None else None,
            'side_rms': float(self.side_rms) if self.side_rms is not None else None,
            'stereo_width': float(self.stereo_width) if self.stereo_width is not None else None,
            'correlation': float(self.correlation) if self.correlation is not None else None,
            'analysis_complete': self.analysis_complete,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StereoProfile':
        """Deserialize from dictionary"""
        profile = cls(data['file_path'])
        profile.filename = data.get('filename', '')
        profile.mid_rms = data.get('mid_rms')
        profile.side_rms = data.get('side_rms')
        profile.stereo_width = data.get('stereo_width')
        profile.correlation = data.get('correlation')
        profile.analysis_complete = data.get('analysis_complete', False)
        return profile


class RealtimeStereoProcessor:
    """Real-time stereo width control processor"""

    def __init__(self, config: PlayerConfig):
        self.config = config
        self.lock = Lock()
        self.enabled = True
        self.bypass_mode = False

        # Stereo processing parameters
        self.width_factor = 1.0  # 1.0 = normal, <1.0 = narrower, >1.0 = wider
        self.target_width = 1.0  # Target width from reference
        self.manual_width = 1.0  # Manual override
        self.use_reference_width = False  # Whether to match reference width

        # Smoothing for width changes
        self.width_smoother = ExponentialSmoother(
            alpha=config.rms_smoothing_alpha * 0.5  # Smoother than level changes
        )

        # Reference profile
        self.reference_profile: Optional[StereoProfile] = None

        # Statistics
        self.chunks_processed = 0
        self.current_correlation = 0.0

    def load_reference(self, reference_file_path: str) -> bool:
        """Load and analyze reference track for stereo characteristics"""
        try:
            print(f"🔊 Analyzing stereo characteristics: {reference_file_path}")
            profile = self._analyze_stereo_profile(reference_file_path)

            if profile and profile.analysis_complete:
                self.reference_profile = profile

                # Set target width based on reference
                if profile.stereo_width is not None:
                    self.target_width = profile.stereo_width

                print(f"✅ Stereo profile loaded:")
                print(f"   Stereo width: {profile.stereo_width:.2f}")
                print(f"   L/R correlation: {profile.correlation:.3f}")
                print(f"   Mid/Side ratio: {profile.mid_rms/max(profile.side_rms, 1e-6):.1f}:1")

                return True

            return False

        except Exception as e:
            print(f"❌ Error loading stereo reference: {e}")
            return False

    def _analyze_stereo_profile(self, reference_file_path: str) -> Optional[StereoProfile]:
        """Analyze reference track for stereo characteristics"""
        try:
            # Import file loader
            from ..utils.file_loader import AudioFileLoader

            # Load reference audio
            loader = AudioFileLoader(
                target_sample_rate=self.config.sample_rate,
                target_channels=2
            )

            reference_audio, sample_rate = loader.load_audio_file(reference_file_path)
            print(f"🔍 Analyzing stereo image ({len(reference_audio)} samples)")

            # Create stereo profile
            profile = StereoProfile(reference_file_path)

            # Convert to Mid-Side for analysis
            mid, side = lr_to_ms(reference_audio)

            # Calculate RMS levels
            from .basic import rms
            profile.mid_rms = rms(mid)
            profile.side_rms = rms(side)

            # Calculate stereo width (side energy relative to mid energy)
            # Width = 1.0 means balanced stereo, <1.0 means narrower, >1.0 means wider
            if profile.mid_rms > 1e-8:
                raw_width = profile.side_rms / profile.mid_rms
                profile.stereo_width = np.clip(raw_width, 0.1, 2.0)  # Reasonable range
            else:
                profile.stereo_width = 1.0

            # Calculate L/R correlation
            left = reference_audio[:, 0]
            right = reference_audio[:, 1]
            correlation_matrix = np.corrcoef(left, right)
            profile.correlation = correlation_matrix[0, 1] if correlation_matrix.size > 1 else 1.0

            profile.analysis_complete = True

            return profile

        except Exception as e:
            print(f"❌ Error analyzing stereo profile: {e}")
            return None

    def process_chunk(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Process audio chunk with stereo width control"""
        if not self.enabled or self.bypass_mode:
            return audio_chunk

        if not is_stereo(audio_chunk):
            return audio_chunk

        try:
            with self.lock:
                # Convert to Mid-Side
                mid, side = lr_to_ms(audio_chunk)

                # Determine target width
                if self.use_reference_width and self.reference_profile:
                    target = self.target_width
                else:
                    target = self.manual_width

                # Smooth width changes
                current_width = self.width_smoother.update(target)

                # Apply width control by scaling the side channel
                # Width < 1.0: Reduce side (narrower stereo)
                # Width > 1.0: Boost side (wider stereo)
                processed_side = side * current_width

                # Safety limiting to prevent excessive width
                if current_width > 1.5:
                    # Gentle compression for very wide settings
                    processed_side = np.tanh(processed_side) * 0.9

                # Convert back to L/R
                processed_audio = ms_to_lr(mid, processed_side)

                # Update statistics
                self.chunks_processed += 1
                self.current_correlation = self._calculate_correlation(processed_audio)
                self.width_factor = current_width

                return processed_audio.astype(audio_chunk.dtype)

        except Exception as e:
            print(f"⚠️ Error in stereo processing: {e}")
            return audio_chunk

    def _calculate_correlation(self, audio_chunk: np.ndarray) -> float:
        """Calculate L/R correlation for current chunk"""
        try:
            left = audio_chunk[:, 0]
            right = audio_chunk[:, 1]

            # Calculate correlation coefficient
            if len(left) > 1:
                correlation_matrix = np.corrcoef(left, right)
                if correlation_matrix.size > 1:
                    return float(correlation_matrix[0, 1])

            return 1.0  # Default to perfect correlation

        except:
            return 1.0

    def set_width(self, width: float):
        """Set manual stereo width (0.0 = mono, 1.0 = normal, 2.0 = very wide)"""
        with self.lock:
            self.manual_width = np.clip(width, 0.0, 2.0)
            self.use_reference_width = False

    def set_reference_matching(self, enabled: bool):
        """Enable/disable automatic width matching to reference"""
        with self.lock:
            self.use_reference_width = enabled

    def get_current_width(self) -> float:
        """Get current effective width factor"""
        return self.width_factor

    def set_enabled(self, enabled: bool):
        """Enable or disable stereo processing"""
        with self.lock:
            self.enabled = enabled
            if not enabled:
                self.width_smoother.reset()

    def set_bypass(self, bypass: bool):
        """Set bypass mode"""
        with self.lock:
            self.bypass_mode = bypass
            if bypass:
                self.width_smoother.reset()

    def reset(self):
        """Reset all processing state"""
        with self.lock:
            self.width_smoother.reset()
            self.chunks_processed = 0
            self.current_correlation = 0.0

    def get_current_stats(self) -> dict:
        """Get current stereo processing statistics"""
        stats = {
            'enabled': self.enabled,
            'bypass_mode': self.bypass_mode,
            'width_factor': self.width_factor,
            'manual_width': self.manual_width,
            'target_width': self.target_width,
            'use_reference_width': self.use_reference_width,
            'current_correlation': self.current_correlation,
            'chunks_processed': self.chunks_processed,
            'reference_loaded': self.reference_profile is not None,
        }

        if self.reference_profile:
            stats.update({
                'reference_filename': self.reference_profile.filename,
                'reference_width': self.reference_profile.stereo_width,
                'reference_correlation': self.reference_profile.correlation,
            })

        return stats