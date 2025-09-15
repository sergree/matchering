# -*- coding: utf-8 -*-

"""
Auralis Real-time Audio Processor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Advanced real-time DSP processing with automatic mastering
Integrated from Matchering Player POC

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.
"""

import numpy as np
import time
from typing import Optional, Dict, Any, List
from threading import Lock

from .config import PlayerConfig
from ..utils.logging import debug, info, warning


class PerformanceMonitor:
    """Monitors processing performance and adapts quality"""

    def __init__(self, max_cpu_usage: float = 0.8):
        self.max_cpu_usage = max_cpu_usage
        self.processing_times = []
        self.max_history = 100
        self.performance_mode = False
        self.consecutive_overruns = 0
        self.chunks_processed = 0

    def record_processing_time(self, processing_time: float, chunk_duration: float):
        """Record processing time for a chunk"""
        self.chunks_processed += 1
        cpu_usage = processing_time / chunk_duration if chunk_duration > 0 else 0.0
        self.processing_times.append(cpu_usage)

        if len(self.processing_times) > self.max_history:
            self.processing_times.pop(0)

        # Check for performance issues
        if cpu_usage > self.max_cpu_usage:
            self.consecutive_overruns += 1
        else:
            self.consecutive_overruns = max(0, self.consecutive_overruns - 1)

        # Enter performance mode if we have sustained overruns
        if self.consecutive_overruns >= 5:
            if not self.performance_mode:
                self.performance_mode = True
                warning("Entering performance mode due to high CPU usage")
        elif self.consecutive_overruns == 0 and self.performance_mode:
            recent_avg = np.mean(self.processing_times[-20:]) if len(self.processing_times) >= 20 else cpu_usage
            if recent_avg < self.max_cpu_usage * 0.6:
                self.performance_mode = False
                info("Exiting performance mode - CPU usage stable")

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.processing_times:
            return {
                'cpu_usage': 0.0,
                'performance_mode': False,
                'status': 'initializing',
                'chunks_processed': self.chunks_processed
            }

        recent_usage = np.mean(self.processing_times[-10:]) if len(self.processing_times) >= 10 else 0.0

        # Determine status
        status = 'optimal'
        if recent_usage > self.max_cpu_usage * 0.8:
            status = 'high_load'
        elif self.performance_mode:
            status = 'performance_mode'
        elif recent_usage > self.max_cpu_usage * 0.6:
            status = 'moderate_load'

        return {
            'cpu_usage': recent_usage,
            'avg_cpu_usage': np.mean(self.processing_times),
            'max_cpu_usage': np.max(self.processing_times),
            'performance_mode': self.performance_mode,
            'consecutive_overruns': self.consecutive_overruns,
            'chunks_processed': self.chunks_processed,
            'status': status,
        }


class AdaptiveGainSmoother:
    """Advanced gain smoothing to prevent audio artifacts"""

    def __init__(self, attack_alpha: float = 0.01, release_alpha: float = 0.001):
        self.attack_alpha = attack_alpha    # How fast to increase gain
        self.release_alpha = release_alpha  # How fast to decrease gain
        self.current_gain = 1.0
        self.target_gain = 1.0

    def set_target(self, target: float):
        """Set target gain"""
        self.target_gain = max(0.0, min(10.0, target))  # Clamp to reasonable range

    def process(self, num_samples: int) -> float:
        """Get smoothed gain for current chunk"""
        if abs(self.current_gain - self.target_gain) < 1e-6:
            return self.current_gain

        # Use different smoothing rates for attack vs release
        if self.target_gain > self.current_gain:
            alpha = self.attack_alpha  # Faster attack
        else:
            alpha = self.release_alpha  # Slower release

        # Exponential smoothing
        self.current_gain += (self.target_gain - self.current_gain) * alpha

        return self.current_gain


class RealtimeLevelMatcher:
    """Real-time RMS level matching with reference audio"""

    def __init__(self, config: PlayerConfig):
        self.config = config
        self.enabled = False
        self.reference_rms = None
        self.target_rms_alpha = 0.01  # Smoothing for RMS calculation
        self.current_target_rms = 0.0

        # Gain smoothing for artifact-free transitions
        self.gain_smoother = AdaptiveGainSmoother(
            attack_alpha=0.02,   # Fairly quick attack
            release_alpha=0.005  # Slower release to avoid pumping
        )

        debug("RealtimeLevelMatcher initialized")

    def set_reference_audio(self, reference: np.ndarray):
        """Set reference audio for level matching"""
        if reference is None:
            self.reference_rms = None
            self.enabled = False
            return False

        # Calculate RMS of reference audio
        self.reference_rms = np.sqrt(np.mean(reference ** 2))
        self.enabled = True
        info(f"Reference RMS set: {self.reference_rms:.6f}")
        return True

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Process audio chunk with level matching"""
        if not self.enabled or self.reference_rms is None or self.reference_rms == 0:
            return audio

        # Calculate current RMS
        current_rms = np.sqrt(np.mean(audio ** 2))

        if current_rms == 0:
            return audio

        # Smooth the target RMS to avoid sudden changes
        target_rms = self.reference_rms
        self.current_target_rms += (target_rms - self.current_target_rms) * self.target_rms_alpha

        # Calculate gain needed
        gain = self.current_target_rms / current_rms

        # Apply gain smoothing
        self.gain_smoother.set_target(gain)
        smooth_gain = self.gain_smoother.process(len(audio))

        # Apply gain with soft limiting to prevent clipping
        processed = audio * smooth_gain

        # Soft limiter to prevent harsh clipping
        max_val = np.max(np.abs(processed))
        if max_val > 0.95:
            limiter_gain = 0.95 / max_val
            processed *= limiter_gain

        return processed

    def get_stats(self) -> Dict[str, Any]:
        """Get level matching statistics"""
        return {
            'enabled': self.enabled,
            'reference_loaded': self.reference_rms is not None,
            'reference_rms': self.reference_rms or 0.0,
            'current_gain': self.gain_smoother.current_gain,
            'target_gain': self.gain_smoother.target_gain,
        }


class AutoMasterProcessor:
    """Automatic mastering with genre-aware processing"""

    def __init__(self, config: PlayerConfig):
        self.config = config
        self.enabled = False
        self.profile = "balanced"  # balanced, warm, bright, punchy

        # Simple EQ parameters for different profiles
        self.profiles = {
            "balanced": {"low_gain": 1.0, "mid_gain": 1.0, "high_gain": 1.0},
            "warm": {"low_gain": 1.1, "mid_gain": 0.95, "high_gain": 0.9},
            "bright": {"low_gain": 0.9, "mid_gain": 1.0, "high_gain": 1.15},
            "punchy": {"low_gain": 1.05, "mid_gain": 1.1, "high_gain": 1.05},
        }

        debug(f"AutoMasterProcessor initialized with profile: {self.profile}")

    def set_profile(self, profile: str):
        """Set mastering profile"""
        if profile in self.profiles:
            self.profile = profile
            info(f"Auto-master profile set to: {profile}")
        else:
            warning(f"Unknown profile: {profile}, using balanced")
            self.profile = "balanced"

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply automatic mastering"""
        if not self.enabled:
            return audio

        # Get current profile settings
        settings = self.profiles[self.profile]

        # Simple frequency-dependent gain adjustment
        # This is a simplified version - a full implementation would use proper EQ
        processed = audio.copy()

        # Apply gentle compression-like effect
        rms = np.sqrt(np.mean(audio ** 2))
        if rms > 0.1:  # Only compress if signal is strong enough
            compression_ratio = min(1.0, 0.8 + 0.2 * (0.1 / rms))
            processed *= compression_ratio

        # Apply profile-based tonal shaping (simplified)
        # In a full implementation, this would be proper EQ bands
        profile_gain = (settings["low_gain"] + settings["mid_gain"] + settings["high_gain"]) / 3
        processed *= profile_gain

        return processed

    def get_stats(self) -> Dict[str, Any]:
        """Get auto-master statistics"""
        return {
            'enabled': self.enabled,
            'profile': self.profile,
            'available_profiles': list(self.profiles.keys()),
        }


class RealtimeProcessor:
    """
    Main real-time audio processor for Auralis
    Coordinates all DSP effects and manages processing state
    """

    def __init__(self, config: PlayerConfig):
        self.config = config
        self.lock = Lock()  # Thread safety for parameter changes

        # Initialize DSP components
        self.level_matcher = RealtimeLevelMatcher(config) if config.enable_level_matching else None
        self.auto_master = AutoMasterProcessor(config) if config.enable_auto_mastering else None

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor(max_cpu_usage=0.75)

        # Processing state
        self.is_processing = False
        self.effects_enabled = {
            'level_matching': config.enable_level_matching,
            'auto_mastering': config.enable_auto_mastering,
        }

        info(f"RealtimeProcessor initialized:")
        info(f"   Sample rate: {config.sample_rate} Hz")
        info(f"   Buffer size: {config.buffer_size} samples ({config.buffer_size / config.sample_rate * 1000:.1f}ms)")
        info(f"   Level matching: {'✅ Enabled' if config.enable_level_matching else '❌ Disabled'}")
        info(f"   Auto-mastering: {'✅ Enabled' if config.enable_auto_mastering else '❌ Disabled'}")

    def set_reference_audio(self, reference: np.ndarray) -> bool:
        """Set reference audio for processing"""
        with self.lock:
            success = False

            if self.level_matcher:
                success = self.level_matcher.set_reference_audio(reference)

            if success:
                info("Reference audio loaded for real-time processing")

            return success

    def set_effect_enabled(self, effect_name: str, enabled: bool):
        """Enable/disable specific effects"""
        with self.lock:
            if effect_name in self.effects_enabled:
                self.effects_enabled[effect_name] = enabled

                # Update component state
                if effect_name == 'level_matching' and self.level_matcher:
                    self.level_matcher.enabled = enabled
                elif effect_name == 'auto_mastering' and self.auto_master:
                    self.auto_master.enabled = enabled

                info(f"Effect {effect_name}: {'enabled' if enabled else 'disabled'}")

    def set_auto_master_profile(self, profile: str):
        """Set auto-mastering profile"""
        with self.lock:
            if self.auto_master:
                self.auto_master.set_profile(profile)

    def process_chunk(self, audio: np.ndarray) -> np.ndarray:
        """
        Process a single audio chunk with all enabled effects

        Args:
            audio: Input audio chunk (stereo or mono)

        Returns:
            Processed audio chunk
        """
        if audio is None or len(audio) == 0:
            return audio

        start_time = time.perf_counter()

        with self.lock:
            processed = audio.copy()

            # Apply level matching first
            if self.effects_enabled.get('level_matching', False) and self.level_matcher:
                processed = self.level_matcher.process(processed)

            # Apply auto-mastering
            if self.effects_enabled.get('auto_mastering', False) and self.auto_master:
                processed = self.auto_master.process(processed)

            # Final safety limiting
            max_val = np.max(np.abs(processed))
            if max_val > 0.98:
                processed *= (0.98 / max_val)

        # Record performance
        processing_time = time.perf_counter() - start_time
        chunk_duration = len(audio) / self.config.sample_rate
        self.performance_monitor.record_processing_time(processing_time, chunk_duration)

        return processed

    def get_processing_info(self) -> Dict[str, Any]:
        """Get comprehensive processing information"""
        with self.lock:
            info = {
                'performance': self.performance_monitor.get_stats(),
                'effects': {
                    'level_matching': self.level_matcher.get_stats() if self.level_matcher else {'enabled': False},
                    'auto_mastering': self.auto_master.get_stats() if self.auto_master else {'enabled': False},
                },
                'enabled_effects': self.effects_enabled.copy(),
                'config': {
                    'sample_rate': self.config.sample_rate,
                    'buffer_size': self.config.buffer_size,
                    'buffer_duration_ms': self.config.buffer_size / self.config.sample_rate * 1000,
                }
            }

        return info

    def reset_all_effects(self):
        """Reset all effects to initial state"""
        with self.lock:
            if self.level_matcher:
                self.level_matcher.reference_rms = None
                self.level_matcher.enabled = False
                self.level_matcher.gain_smoother = AdaptiveGainSmoother()

            if self.auto_master:
                self.auto_master.profile = "balanced"
                self.auto_master.enabled = False

            # Reset effect states
            for effect in self.effects_enabled:
                self.effects_enabled[effect] = False

            info("All effects reset to initial state")