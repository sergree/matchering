# -*- coding: utf-8 -*-

"""
Matchering - Audio Matching and Mastering Python Library
Copyright (C) 2016-2022 Sergree

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import numpy as np
import math
from scipy import signal
from scipy.ndimage.filters import maximum_filter1d

from .. import Config
from ..log import debug
from ..dsp import rectify, flip, max_mix
from ..utils import make_odd, ms_to_samples


def __sliding_window_fast(
    array: np.ndarray, window_size: int, mode: str = "attack"
) -> np.ndarray:
    if mode == "attack":
        window_size = make_odd(window_size)
        return maximum_filter1d(array, size=(2 * window_size - 1))
    half_window_size = (window_size - 1) // 2
    array = np.pad(array, (half_window_size, 0))
    return maximum_filter1d(array, size=window_size)[:-half_window_size]


def __process_attack(array: np.ndarray, config: Config) -> (np.ndarray, np.ndarray):
    attack = ms_to_samples(config.limiter.attack, config.internal_sample_rate)

    slided_input = __sliding_window_fast(array, attack, mode="attack")

    coef = math.exp(config.limiter.attack_filter_coefficient / attack)
    b = [1 - coef]
    a = [1, -coef]
    output = signal.filtfilt(b, a, slided_input)

    return output, slided_input


def __process_release(array: np.ndarray, config: Config) -> np.ndarray:
    hold = ms_to_samples(config.limiter.hold, config.internal_sample_rate)

    slided_input = __sliding_window_fast(array, hold, mode="hold")

    b, a = signal.butter(
        config.limiter.hold_filter_order,
        config.limiter.hold_filter_coefficient,
        fs=config.internal_sample_rate,
    )
    hold_output = signal.lfilter(b, a, slided_input)

    b, a = signal.butter(
        config.limiter.release_filter_order,
        config.limiter.release_filter_coefficient / config.limiter.release,
        fs=config.internal_sample_rate,
    )
    release_output = signal.lfilter(b, a, np.maximum(slided_input, hold_output))

    return np.maximum(hold_output, release_output)


def limit(array: np.ndarray, config: Config = None, sample_rate: int = None) -> np.ndarray:
    # Handle legacy sample_rate parameter
    if sample_rate is not None:
        config = Config()
        config.internal_sample_rate = sample_rate
    
    # First check: if empty array, return as is
    if array.size == 0:
        return array
    
    # Compute robust peak estimate (ignore rare outliers)
    abs_array = np.abs(array)
    robust_peak = float(np.percentile(abs_array, 99.9))
    
    # If robust peak is below threshold, treat as no limiting needed
    if robust_peak <= config.threshold:
        debug("The limiter is not needed - robust peak below threshold")
        return array
    
    # Fall back to strict max check to decide limiting path
    max_val = float(np.max(abs_array))
    debug(f"The limiter is needed - maximum value {max_val} exceeds threshold {config.threshold} (robust {robust_peak})")
    
    # Only copy the array if we need to modify it
    result = np.array(array, copy=True)

    debug("The limiter is started. Preparing the gain envelope...")

    # Calculate the amount we need to reduce the gain by
    gain_reduction = max_val / config.threshold - 1.0
    if gain_reduction <= 0.0:
        return array  # Defensive check - shouldn't happen due to earlier threshold check
    
    # Apply soft knee compression near threshold
    scale = np.where(
        np.abs(result) > config.threshold,
        config.threshold / (np.abs(result) + 1e-6),  # Limit to threshold
        1.0  # Leave unchanged
    )
    result *= scale
    
    # Safety check - ensure we didn't exceed threshold
    max_val_after = float(np.max(np.abs(result)))
    if max_val_after > config.threshold:
        result *= config.threshold / max_val_after
    
    return result
