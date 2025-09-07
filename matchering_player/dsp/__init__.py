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

__all__ = [
    # Basic DSP functions
    "rms", "amplify", "normalize", "clip",
    "lr_to_ms", "ms_to_lr",
    "ExponentialSmoother", "CircularBuffer",
    
    # Level matching
    "RealtimeLevelMatcher", "ReferenceProfile", "ReferenceCache",
    
    # Advanced smoothing
    "AdaptiveGainSmoother", "GainChangeRateLimiter", "MovingAverageFilter",
    
    # Main processor
    "RealtimeProcessor", "PerformanceMonitor",
]
