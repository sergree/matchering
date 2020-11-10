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

import numpy as np
from time import time
from scipy import signal, interpolate

from ..log import debug
from .. import Config
from ..dsp import ms_to_lr, smooth_lowess


def __average_fft(
    loudest_pieces: np.ndarray, sample_rate: int, fft_size: int
) -> np.ndarray:
    *_, specs = signal.stft(
        loudest_pieces,
        sample_rate,
        window="boxcar",
        nperseg=fft_size,
        noverlap=0,
        boundary=None,
        padded=False,
    )
    return np.abs(specs).mean((0, 2))


def __smooth_exponentially(matching_fft: np.ndarray, config: Config) -> np.ndarray:
    grid_linear = (
        config.internal_sample_rate * 0.5 * np.linspace(0, 1, config.fft_size // 2 + 1)
    )

    grid_logarithmic = (
        config.internal_sample_rate
        * 0.5
        * np.logspace(
            np.log10(4 / config.fft_size),
            0,
            (config.fft_size // 2) * config.lin_log_oversampling + 1,
        )
    )

    interpolator = interpolate.interp1d(grid_linear, matching_fft, "cubic")
    matching_fft_log = interpolator(grid_logarithmic)

    matching_fft_log_filtered = smooth_lowess(
        matching_fft_log, config.lowess_frac, config.lowess_it, config.lowess_delta
    )

    interpolator = interpolate.interp1d(
        grid_logarithmic, matching_fft_log_filtered, "cubic", fill_value="extrapolate"
    )
    matching_fft_filtered = interpolator(grid_linear)

    matching_fft_filtered[0] = 0
    matching_fft_filtered[1] = matching_fft[1]

    return matching_fft_filtered


def get_fir(
    target_loudest_pieces: np.ndarray,
    reference_loudest_pieces: np.ndarray,
    name: str,
    config: Config,
) -> np.ndarray:
    debug(f"Calculating the {name} FIR for the matching EQ...")

    target_average_fft = __average_fft(
        target_loudest_pieces, config.internal_sample_rate, config.fft_size
    )
    reference_average_fft = __average_fft(
        reference_loudest_pieces, config.internal_sample_rate, config.fft_size
    )

    np.maximum(config.min_value, target_average_fft, out=target_average_fft)
    matching_fft = reference_average_fft / target_average_fft

    matching_fft_filtered = __smooth_exponentially(matching_fft, config)

    fir = np.fft.irfft(matching_fft_filtered)
    fir = np.fft.ifftshift(fir) * signal.windows.hann(len(fir))

    return fir


def convolve(
    target_mid: np.ndarray,
    mid_fir: np.ndarray,
    target_side: np.ndarray,
    side_fir: np.ndarray,
) -> (np.ndarray, np.ndarray):
    debug("Convolving the TARGET audio with calculated FIRs...")
    timer = time()
    result_mid = signal.fftconvolve(target_mid, mid_fir, "same")
    result_side = signal.fftconvolve(target_side, side_fir, "same")
    debug(f"The convolution is done in {time() - timer:.2f} seconds")

    debug("Converting MS to LR...")
    result = ms_to_lr(result_mid, result_side)

    return result, result_mid
