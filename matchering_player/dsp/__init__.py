# -*- coding: utf-8 -*-

"""
DSP Module for Matchering Player
Real-time audio processing adapted from Matchering 2.0
"""

from .basic import (
    rms, amplify, normalize, clip,
    lr_to_ms, ms_to_lr, 
    ExponentialSmoother, CircularBuffer
)
from .levels import RealtimeLevelMatcher, ReferenceProfile, ReferenceCache
from .smoothing import AdaptiveGainSmoother, GainChangeRateLimiter, MovingAverageFilter
from .processor import RealtimeProcessor, PerformanceMonitor
from .frequency import RealtimeFrequencyMatcher, FrequencyProfile, ParametricEQ
from .stereo import RealtimeStereoProcessor, StereoProfile
from .auto_master import AutoMasterProcessor, AutoMasterProfile, ContentAnalyzer

__all__ = [
    # Basic DSP functions
    "rms", "amplify", "normalize", "clip",
    "lr_to_ms", "ms_to_lr",
    "ExponentialSmoother", "CircularBuffer",

    # Level matching
    "RealtimeLevelMatcher", "ReferenceProfile", "ReferenceCache",

    # Frequency matching
    "RealtimeFrequencyMatcher", "FrequencyProfile", "ParametricEQ",

    # Stereo processing
    "RealtimeStereoProcessor", "StereoProfile",

    # Auto-mastering
    "AutoMasterProcessor", "AutoMasterProfile", "ContentAnalyzer",

    # Advanced smoothing
    "AdaptiveGainSmoother", "GainChangeRateLimiter", "MovingAverageFilter",

    # Main processor
    "RealtimeProcessor", "PerformanceMonitor",
]
