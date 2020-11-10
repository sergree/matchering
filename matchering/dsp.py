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
import statsmodels.api as sm


def size(array: np.ndarray) -> int:
    return array.shape[0]


def channel_count(array: np.ndarray) -> int:
    return array.shape[1]


def is_mono(array: np.ndarray) -> bool:
    return array.shape[1] == 1


def is_stereo(array: np.ndarray) -> bool:
    return array.shape[1] == 2


def is_1d(array: np.ndarray) -> bool:
    return len(array.shape) == 1


def mono_to_stereo(array: np.ndarray) -> np.ndarray:
    return np.repeat(array, repeats=2, axis=1)


def count_max_peaks(array: np.ndarray) -> (float, int):
    max_value = np.abs(array).max()
    max_count = np.count_nonzero(
        np.logical_or(np.isclose(array, max_value), np.isclose(array, -max_value))
    )
    return max_value, max_count


def lr_to_ms(array: np.ndarray) -> (np.ndarray, np.ndarray):
    array = np.copy(array)
    array[:, 0] += array[:, 1]
    array[:, 0] *= 0.5
    mid = np.copy(array[:, 0])
    array[:, 0] -= array[:, 1]
    side = np.copy(array[:, 0])
    return mid, side


def ms_to_lr(mid_array: np.ndarray, side_array: np.ndarray) -> np.ndarray:
    return np.vstack((mid_array + side_array, mid_array - side_array)).T


def unfold(array: np.ndarray, piece_size: int, divisions: int) -> np.ndarray:
    # (len(array),) -> (divisions, piece_size)
    return array[: piece_size * divisions].reshape(-1, piece_size)


def rms(array: np.ndarray) -> float:
    return np.sqrt(array @ array / array.shape[0])


def batch_rms(array: np.ndarray) -> np.ndarray:
    piece_size = array.shape[1]
    # (divisions, piece_size) -> (divisions, 1, piece_size)
    multiplicand = array[:, None, :]
    # (divisions, piece_size) -> (divisions, piece_size, 1)
    multiplier = array[..., None]
    return np.sqrt(np.squeeze(multiplicand @ multiplier, axis=(1, 2)) / piece_size)


def amplify(array: np.ndarray, gain: float) -> np.ndarray:
    return array * gain


def normalize(
    array: np.ndarray, threshold: float, epsilon: float, normalize_clipped: bool
) -> (np.ndarray, float):
    coefficient = 1.0
    max_value = np.abs(array).max()
    if max_value < threshold or normalize_clipped:
        coefficient = max(epsilon, max_value / threshold)
    return array / coefficient, coefficient


def smooth_lowess(array: np.ndarray, frac: float, it: int, delta: float) -> np.ndarray:
    return sm.nonparametric.lowess(
        array, np.linspace(0, 1, len(array)), frac=frac, it=it, delta=delta
    )[:, 1]


def clip(array: np.ndarray, to: float = 1) -> np.ndarray:
    return np.clip(array, -to, to)


def flip(array: np.ndarray) -> np.ndarray:
    return 1.0 - array


def rectify(array: np.ndarray, threshold: float) -> np.ndarray:
    rectified = np.abs(array).max(1)
    rectified[rectified <= threshold] = threshold
    rectified /= threshold
    return rectified


def max_mix(*args) -> np.ndarray:
    return np.maximum.reduce(args)


def strided_app_2d(matrix: np.ndarray, batch_size: int, step: int) -> np.ndarray:
    matrix_length = matrix.shape[0]
    matrix_width = matrix.shape[1]
    if batch_size > matrix_length:
        return np.expand_dims(matrix, axis=0)
    batch_count = ((matrix_length - batch_size) // step) + 1
    stride_length, stride_width = matrix.strides
    return np.lib.stride_tricks.as_strided(
        matrix,
        shape=(batch_count, batch_size, matrix_width),
        strides=(step * stride_length, stride_length, stride_width),
    )


def batch_rms_2d(array: np.ndarray) -> np.ndarray:
    return batch_rms(array.reshape(array.shape[0], array.shape[1] * array.shape[2]))


def fade(array: np.ndarray, fade_size: int) -> np.ndarray:
    array = np.copy(array)
    fade_in = np.linspace(0, 1, fade_size)
    fade_out = fade_in[::-1]
    array[:fade_size].T[:] *= fade_in
    array[size(array) - fade_size :].T[:] *= fade_out
    return array
