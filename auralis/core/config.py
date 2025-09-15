# -*- coding: utf-8 -*-

"""
Auralis Core Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration classes for core audio processing

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import math
from ..utils.logging import debug


class LimiterConfig:
    """Configuration for the audio limiter"""

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
        assert attack > 0
        self.attack = attack

        assert hold > 0
        self.hold = hold

        assert release > 0
        self.release = release

        self.attack_filter_coefficient = attack_filter_coefficient

        assert hold_filter_order > 0
        assert isinstance(hold_filter_order, int)
        self.hold_filter_order = hold_filter_order

        self.hold_filter_coefficient = hold_filter_coefficient

        assert release_filter_order > 0
        assert isinstance(release_filter_order, int)
        self.release_filter_order = release_filter_order

        self.release_filter_coefficient = release_filter_coefficient


class Config:
    """Main configuration for core audio processing"""

    def __init__(
        self,
        internal_sample_rate: int = 44100,
        fft_size: int = 4096,
        temp_folder: str = None,
        allow_equality: bool = False,
        limiter: LimiterConfig = None,
    ):
        # Validate internal sample rate
        assert internal_sample_rate > 0
        assert isinstance(internal_sample_rate, int)
        self.internal_sample_rate = internal_sample_rate

        # Validate FFT size (must be power of 2)
        assert fft_size > 0
        assert isinstance(fft_size, int)
        assert math.log2(fft_size) == int(math.log2(fft_size))
        self.fft_size = fft_size

        # Optional temporary folder
        self.temp_folder = temp_folder

        # Whether to allow target and reference to be identical
        self.allow_equality = allow_equality

        # Limiter configuration
        if limiter is None:
            limiter = LimiterConfig()
        self.limiter = limiter

        debug(f"Core config initialized: SR={self.internal_sample_rate}, FFT={self.fft_size}")

    def __repr__(self):
        return (
            f"Config(internal_sample_rate={self.internal_sample_rate}, "
            f"fft_size={self.fft_size}, temp_folder={self.temp_folder}, "
            f"allow_equality={self.allow_equality})"
        )