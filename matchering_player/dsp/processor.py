# -*- coding: utf-8 -*-

"""
Main Realtime Processor for Matchering Player
Orchestrates all DSP effects and maintains processing state
"""

import numpy as np
import time
from typing import Optional, Dict, Any
from threading import Lock

from .basic import CircularBuffer, is_stereo
from .levels import RealtimeLevelMatcher
from .smoothing import AdaptiveGainSmoother, GainChangeRateLimiter
from .frequency import RealtimeFrequencyMatcher
from .stereo import RealtimeStereoProcessor
from .auto_master import AutoMasterProcessor
from ..core.config import PlayerConfig


class PerformanceMonitor:
    """Monitors processing performance and adapts quality"""
    
    def __init__(self, max_cpu_usage: float = 0.8):
        self.max_cpu_usage = max_cpu_usage
        self.processing_times = []
        self.max_history = 100
        self.performance_mode = False
        self.consecutive_overruns = 0
        
    def record_processing_time(self, processing_time: float, chunk_duration: float):
        """Record processing time for a chunk"""
        cpu_usage = processing_time / chunk_duration
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
            self.performance_mode = True
            print("⚠️  Entering performance mode due to high CPU usage")
        elif self.consecutive_overruns == 0 and self.performance_mode:
            recent_avg = np.mean(self.processing_times[-20:]) if len(self.processing_times) >= 20 else cpu_usage
            if recent_avg < self.max_cpu_usage * 0.6:
                self.performance_mode = False
                print("✅ Exiting performance mode - CPU usage stable")
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.processing_times:
            return {'cpu_usage': 0.0, 'performance_mode': False, 'status': 'initializing'}
        
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
            'status': status,
        }


class RealtimeProcessor:
    """
    Main realtime audio processor for Matchering Player
    Coordinates all DSP effects and manages processing state
    """
    
    def __init__(self, config: PlayerConfig):
        self.config = config
        self.lock = Lock()  # Thread safety for parameter changes
        
        # DSP Components
        self.level_matcher = RealtimeLevelMatcher(config) if config.enable_level_matching else None
        self.frequency_matcher = RealtimeFrequencyMatcher(config) if config.enable_frequency_matching else None
        self.stereo_processor = RealtimeStereoProcessor(config) if config.enable_stereo_width else None
        self.auto_master = AutoMasterProcessor(config) if config.enable_auto_mastering else None
        
        # Advanced smoothing system
        self.gain_smoother = AdaptiveGainSmoother(
            base_attack_alpha=config.rms_smoothing_alpha * 0.1,  # Even slower for professional sound
            base_release_alpha=config.rms_smoothing_alpha * 0.5,
            adaptation_speed=0.001
        )
        
        # Safety rate limiter
        self.rate_limiter_mid = GainChangeRateLimiter(max_db_change_per_second=2.0)  # Conservative 2dB/sec
        self.rate_limiter_side = GainChangeRateLimiter(max_db_change_per_second=2.5)  # Side can be slightly faster
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor(config.max_cpu_usage)
        
        # Processing buffers
        self.input_buffer = CircularBuffer(
            size=config.buffer_size_samples * 4,  # 4x buffer for stability
            channels=2
        )
        self.output_buffer = CircularBuffer(
            size=config.buffer_size_samples * 2,  # 2x output buffer
            channels=2
        )
        
        # Processing state
        self.is_processing = False
        self.bypass_all = False
        self.total_processed_samples = 0
        self.chunks_processed = 0
        self.processing_stats = {}
        
        # Quality adaptation
        self.adaptive_quality = True
        self.current_quality_factor = 1.0  # 1.0 = full quality, lower = reduced quality
        
        # Effect chain (for future expansion)
        self.effect_chain = []
        
        print(f"🎛️  RealtimeProcessor initialized:")
        print(f"   Sample rate: {config.sample_rate} Hz")
        print(f"   Buffer size: {config.buffer_size_samples} samples ({config.buffer_size_ms:.1f}ms)")
        print(f"   Level matching: {'✅ Enabled' if config.enable_level_matching else '❌ Disabled'}")
        print(f"   Frequency matching: {'✅ Enabled' if config.enable_frequency_matching else '❌ Disabled'}")
        print(f"   Stereo width control: {'✅ Enabled' if config.enable_stereo_width else '❌ Disabled'}")
        print(f"   Auto-mastering: {'✅ Enabled' if config.enable_auto_mastering else '❌ Disabled'}")
        print(f"   Advanced smoothing: ✅ Enabled")
        print(f"   Rate limiting: ✅ 2dB/sec max change")
    
    def start_processing(self):
        """Start the realtime processing engine"""
        with self.lock:
            self.is_processing = True
            self.total_processed_samples = 0
            self.chunks_processed = 0
            
            # Reset all smoothing systems
            self.gain_smoother.reset()
            self.rate_limiter_mid.reset()
            self.rate_limiter_side.reset()
            
            print("🚀 Realtime processing started")
    
    def stop_processing(self):
        """Stop the realtime processing engine"""
        with self.lock:
            self.is_processing = False
            print("⏹️  Realtime processing stopped")
    
    def process_audio_chunk(self, input_chunk: np.ndarray) -> np.ndarray:
        """
        Process a single audio chunk through the effect chain
        
        Args:
            input_chunk: Raw audio input (shape: [samples, 2])
            
        Returns:
            Processed audio output (same shape as input)
        """
        if not self.is_processing or self.bypass_all:
            return input_chunk
        
        start_time = time.perf_counter()
        
        try:
            with self.lock:
                # Validate input
                if not is_stereo(input_chunk):
                    print("⚠️  Warning: Processor expects stereo input")
                    return input_chunk
                
                # Start with the input
                processed_chunk = input_chunk.copy()

                # Auto-mastering coordination (if enabled)
                auto_targets = {}
                if self.auto_master and self.config.enable_auto_mastering:
                    auto_targets, processed_chunk = self.auto_master.process_chunk(processed_chunk)

                # Apply level matching (MVP feature)
                if self.level_matcher and self.config.enable_level_matching:
                    processed_chunk = self._process_level_matching(processed_chunk, auto_targets)

                # Apply frequency matching (Phase 2 feature)
                if self.frequency_matcher and self.config.enable_frequency_matching:
                    processed_chunk = self._process_frequency_matching(processed_chunk, auto_targets)

                # Apply stereo width control (Phase 2 feature)
                if self.stereo_processor and self.config.enable_stereo_width:
                    processed_chunk = self._process_stereo_width(processed_chunk, auto_targets)

                # Future effects would go here:
                # - Limiting (Phase 3)
                
                # Apply any additional effects in the chain
                for effect in self.effect_chain:
                    processed_chunk = effect.process(processed_chunk)
                
                # Update counters
                self.total_processed_samples += len(input_chunk)
                self.chunks_processed += 1
                
                # Monitor performance
                processing_time = time.perf_counter() - start_time
                chunk_duration = len(input_chunk) / self.config.sample_rate
                self.performance_monitor.record_processing_time(processing_time, chunk_duration)
                
                # Adapt quality if needed
                self._adapt_quality()
                
                return processed_chunk
                
        except Exception as e:
            print(f"❌ Error in audio processing: {e}")
            return input_chunk
    
    def _process_level_matching(self, audio_chunk: np.ndarray, auto_targets: dict = None) -> np.ndarray:
        """Apply level matching with advanced smoothing"""
        # Check for auto-mastering targets
        if auto_targets and 'target_rms_db' in auto_targets and not self.level_matcher.reference_profile:
            # Use auto-mastering target instead of reference
            target_rms = auto_targets['target_rms_db']
            processed = self._apply_auto_level_target(audio_chunk, target_rms)
            return processed
        elif self.level_matcher and self.level_matcher.reference_profile:
            # Use reference-based level matching
            processed = self.level_matcher.process_chunk(audio_chunk)
            return processed

        return audio_chunk

    def _process_frequency_matching(self, audio_chunk: np.ndarray, auto_targets: dict = None) -> np.ndarray:
        """Apply frequency matching using parametric EQ"""
        # Check for auto-mastering targets
        if auto_targets and 'eq_bands' in auto_targets and not self.frequency_matcher.reference_profile:
            # Apply auto-mastering EQ curve
            processed = self._apply_auto_eq_targets(audio_chunk, auto_targets['eq_bands'])
            return processed
        elif self.frequency_matcher and self.frequency_matcher.reference_profile:
            # Use reference-based frequency matching
            processed = self.frequency_matcher.process_chunk(audio_chunk)
            return processed

        return audio_chunk

    def _process_stereo_width(self, audio_chunk: np.ndarray, auto_targets: dict = None) -> np.ndarray:
        """Apply stereo width control using Mid-Side processing"""
        # Check for auto-mastering targets
        if auto_targets and 'stereo_width' in auto_targets:
            # Use auto-mastering stereo width
            self.stereo_processor.set_width(auto_targets['stereo_width'])

        if self.stereo_processor:
            # Apply stereo width adjustment
            processed = self.stereo_processor.process_chunk(audio_chunk)
            return processed

        return audio_chunk

    def _apply_auto_level_target(self, audio_chunk: np.ndarray, target_rms_db: float) -> np.ndarray:
        """Apply auto-mastering level target"""
        try:
            # Calculate current RMS
            from .basic import rms
            current_rms = rms(np.mean(audio_chunk, axis=1))
            current_rms_db = 20 * np.log10(max(current_rms, 1e-8))

            # Calculate gain needed
            gain_db = target_rms_db - current_rms_db
            gain_db = np.clip(gain_db, -20, +20)  # Safety limits
            gain_linear = 10 ** (gain_db / 20)

            # Apply with smoothing
            smooth_gain = self.gain_smoother.update(gain_linear)

            # Apply gain
            from .basic import amplify
            processed = amplify(audio_chunk, smooth_gain)
            return processed.astype(audio_chunk.dtype)

        except Exception as e:
            print(f"⚠️ Error in auto level matching: {e}")
            return audio_chunk

    def _apply_auto_eq_targets(self, audio_chunk: np.ndarray, eq_bands: list) -> np.ndarray:
        """Apply auto-mastering EQ targets"""
        try:
            if not hasattr(self, '_auto_eq_cache') or self._auto_eq_cache != eq_bands:
                # Update frequency matcher with auto-mastering EQ settings
                if self.frequency_matcher:
                    # Convert auto-mastering EQ bands to frequency matcher format
                    self.frequency_matcher.parametric_eq.update_eq_settings(eq_bands)
                    self._auto_eq_cache = eq_bands.copy()

            # Apply EQ
            if self.frequency_matcher:
                processed = self.frequency_matcher.parametric_eq.process_chunk(audio_chunk)
                return processed

        except Exception as e:
            print(f"⚠️ Error in auto EQ matching: {e}")

        return audio_chunk
    
    def _adapt_quality(self):
        """Adapt processing quality based on CPU usage"""
        if not self.adaptive_quality:
            return
        
        perf_stats = self.performance_monitor.get_stats()
        
        if perf_stats['performance_mode']:
            # Reduce quality for performance
            self.current_quality_factor = 0.7
            # Could reduce smoothing complexity, skip some processing steps, etc.
        else:
            # Restore full quality
            self.current_quality_factor = 1.0
    
    def load_reference_track(self, reference_file_path: str) -> bool:
        """
        Load a reference track for matching

        Args:
            reference_file_path: Path to reference audio file

        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            success_level = True
            success_frequency = True
            success_stereo = True

            # Load for level matching
            if self.level_matcher:
                success_level = self.level_matcher.load_reference(reference_file_path)
                if success_level:
                    self.level_matcher.reset_smoothing()
                    self.gain_smoother.reset()
                    self.rate_limiter_mid.reset()
                    self.rate_limiter_side.reset()

            # Load for frequency matching
            if self.frequency_matcher:
                success_frequency = self.frequency_matcher.load_reference(reference_file_path)

            # Load for stereo processing
            if self.stereo_processor:
                success_stereo = self.stereo_processor.load_reference(reference_file_path)

            overall_success = success_level and success_frequency and success_stereo

            # Count successful loads
            successes = [s for s in [success_level, success_frequency, success_stereo] if s]
            enabled_processors = [p for p in [self.level_matcher, self.frequency_matcher, self.stereo_processor] if p]

            if overall_success:
                print(f"✅ Reference track loaded for all enabled processors")
            elif len(successes) == len(enabled_processors):
                print(f"✅ Reference track loaded for all enabled processors")
            elif len(successes) > 0:
                processor_names = []
                if success_level: processor_names.append("level matching")
                if success_frequency: processor_names.append("frequency matching")
                if success_stereo: processor_names.append("stereo processing")
                print(f"⚠️  Reference loaded for: {', '.join(processor_names)}")
            else:
                print(f"❌ Failed to load reference track")

            return len(successes) > 0  # Succeed if at least one worked
    
    def set_effect_enabled(self, effect_name: str, enabled: bool):
        """Enable or disable specific effects"""
        with self.lock:
            if effect_name == "level_matching" and self.level_matcher:
                self.level_matcher.set_enabled(enabled)
                print(f"🎛️  Level matching {'✅ enabled' if enabled else '❌ disabled'}")
            elif effect_name == "frequency_matching" and self.frequency_matcher:
                self.frequency_matcher.set_enabled(enabled)
                print(f"🎛️  Frequency matching {'✅ enabled' if enabled else '❌ disabled'}")
            elif effect_name == "stereo_width" and self.stereo_processor:
                self.stereo_processor.set_enabled(enabled)
                print(f"🎛️  Stereo width control {'✅ enabled' if enabled else '❌ disabled'}")
            elif effect_name == "auto_mastering" and self.auto_master:
                self.auto_master.set_enabled(enabled)
                print(f"🎛️  Auto-mastering {'✅ enabled' if enabled else '❌ disabled'}")
            elif effect_name == "adaptive_quality":
                self.adaptive_quality = enabled
                print(f"🎛️  Adaptive quality {'✅ enabled' if enabled else '❌ disabled'}")
    
    def set_bypass_all(self, bypass: bool):
        """Bypass all processing (emergency disable)"""
        with self.lock:
            self.bypass_all = bypass
            print(f"🎛️  All processing {'⏸️  bypassed' if bypass else '▶️  active'}")
    
    def set_effect_parameter(self, effect_name: str, parameter: str, value: Any):
        """Set parameters for specific effects"""
        with self.lock:
            if effect_name == "level_matching" and self.level_matcher:
                if parameter == "bypass":
                    self.level_matcher.set_bypass(value)
                elif parameter == "smoothing_speed":
                    # Adjust smoothing speed (0.1 = slow, 1.0 = fast)
                    alpha = self.config.rms_smoothing_alpha * value
                    self.gain_smoother.base_attack_alpha = alpha * 0.1
                    self.gain_smoother.base_release_alpha = alpha * 0.5
            elif effect_name == "stereo_width" and self.stereo_processor:
                if parameter == "width":
                    self.stereo_processor.set_width(value)
                elif parameter == "bypass":
                    self.stereo_processor.set_bypass(value)
                elif parameter == "reference_matching":
                    self.stereo_processor.set_reference_matching(value)
            elif effect_name == "processor":
                if parameter == "max_cpu_usage":
                    self.performance_monitor.max_cpu_usage = value
                elif parameter == "quality_factor":
                    self.current_quality_factor = np.clip(value, 0.1, 1.0)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        stats = {
            'processing_active': self.is_processing,
            'bypass_all': self.bypass_all,
            'total_processed_samples': self.total_processed_samples,
            'chunks_processed': self.chunks_processed,
            'processed_duration_seconds': self.total_processed_samples / self.config.sample_rate,
            'current_quality_factor': self.current_quality_factor,
        }
        
        # Add performance stats
        stats.update(self.performance_monitor.get_stats())
        
        # Add level matcher stats if available
        if self.level_matcher:
            stats['level_matching'] = self.level_matcher.get_current_stats()
        
        # Add smoothing stats
        stats['smoothing'] = self.gain_smoother.get_adaptation_stats()
        
        # Add buffer stats
        stats['buffers'] = {
            'input_available': self.input_buffer.available_samples(),
            'output_available': self.output_buffer.available_samples(),
        }
        
        # Processing rate statistics
        if self.chunks_processed > 0 and self.total_processed_samples > 0:
            stats['processing_rate'] = {
                'chunks_per_second': self.chunks_processed / (self.total_processed_samples / self.config.sample_rate),
                'samples_per_chunk': self.total_processed_samples / self.chunks_processed,
                'expected_chunks_per_second': self.config.sample_rate / self.config.buffer_size_samples,
            }
        
        return stats
    
    def get_latency_info(self) -> Dict[str, float]:
        """Get latency information"""
        base_latency = self.config.get_latency_ms()
        processing_overhead = 1.0  # Estimate 1ms processing overhead
        
        return {
            'buffer_latency_ms': base_latency,
            'processing_overhead_ms': processing_overhead,
            'total_estimated_latency_ms': base_latency + processing_overhead,
            'buffer_latency_samples': self.config.get_latency_samples(),
            'is_low_latency': base_latency < 50.0,  # Under 50ms is considered low latency
        }
    
    def reset_all_effects(self):
        """Reset all effects to initial state"""
        with self.lock:
            if self.level_matcher:
                self.level_matcher.reset_smoothing()
            
            # Reset advanced smoothing systems
            self.gain_smoother.reset()
            self.rate_limiter_mid.reset()
            self.rate_limiter_side.reset()
            
            # Reset performance monitoring
            self.performance_monitor.processing_times.clear()
            self.performance_monitor.performance_mode = False
            self.performance_monitor.consecutive_overruns = 0
            
            # Reset counters
            self.total_processed_samples = 0
            self.chunks_processed = 0
            self.current_quality_factor = 1.0
            
            print("🔄 All effects reset to initial state")
    
    def add_effect_to_chain(self, effect):
        """Add a custom effect to the processing chain (future expansion)"""
        with self.lock:
            self.effect_chain.append(effect)
            print(f"➕ Added effect to chain: {effect.__class__.__name__}")
    
    def remove_effect_from_chain(self, effect_class):
        """Remove an effect from the processing chain"""
        with self.lock:
            removed_count = len(self.effect_chain)
            self.effect_chain = [e for e in self.effect_chain if not isinstance(e, effect_class)]
            removed_count -= len(self.effect_chain)
            print(f"➖ Removed {removed_count} effect(s) from chain: {effect_class.__name__}")
    
    def get_supported_effects(self) -> list:
        """Get list of supported effects"""
        effects = []
        if self.config.enable_level_matching:
            effects.append("level_matching")
        if self.config.enable_frequency_matching:
            effects.append("frequency_matching")  # Future
        if self.config.enable_stereo_width:
            effects.append("stereo_width")  # Future
        if self.config.enable_limiter:
            effects.append("limiter")  # Future
        return effects
    
    def get_health_status(self) -> Dict[str, str]:
        """Get overall system health status"""
        perf_stats = self.performance_monitor.get_stats()
        stats = self.get_processing_stats()
        
        health = {
            'overall': 'healthy',
            'processing': 'active' if self.is_processing else 'stopped',
            'performance': perf_stats['status'],
            'level_matching': 'active' if self.level_matcher and self.level_matcher.enabled else 'disabled',
            'buffers': 'ok',  # Could add buffer health checks
        }
        
        # Determine overall health
        if perf_stats['status'] in ['high_load', 'performance_mode']:
            health['overall'] = 'degraded'
        elif not self.is_processing:
            health['overall'] = 'idle'
        
        return health
