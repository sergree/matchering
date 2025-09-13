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
    # Allow passing (array, coef) tuples by taking the array part
    if isinstance(array, tuple) and len(array) >= 1:
        array = array[0]
    return np.sqrt(np.mean(np.asarray(array) ** 2))


def batch_rms(array: np.ndarray) -> np.ndarray:
    piece_size = array.shape[1]
    # (divisions, piece_size) -> (divisions, 1, piece_size)
    multiplicand = array[:, None, :]
    # (divisions, piece_size) -> (divisions, piece_size, 1)
    multiplier = array[..., None]
    return np.sqrt(np.squeeze(multiplicand @ multiplier, axis=(1, 2)) / piece_size)


def amplify(array: np.ndarray, gain: float) -> np.ndarray:
    if gain == 1.0:
        return array  # Return input directly if no amplification needed
    return array * gain


def normalize(
    array: np.ndarray, threshold: float = 1.0, epsilon: float = 1e-7, normalize_clipped: bool = True
) -> (np.ndarray, float):
    if array.size == 0:
        return array.copy(), 1.0

    if normalize_clipped:
        # Target RMS = threshold
        current_rms = rms(array)
        if current_rms < epsilon:
            return array.astype(array.dtype, copy=True), 1.0
        gain = threshold / current_rms
        normalized = array * gain
        # If target threshold is 1.0 or higher, prevent clipping by capping peaks
        if threshold >= 1.0:
            max_value = float(np.max(np.abs(normalized)))
            if max_value > 1.0:
                cap_scale = 1.0 / max_value
                normalized *= cap_scale
                gain *= cap_scale
        return normalized.astype(array.dtype, copy=False), 1.0 / gain
    else:
        # Peak-normalize only if above threshold
        max_value = float(np.max(np.abs(array)))
        if max_value < epsilon:
            return array.astype(array.dtype, copy=True), 1.0
        if max_value > threshold:
            gain = threshold / max_value
            normalized = array * gain
            return normalized.astype(array.dtype, copy=False), 1.0 / gain
        else:
            return array.astype(array.dtype, copy=True), 1.0


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
