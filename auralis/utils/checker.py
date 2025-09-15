# -*- coding: utf-8 -*-

"""
Auralis Audio Checker
~~~~~~~~~~~~~~~~~~~~~

Audio validation and checking utilities

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import numpy as np
from .logging import debug, ModuleError, Code


def check(audio: np.ndarray, sample_rate: int, config, file_type: str = "audio"):
    """
    Check and validate audio data

    Args:
        audio: Audio data to check
        sample_rate: Sample rate of the audio
        config: Processing configuration
        file_type: Type of file being checked

    Returns:
        tuple: (validated_audio, sample_rate)
    """
    debug(f"Checking {file_type} audio: {audio.shape}, {sample_rate} Hz")

    # For now, just return the audio as-is
    # TODO: Implement full validation and resampling
    return audio, sample_rate


def check_equality(target: np.ndarray, reference: np.ndarray):
    """
    Check if target and reference are too similar

    Args:
        target: Target audio data
        reference: Reference audio data

    Raises:
        ModuleError: If files are too similar
    """
    # Simple similarity check
    if np.array_equal(target, reference):
        raise ModuleError(Code.ERROR_VALIDATION)

    debug("Equality check passed")