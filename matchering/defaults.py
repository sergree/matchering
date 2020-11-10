# -*- coding: utf-8 -*-

"""
Matchering - Audio Matching and Mastering Python Library
Copyright (C) 2016-2021 Sergree

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

import math
from .log import debug


class LimiterConfig:
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
    def __init__(
        self,
        internal_sample_rate: int = 44100,
        max_length: float = 15 * 60,
        max_piece_size: float = 15,
        threshold: float = (2 ** 15 - 61) / 2 ** 15,
        min_value: float = 1e-6,
        fft_size: int = 4096,
        lin_log_oversampling: int = 4,
        rms_correction_steps: int = 4,
        clipping_samples_threshold: int = 8,
        limited_samples_threshold: int = 128,
        allow_equality: bool = False,
        lowess_frac: float = 0.0375,
        lowess_it: int = 0,
        lowess_delta: float = 0.001,
        preview_size: float = 30,
        preview_analysis_step: float = 5,
        preview_fade_size: float = 1,
        preview_fade_coefficient: float = 8,
        temp_folder: str = None,
        limiter: LimiterConfig = LimiterConfig(),
    ):
        assert internal_sample_rate > 0
        assert isinstance(internal_sample_rate, int)
        if internal_sample_rate != 44100:
            debug(
                "Using an internal sample rate other than 44100 has not been tested properly! "
                "Use it at your own risk!"
            )
        self.internal_sample_rate = internal_sample_rate

        assert max_length > 0
        assert max_length > fft_size / internal_sample_rate
        self.max_length = max_length

        assert threshold > min_value
        assert threshold < 1
        self.threshold = threshold

        assert min_value > 0
        assert min_value < 0.1
        self.min_value = min_value

        assert max_piece_size > 0
        assert max_piece_size > fft_size / internal_sample_rate
        assert max_piece_size < max_length
        self.max_piece_size = max_piece_size * internal_sample_rate

        assert fft_size > 1
        assert math.log2(fft_size).is_integer()
        self.fft_size = fft_size

        assert lin_log_oversampling > 0
        assert isinstance(lin_log_oversampling, int)
        self.lin_log_oversampling = lin_log_oversampling

        assert rms_correction_steps >= 0
        assert isinstance(rms_correction_steps, int)
        self.rms_correction_steps = rms_correction_steps

        assert clipping_samples_threshold >= 0
        assert limited_samples_threshold > 0
        assert limited_samples_threshold > clipping_samples_threshold
        assert isinstance(clipping_samples_threshold, int)
        assert isinstance(limited_samples_threshold, int)
        self.clipping_samples_threshold = clipping_samples_threshold
        self.limited_samples_threshold = limited_samples_threshold

        assert isinstance(allow_equality, bool)
        self.allow_equality = allow_equality

        assert lowess_frac > 0
        assert lowess_it >= 0
        assert lowess_delta >= 0
        assert isinstance(lowess_it, int)
        self.lowess_frac = lowess_frac
        self.lowess_it = lowess_it
        self.lowess_delta = lowess_delta

        assert preview_size > 5
        assert preview_analysis_step > 1
        assert preview_fade_size > 0
        assert preview_fade_coefficient >= 2
        self.preview_size = preview_size * internal_sample_rate
        self.preview_analysis_step = preview_analysis_step * internal_sample_rate
        self.preview_fade_size = preview_fade_size * internal_sample_rate
        self.preview_fade_coefficient = preview_fade_coefficient

        assert temp_folder is None or isinstance(temp_folder, str)
        self.temp_folder = temp_folder

        assert isinstance(limiter, LimiterConfig)
        self.limiter = limiter
