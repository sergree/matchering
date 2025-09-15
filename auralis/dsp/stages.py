# -*- coding: utf-8 -*-

"""
Auralis DSP Processing Stages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multi-stage audio processing pipeline

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import numpy as np
from .basic import rms, normalize, amplify
from ..utils.logging import debug, info


def main(
    target: np.ndarray,
    reference: np.ndarray,
    config,
    need_default: bool = True,
    need_no_limiter: bool = False,
    need_no_limiter_normalized: bool = False,
):
    """
    Main processing pipeline

    Args:
        target: Target audio to be processed
        reference: Reference audio for matching
        config: Processing configuration
        need_default: Whether to generate default (with limiter) result
        need_no_limiter: Whether to generate no-limiter result
        need_no_limiter_normalized: Whether to generate normalized no-limiter result

    Returns:
        tuple: (result, result_no_limiter, result_no_limiter_normalized)
    """
    debug("Starting main processing pipeline")

    # For now, implement a simplified version
    # TODO: Implement full matching algorithms

    # Calculate RMS levels
    target_rms = rms(target)
    reference_rms = rms(reference)

    debug(f"Target RMS: {target_rms:.6f}")
    debug(f"Reference RMS: {reference_rms:.6f}")

    # Calculate gain needed to match RMS levels
    if target_rms > 0:
        gain_db = 20 * np.log10(reference_rms / target_rms)
    else:
        gain_db = 0

    debug(f"Applying gain: {gain_db:.2f} dB")

    # Apply gain to match RMS
    result_no_limiter = amplify(target, gain_db)

    # Apply simple peak limiting for default result
    result = np.copy(result_no_limiter)
    peak = np.max(np.abs(result))
    if peak > 0.99:  # Simple peak limiting
        result = result * (0.99 / peak)

    # Create normalized version
    result_no_limiter_normalized = normalize(result_no_limiter, 0.99)

    info("Processing pipeline completed")

    # Return only what's needed
    return (
        result if need_default else None,
        result_no_limiter if need_no_limiter else None,
        result_no_limiter_normalized if need_no_limiter_normalized else None,
    )