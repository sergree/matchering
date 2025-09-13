# -*- coding: utf-8 -*-

"""
Intelligent Auto-Mastering System for Matchering Player
Automatically applies mastering without needing a reference track
"""

import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import json
from threading import Lock

from .basic import rms, lr_to_ms, ms_to_lr, is_stereo, ExponentialSmoother
from ..core.config import PlayerConfig


class AutoMasterProfile(Enum):
    """Auto-mastering profiles for different content types"""
    MODERN_POP = "modern_pop"
    CLASSIC_ROCK = "classic_rock"
    ELECTRONIC = "electronic"
    ACOUSTIC = "acoustic"
    CLASSICAL = "classical"
    PODCAST = "podcast"
    BROADCAST = "broadcast"
    VINTAGE = "vintage"
    ADAPTIVE = "adaptive"  # Automatically detects best profile


class ContentAnalyzer:
    """Analyzes audio content to determine optimal processing"""

    def __init__(self, config: PlayerConfig):
        self.config = config
        self.sample_rate = config.sample_rate

        # Analysis parameters
        self.analysis_window_size = 8192  # For spectral analysis
        self.analysis_buffer = []
        self.buffer_max_size = 50  # About 5 seconds of analysis

        # Content characteristics
        self.detected_genre = AutoMasterProfile.ADAPTIVE
        self.spectral_centroid = 0.0
        self.dynamic_range = 0.0
        self.bass_energy = 0.0
        self.treble_energy = 0.0
        self.stereo_complexity = 0.0
        self.tempo_estimate = 0.0

        # Analysis confidence
        self.analysis_complete = False
        self.confidence_level = 0.0

    def analyze_chunk(self, audio_chunk: np.ndarray):
        """Analyze audio chunk and update content characteristics"""
        if not is_stereo(audio_chunk):
            return

        # Add to analysis buffer
        self.analysis_buffer.append(audio_chunk.copy())
        if len(self.analysis_buffer) > self.buffer_max_size:
            self.analysis_buffer.pop(0)

        # Perform analysis on accumulated data
        if len(self.analysis_buffer) >= 10:  # Need enough data
            self._perform_spectral_analysis()
            self._perform_dynamic_analysis()
            self._perform_stereo_analysis()
            self._detect_content_type()

    def _perform_spectral_analysis(self):
        """Analyze frequency content"""
        try:
            # Concatenate recent chunks for analysis
            analysis_audio = np.vstack(self.analysis_buffer[-20:])  # Last 2 seconds
            mono_audio = np.mean(analysis_audio, axis=1)

            # Compute spectrum
            fft = np.fft.rfft(mono_audio * np.hanning(len(mono_audio)))
            magnitude = np.abs(fft)
            frequencies = np.fft.rfftfreq(len(mono_audio), 1/self.sample_rate)

            # Calculate spectral centroid (brightness indicator)
            if np.sum(magnitude) > 0:
                self.spectral_centroid = np.sum(frequencies * magnitude) / np.sum(magnitude)

            # Analyze frequency bands
            bass_mask = (frequencies >= 20) & (frequencies <= 250)
            mid_mask = (frequencies > 250) & (frequencies <= 4000)
            treble_mask = frequencies > 4000

            total_energy = np.sum(magnitude)
            if total_energy > 0:
                self.bass_energy = np.sum(magnitude[bass_mask]) / total_energy
                self.treble_energy = np.sum(magnitude[treble_mask]) / total_energy

        except Exception as e:
            pass  # Fail silently for analysis

    def _perform_dynamic_analysis(self):
        """Analyze dynamic range and loudness characteristics"""
        try:
            # Calculate RMS levels over time
            rms_values = []
            for chunk in self.analysis_buffer[-10:]:
                chunk_rms = rms(np.mean(chunk, axis=1))
                if chunk_rms > 1e-6:  # Avoid silence
                    rms_values.append(chunk_rms)

            if len(rms_values) > 5:
                # Dynamic range in dB
                max_rms = max(rms_values)
                min_rms = min(rms_values)
                if min_rms > 0:
                    self.dynamic_range = 20 * np.log10(max_rms / min_rms)
                else:
                    self.dynamic_range = 40.0  # Default high dynamic range

        except Exception as e:
            pass

    def _perform_stereo_analysis(self):
        """Analyze stereo image complexity"""
        try:
            recent_audio = np.vstack(self.analysis_buffer[-5:])
            left = recent_audio[:, 0]
            right = recent_audio[:, 1]

            # Calculate correlation coefficient
            if len(left) > 1:
                correlation_matrix = np.corrcoef(left, right)
                if correlation_matrix.size > 1:
                    correlation = correlation_matrix[0, 1]
                    # Lower correlation = more complex stereo image
                    self.stereo_complexity = 1.0 - abs(correlation)

        except Exception as e:
            pass

    def _detect_content_type(self):
        """Detect content type based on analysis"""
        # Simple heuristic-based detection
        confidence_scores = {}

        # Modern Pop: Bright, compressed, moderate bass
        pop_score = 0
        if 2000 <= self.spectral_centroid <= 4000:  # Bright but not harsh
            pop_score += 0.3
        if self.dynamic_range < 15:  # Compressed
            pop_score += 0.3
        if 0.15 <= self.bass_energy <= 0.35:  # Moderate bass
            pop_score += 0.2
        if self.stereo_complexity > 0.3:  # Good stereo spread
            pop_score += 0.2
        confidence_scores[AutoMasterProfile.MODERN_POP] = pop_score

        # Electronic: Very bright, very compressed, heavy bass
        electronic_score = 0
        if self.spectral_centroid > 3000:  # Bright
            electronic_score += 0.3
        if self.dynamic_range < 10:  # Very compressed
            electronic_score += 0.3
        if self.bass_energy > 0.25:  # Heavy bass
            electronic_score += 0.2
        if self.treble_energy > 0.3:  # Lots of high-end
            electronic_score += 0.2
        confidence_scores[AutoMasterProfile.ELECTRONIC] = electronic_score

        # Acoustic/Folk: Natural dynamics, mid-focused
        acoustic_score = 0
        if 1000 <= self.spectral_centroid <= 3000:  # Mid-focused
            acoustic_score += 0.3
        if self.dynamic_range > 20:  # Good dynamics
            acoustic_score += 0.3
        if self.bass_energy < 0.25:  # Not bass-heavy
            acoustic_score += 0.2
        if self.stereo_complexity < 0.5:  # Simple stereo image
            acoustic_score += 0.2
        confidence_scores[AutoMasterProfile.ACOUSTIC] = acoustic_score

        # Classical: Wide dynamics, natural balance
        classical_score = 0
        if 1500 <= self.spectral_centroid <= 2500:  # Natural balance
            classical_score += 0.3
        if self.dynamic_range > 30:  # Very wide dynamics
            classical_score += 0.4
        if 0.1 <= self.bass_energy <= 0.2:  # Moderate bass
            classical_score += 0.15
        if self.stereo_complexity > 0.4:  # Complex stereo
            classical_score += 0.15
        confidence_scores[AutoMasterProfile.CLASSICAL] = classical_score

        # Podcast/Broadcast: Mid-focused, compressed, mono-friendly
        podcast_score = 0
        if 800 <= self.spectral_centroid <= 2000:  # Voice range
            podcast_score += 0.4
        if self.dynamic_range < 12:  # Broadcast compression
            podcast_score += 0.3
        if self.bass_energy < 0.15:  # Not bass-heavy
            podcast_score += 0.15
        if self.stereo_complexity < 0.3:  # Mostly mono
            podcast_score += 0.15
        confidence_scores[AutoMasterProfile.PODCAST] = podcast_score

        # Select best match
        if confidence_scores:
            best_profile = max(confidence_scores.items(), key=lambda x: x[1])
            if best_profile[1] > 0.6:  # High confidence threshold
                self.detected_genre = best_profile[0]
                self.confidence_level = best_profile[1]
                self.analysis_complete = True
            else:
                self.detected_genre = AutoMasterProfile.ADAPTIVE
                self.confidence_level = 0.5

    def get_analysis_results(self) -> Dict[str, Any]:
        """Get current analysis results"""
        return {
            'detected_genre': self.detected_genre.value,
            'confidence_level': self.confidence_level,
            'analysis_complete': self.analysis_complete,
            'spectral_centroid': self.spectral_centroid,
            'dynamic_range': self.dynamic_range,
            'bass_energy': self.bass_energy,
            'treble_energy': self.treble_energy,
            'stereo_complexity': self.stereo_complexity,
        }


class AutoMasterProcessor:
    """Intelligent auto-mastering processor"""

    def __init__(self, config: PlayerConfig):
        self.config = config
        self.lock = Lock()
        self.enabled = True

        # Content analysis
        self.analyzer = ContentAnalyzer(config)

        # Current profile and settings
        self.current_profile = AutoMasterProfile.ADAPTIVE
        self.manual_profile: Optional[AutoMasterProfile] = None

        # Target processing parameters (updated based on profile)
        self.target_rms_db = -16.0  # Target RMS level
        self.target_eq_bands = []  # EQ adjustments
        self.target_stereo_width = 1.0  # Stereo width
        self.target_dynamics = 1.0  # Compression amount

        # Smoothing for parameter changes
        self.rms_smoother = ExponentialSmoother(alpha=0.05)
        self.eq_smoothers = [ExponentialSmoother(alpha=0.02) for _ in range(8)]
        self.width_smoother = ExponentialSmoother(alpha=0.03)

        # Processing state
        self.chunks_processed = 0
        self.learning_mode = True  # Analyze content initially
        self.analysis_period = 100  # Chunks to analyze before settling

        print("🤖 Auto-mastering processor initialized")

    def set_profile(self, profile: AutoMasterProfile):
        """Manually set mastering profile"""
        with self.lock:
            self.manual_profile = profile
            self.current_profile = profile
            self._update_target_parameters()
            print(f"🎛️ Auto-mastering profile set to: {profile.value}")

    def enable_adaptive_mode(self):
        """Enable adaptive profile detection"""
        with self.lock:
            self.manual_profile = None
            self.current_profile = AutoMasterProfile.ADAPTIVE
            self.learning_mode = True
            self.chunks_processed = 0
            print("🧠 Adaptive auto-mastering enabled")

    def _update_target_parameters(self):
        """Update target parameters based on current profile"""
        profile_settings = self._get_profile_settings(self.current_profile)

        self.target_rms_db = profile_settings['target_rms']
        self.target_eq_bands = profile_settings['eq_curve']
        self.target_stereo_width = profile_settings['stereo_width']
        self.target_dynamics = profile_settings['dynamics']

    def _get_profile_settings(self, profile: AutoMasterProfile) -> Dict[str, Any]:
        """Get settings for specific mastering profile"""
        settings = {
            AutoMasterProfile.MODERN_POP: {
                'target_rms': -12.0,  # Loud modern master
                'eq_curve': [  # 8-band EQ adjustments in dB
                    {'freq': 60, 'gain': -2.0},    # Clean up sub-bass
                    {'freq': 120, 'gain': +1.0},   # Punchy bass
                    {'freq': 250, 'gain': -1.0},   # Clean low-mids
                    {'freq': 500, 'gain': 0.0},    # Neutral
                    {'freq': 1000, 'gain': +0.5},  # Presence
                    {'freq': 2000, 'gain': +1.5},  # Modern brightness
                    {'freq': 4000, 'gain': +2.0},  # Excitement
                    {'freq': 8000, 'gain': +1.0},  # Air
                ],
                'stereo_width': 1.2,  # Wide stereo
                'dynamics': 0.7,  # Compressed
            },

            AutoMasterProfile.CLASSIC_ROCK: {
                'target_rms': -14.0,
                'eq_curve': [
                    {'freq': 60, 'gain': -1.0},
                    {'freq': 120, 'gain': +2.0},   # Rock bass
                    {'freq': 250, 'gain': +0.5},
                    {'freq': 500, 'gain': +1.0},   # Midrange punch
                    {'freq': 1000, 'gain': +1.5},  # Presence
                    {'freq': 2000, 'gain': +1.0},
                    {'freq': 4000, 'gain': +0.5},
                    {'freq': 8000, 'gain': -0.5},  # Less harsh
                ],
                'stereo_width': 1.1,
                'dynamics': 0.8,  # Less compressed
            },

            AutoMasterProfile.ELECTRONIC: {
                'target_rms': -10.0,  # Very loud
                'eq_curve': [
                    {'freq': 60, 'gain': +3.0},    # Sub-bass
                    {'freq': 120, 'gain': +2.0},   # Bass
                    {'freq': 250, 'gain': -2.0},   # Clean mids
                    {'freq': 500, 'gain': -1.0},
                    {'freq': 1000, 'gain': 0.0},
                    {'freq': 2000, 'gain': +1.0},
                    {'freq': 4000, 'gain': +3.0},  # Crisp highs
                    {'freq': 8000, 'gain': +2.0},  # Sparkle
                ],
                'stereo_width': 1.4,  # Very wide
                'dynamics': 0.6,  # Heavily compressed
            },

            AutoMasterProfile.ACOUSTIC: {
                'target_rms': -18.0,  # Natural loudness
                'eq_curve': [
                    {'freq': 60, 'gain': -3.0},    # Roll off lows
                    {'freq': 120, 'gain': -1.0},
                    {'freq': 250, 'gain': +0.5},
                    {'freq': 500, 'gain': +1.0},   # Warmth
                    {'freq': 1000, 'gain': +1.5},  # Clarity
                    {'freq': 2000, 'gain': +1.0},  # Presence
                    {'freq': 4000, 'gain': +0.5},
                    {'freq': 8000, 'gain': +1.5},  # Natural air
                ],
                'stereo_width': 0.9,  # Slightly narrow
                'dynamics': 0.9,  # Preserve dynamics
            },

            AutoMasterProfile.CLASSICAL: {
                'target_rms': -20.0,  # Preserve dynamics
                'eq_curve': [
                    {'freq': 60, 'gain': +0.5},    # Natural bass
                    {'freq': 120, 'gain': +0.3},
                    {'freq': 250, 'gain': 0.0},
                    {'freq': 500, 'gain': +0.2},
                    {'freq': 1000, 'gain': +0.3},
                    {'freq': 2000, 'gain': +0.5},
                    {'freq': 4000, 'gain': +0.8},  # String clarity
                    {'freq': 8000, 'gain': +1.2},  # Hall ambience
                ],
                'stereo_width': 1.0,  # Natural width
                'dynamics': 0.95,  # Minimal compression
            },

            AutoMasterProfile.PODCAST: {
                'target_rms': -16.0,  # Broadcast standard
                'eq_curve': [
                    {'freq': 60, 'gain': -6.0},    # Remove rumble
                    {'freq': 120, 'gain': -3.0},   # Clean bass
                    {'freq': 250, 'gain': +1.0},   # Voice warmth
                    {'freq': 500, 'gain': +2.0},   # Voice clarity
                    {'freq': 1000, 'gain': +3.0},  # Intelligibility
                    {'freq': 2000, 'gain': +2.5},  # Presence
                    {'freq': 4000, 'gain': +1.0},  # Clarity
                    {'freq': 8000, 'gain': -2.0},  # Reduce sibilance
                ],
                'stereo_width': 0.8,  # Mono-compatible
                'dynamics': 0.7,  # Consistent levels
            },
        }

        # Default adaptive settings
        return settings.get(profile, settings[AutoMasterProfile.MODERN_POP])

    def process_chunk(self, audio_chunk: np.ndarray) -> Tuple[Dict[str, Any], np.ndarray]:
        """
        Process audio chunk and return target parameters

        Returns:
            Tuple of (target_parameters, analyzed_audio)
            target_parameters can be applied by other processors
        """
        if not self.enabled:
            return {}, audio_chunk

        with self.lock:
            # Analyze content (always for adaptive learning)
            if self.learning_mode or self.manual_profile is None:
                self.analyzer.analyze_chunk(audio_chunk)

                # Check if we should update profile
                if self.chunks_processed > self.analysis_period:
                    analysis = self.analyzer.get_analysis_results()
                    if analysis['analysis_complete'] and self.manual_profile is None:
                        new_profile = AutoMasterProfile(analysis['detected_genre'])
                        if new_profile != self.current_profile:
                            self.current_profile = new_profile
                            self._update_target_parameters()
                            print(f"🧠 Auto-detected profile: {new_profile.value} "
                                  f"(confidence: {analysis['confidence_level']:.1%})")

                    self.learning_mode = False

            self.chunks_processed += 1

            # Generate smoothed target parameters
            target_params = {
                'target_rms_db': self.target_rms_db,
                'eq_bands': self.target_eq_bands,
                'stereo_width': self.target_stereo_width,
                'dynamics': self.target_dynamics,
                'profile': self.current_profile.value,
                'analysis': self.analyzer.get_analysis_results(),
            }

            return target_params, audio_chunk

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current auto-mastering statistics"""
        analysis = self.analyzer.get_analysis_results()

        return {
            'enabled': self.enabled,
            'current_profile': self.current_profile.value,
            'manual_profile': self.manual_profile.value if self.manual_profile else None,
            'learning_mode': self.learning_mode,
            'chunks_processed': self.chunks_processed,
            'target_rms_db': self.target_rms_db,
            'target_stereo_width': self.target_stereo_width,
            'analysis': analysis,
        }

    def set_enabled(self, enabled: bool):
        """Enable/disable auto-mastering"""
        with self.lock:
            self.enabled = enabled
            if enabled:
                print("🤖 Auto-mastering enabled")
            else:
                print("🤖 Auto-mastering disabled")

    @staticmethod
    def get_available_profiles() -> List[str]:
        """Get list of available auto-mastering profiles"""
        return [profile.value for profile in AutoMasterProfile]