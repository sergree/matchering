# -*- coding: utf-8 -*-

"""
Advanced Smoothing Systems for Matchering Player
Professional-grade parameter smoothing to prevent audio artifacts
"""

import numpy as np
from typing import Optional
from collections import deque


class ExponentialSmoother:
    """
    Exponential smoothing with attack/release characteristics
    Mimics analog circuit behavior for natural-sounding parameter changes
    """
    
    def __init__(
        self, 
        attack_alpha: float = 0.01,    # Slow attack for gradual increases
        release_alpha: float = 0.05,   # Faster release for quick decreases
        max_change_per_chunk: float = 0.1  # Max 10% change per chunk (safety)
    ):
        """
        Advanced exponential smoother with different attack/release rates
        
        Args:
            attack_alpha: Smoothing factor when value is increasing (0 < alpha <= 1)
            release_alpha: Smoothing factor when value is decreasing
            max_change_per_chunk: Maximum allowed change per processing chunk
        """
        assert 0 < attack_alpha <= 1, "Attack alpha must be between 0 and 1"
        assert 0 < release_alpha <= 1, "Release alpha must be between 0 and 1"
        assert 0 < max_change_per_chunk <= 1, "Max change must be between 0 and 1"
        
        self.attack_alpha = attack_alpha
        self.release_alpha = release_alpha
        self.max_change_per_chunk = max_change_per_chunk
        self.current_value: Optional[float] = None
    
    def update(self, new_value: float) -> float:
        """Update smoother with new value and return smoothed result"""
        if self.current_value is None:
            # First value - no smoothing needed
            self.current_value = new_value
            return new_value
        
        # Determine if we're attacking (increasing) or releasing (decreasing)
        is_increasing = new_value > self.current_value
        alpha = self.attack_alpha if is_increasing else self.release_alpha
        
        # Calculate smoothed value
        smoothed = alpha * new_value + (1 - alpha) * self.current_value
        
        # Apply safety limiting to prevent sudden jumps
        max_absolute_change = self.current_value * self.max_change_per_chunk
        change = smoothed - self.current_value
        
        if abs(change) > max_absolute_change:
            # Limit the change to the maximum allowed
            change = np.sign(change) * max_absolute_change
            smoothed = self.current_value + change
        
        self.current_value = smoothed
        return smoothed
    
    def reset(self):
        """Reset smoother state"""
        self.current_value = None
    
    def get_current_value(self) -> Optional[float]:
        """Get current smoothed value"""
        return self.current_value


class MovingAverageFilter:
    """
    Moving average filter for additional smoothing of RMS calculations
    Reduces impact of transient peaks on gain calculations
    """
    
    def __init__(self, window_size: int = 10):
        """
        Initialize moving average filter
        
        Args:
            window_size: Number of samples to average (10 = 1 second at 100ms chunks)
        """
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
    
    def update(self, new_value: float) -> float:
        """Add new value and return moving average"""
        self.history.append(new_value)
        return np.mean(self.history) if self.history else new_value
    
    def reset(self):
        """Clear filter history"""
        self.history.clear()
    
    def is_ready(self) -> bool:
        """Check if filter has enough data for stable output"""
        return len(self.history) >= min(5, self.window_size // 2)


class AdaptiveGainSmoother:
    """
    Adaptive gain smoother that adjusts smoothing based on audio characteristics
    More aggressive smoothing for stable content, faster response for dynamic content
    """
    
    def __init__(
        self,
        base_attack_alpha: float = 0.01,
        base_release_alpha: float = 0.05,
        adaptation_speed: float = 0.001
    ):
        self.base_attack_alpha = base_attack_alpha
        self.base_release_alpha = base_release_alpha
        self.adaptation_speed = adaptation_speed
        
        # Core smoothers for mid and side channels
        self.mid_smoother = ExponentialSmoother(base_attack_alpha, base_release_alpha)
        self.side_smoother = ExponentialSmoother(base_attack_alpha, base_release_alpha)
        
        # RMS history for adaptation
        self.rms_variance_history = deque(maxlen=50)  # 5 seconds of history
        
        # Current adaptation state
        self.current_variance = 0.0
        self.adapted_attack_alpha = base_attack_alpha
        self.adapted_release_alpha = base_release_alpha
    
    def _calculate_adaptation_factor(self, rms_values: list) -> float:
        """Calculate how much to adapt smoothing based on RMS variance"""
        if len(rms_values) < 10:
            return 1.0
        
        # Calculate variance in recent RMS values
        recent_variance = np.var(rms_values[-20:])  # Last 2 seconds
        self.rms_variance_history.append(recent_variance)
        
        # Smooth the variance itself
        if len(self.rms_variance_history) > 1:
            self.current_variance = (
                self.adaptation_speed * recent_variance + 
                (1 - self.adaptation_speed) * self.current_variance
            )
        else:
            self.current_variance = recent_variance
        
        # High variance = more dynamic content = faster response needed
        # Low variance = stable content = more smoothing beneficial
        adaptation_factor = np.clip(self.current_variance * 100, 0.5, 2.0)
        
        return adaptation_factor
    
    def update_gains(
        self, 
        mid_gain: float, 
        side_gain: float,
        rms_history_mid: list,
        rms_history_side: list
    ) -> tuple[float, float]:
        """
        Update both mid and side gains with adaptive smoothing
        
        Returns:
            Tuple of (smoothed_mid_gain, smoothed_side_gain)
        """
        # Calculate adaptation based on audio dynamics
        mid_adaptation = self._calculate_adaptation_factor(rms_history_mid)
        side_adaptation = self._calculate_adaptation_factor(rms_history_side)
        
        # Adapt smoothing parameters
        self.adapted_attack_alpha = self.base_attack_alpha * mid_adaptation
        self.adapted_release_alpha = self.base_release_alpha * mid_adaptation
        
        # Ensure we don't exceed bounds
        self.adapted_attack_alpha = np.clip(self.adapted_attack_alpha, 0.001, 0.1)
        self.adapted_release_alpha = np.clip(self.adapted_release_alpha, 0.001, 0.2)
        
        # Update smoother parameters
        self.mid_smoother.attack_alpha = self.adapted_attack_alpha
        self.mid_smoother.release_alpha = self.adapted_release_alpha
        self.side_smoother.attack_alpha = self.adapted_attack_alpha * 0.8  # Side slightly slower
        self.side_smoother.release_alpha = self.adapted_release_alpha * 0.8
        
        # Apply smoothing
        smooth_mid = self.mid_smoother.update(mid_gain)
        smooth_side = self.side_smoother.update(side_gain)
        
        return smooth_mid, smooth_side
    
    def reset(self):
        """Reset all smoothing state"""
        self.mid_smoother.reset()
        self.side_smoother.reset()
        self.rms_variance_history.clear()
        self.current_variance = 0.0
    
    def get_adaptation_stats(self) -> dict:
        """Get current adaptation statistics for monitoring"""
        return {
            'current_variance': self.current_variance,
            'adapted_attack_alpha': self.adapted_attack_alpha,
            'adapted_release_alpha': self.adapted_release_alpha,
            'mid_current_gain': self.mid_smoother.get_current_value(),
            'side_current_gain': self.side_smoother.get_current_value(),
        }


class GainChangeRateLimiter:
    """
    Additional safety layer that limits the rate of gain changes
    Prevents any sudden jumps that could damage audio equipment or hearing
    """
    
    def __init__(
        self,
        max_db_change_per_second: float = 3.0,  # Max 3dB change per second
        chunk_rate_hz: float = 10.0  # 10 chunks per second (100ms chunks)
    ):
        self.max_linear_change_per_chunk = 10 ** ((max_db_change_per_second / chunk_rate_hz) / 20.0)
        self.previous_gain = 1.0
    
    def limit_gain_change(self, new_gain: float) -> float:
        """Apply rate limiting to gain change"""
        max_allowed_gain = self.previous_gain * self.max_linear_change_per_chunk
        min_allowed_gain = self.previous_gain / self.max_linear_change_per_chunk
        
        limited_gain = np.clip(new_gain, min_allowed_gain, max_allowed_gain)
        self.previous_gain = limited_gain
        
        return limited_gain
    
    def reset(self, initial_gain: float = 1.0):
        """Reset rate limiter"""
        self.previous_gain = initial_gain
