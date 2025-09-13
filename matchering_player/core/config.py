# -*- coding: utf-8 -*-

"""
Configuration system for Matchering Player
Adapted from Matchering 2.0 for realtime processing
"""

import math
from typing import Optional


class PlayerConfig:
    """Configuration for Matchering Player realtime processing"""
    
    def __init__(
        self,
        # Audio settings
        sample_rate: int = 44100,
        buffer_size_ms: float = 100.0,  # 100ms chunks for realtime
        
        # Processing settings
        enable_level_matching: bool = True,
        enable_frequency_matching: bool = False,  # MVP: start with levels only
        enable_stereo_width: bool = False,  # Phase 2 feature
        enable_auto_mastering: bool = False,  # Intelligent auto-mastering
        enable_limiter: bool = True,
        
        # Level matching parameters (from Matchering)
        min_value: float = 1e-6,
        threshold: float = (2**15 - 61) / 2**15,  # Same as Matchering
        rms_smoothing_alpha: float = 0.1,  # Exponential smoothing for realtime
        
        # Performance settings
        enable_performance_mode: bool = False,  # Lower quality for performance
        max_cpu_usage: float = 0.8,  # Adaptive quality control
        
        # Reference management
        reference_cache_dir: Optional[str] = None,
        auto_reference_learning: bool = True,
        
        # GUI settings
        enable_visualization: bool = True,
        waveform_resolution: int = 1024,
        spectrum_resolution: int = 512,
    ):
        # Validate sample rate
        assert sample_rate > 0 and isinstance(sample_rate, int)
        if sample_rate != 44100:
            print(f"Warning: Sample rate {sample_rate} Hz not thoroughly tested. 44.1kHz recommended.")
        self.sample_rate = sample_rate
        
        # Calculate buffer size in samples
        assert buffer_size_ms > 0
        self.buffer_size_ms = buffer_size_ms
        self.buffer_size_samples = int((buffer_size_ms / 1000.0) * sample_rate)
        
        # Processing toggles
        self.enable_level_matching = enable_level_matching
        self.enable_frequency_matching = enable_frequency_matching
        self.enable_stereo_width = enable_stereo_width
        self.enable_auto_mastering = enable_auto_mastering
        self.enable_limiter = enable_limiter
        
        # Level matching parameters
        assert min_value > 0 and min_value < 0.1
        self.min_value = min_value
        
        assert threshold > min_value and threshold < 1
        self.threshold = threshold
        
        assert 0 < rms_smoothing_alpha <= 1
        self.rms_smoothing_alpha = rms_smoothing_alpha
        
        # Performance settings
        self.enable_performance_mode = enable_performance_mode
        assert 0 < max_cpu_usage <= 1
        self.max_cpu_usage = max_cpu_usage
        
        # Reference management
        self.reference_cache_dir = reference_cache_dir
        self.auto_reference_learning = auto_reference_learning
        
        # GUI settings
        self.enable_visualization = enable_visualization
        self.waveform_resolution = waveform_resolution
        self.spectrum_resolution = spectrum_resolution
    
    def get_latency_ms(self) -> float:
        """Calculate theoretical minimum latency in milliseconds"""
        return self.buffer_size_ms
    
    def get_latency_samples(self) -> int:
        """Calculate theoretical minimum latency in samples"""
        return self.buffer_size_samples
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization"""
        return {
            'sample_rate': self.sample_rate,
            'buffer_size_ms': self.buffer_size_ms,
            'enable_level_matching': self.enable_level_matching,
            'enable_frequency_matching': self.enable_frequency_matching,
            'enable_stereo_width': self.enable_stereo_width,
            'enable_limiter': self.enable_limiter,
            'min_value': self.min_value,
            'threshold': self.threshold,
            'rms_smoothing_alpha': self.rms_smoothing_alpha,
            'enable_performance_mode': self.enable_performance_mode,
            'max_cpu_usage': self.max_cpu_usage,
            'auto_reference_learning': self.auto_reference_learning,
            'enable_visualization': self.enable_visualization,
        }
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'PlayerConfig':
        """Create config from dictionary"""
        return cls(**config_dict)


class LimiterConfig:
    """Limiter configuration adapted from Matchering's Hyrax limiter"""
    
    def __init__(
        self,
        attack: float = 1,
        hold: float = 1,
        release: float = 3000,
        attack_filter_coefficient: float = -2,
        hold_filter_order: int = 1,
        hold_filter_coefficient: float = 7,
        release_filter_order: int = 1,
        release_filter_coefficient: float = 800,
    ):
        # Validate parameters (same as Matchering)
        assert attack > 0
        self.attack = attack
        
        assert hold > 0
        self.hold = hold
        
        assert release > 0
        self.release = release
        
        self.attack_filter_coefficient = attack_filter_coefficient
        
        assert hold_filter_order > 0 and isinstance(hold_filter_order, int)
        self.hold_filter_order = hold_filter_order
        self.hold_filter_coefficient = hold_filter_coefficient
        
        assert release_filter_order > 0 and isinstance(release_filter_order, int)
        self.release_filter_order = release_filter_order
        self.release_filter_coefficient = release_filter_coefficient
