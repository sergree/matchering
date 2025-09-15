# -*- coding: utf-8 -*-

"""
Auralis Basic DSP Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basic audio processing utilities

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import numpy as np


def channel_count(audio: np.ndarray) -> int:
    """Get the number of audio channels"""
    if audio.ndim == 1:
        return 1
    return audio.shape[1]


def size(audio: np.ndarray) -> int:
    """Get the number of audio samples"""
    return audio.shape[0]


def rms(audio: np.ndarray) -> float:
    """Calculate RMS (Root Mean Square) of audio signal"""
    return np.sqrt(np.mean(audio ** 2))


def normalize(audio: np.ndarray, target_level: float = 1.0) -> np.ndarray:
    """
    Normalize audio to target level

    Args:
        audio: Input audio signal
        target_level: Target peak level (default 1.0)

    Returns:
        Normalized audio signal
    """
    peak = np.max(np.abs(audio))
    if peak > 0:
        return audio * (target_level / peak)
    return audio


def amplify(audio: np.ndarray, gain_db: float) -> np.ndarray:
    """
    Apply gain to audio signal

    Args:
        audio: Input audio signal
        gain_db: Gain in decibels

    Returns:
        Amplified audio signal
    """
    gain_linear = 10 ** (gain_db / 20)
    return audio * gain_linear


def mid_side_encode(stereo_audio: np.ndarray) -> tuple:
    """
    Convert stereo audio to mid-side encoding

    Args:
        stereo_audio: Stereo audio signal [samples, 2]

    Returns:
        tuple: (mid_signal, side_signal)
    """
    left = stereo_audio[:, 0]
    right = stereo_audio[:, 1]

    mid = (left + right) / 2
    side = (left - right) / 2

    return mid, side


def mid_side_decode(mid: np.ndarray, side: np.ndarray) -> np.ndarray:
    """
    Convert mid-side signals back to stereo

    Args:
        mid: Mid signal
        side: Side signal

    Returns:
        Stereo audio signal [samples, 2]
    """
    left = mid + side
    right = mid - side

    return np.column_stack([left, right])