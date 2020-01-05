import numpy as np


def length_nda(array: np.ndarray) -> int:
    return array.shape[0]


def channel_count(array: np.ndarray) -> int:
    return array.shape[1]


def is_mono(array: np.ndarray) -> bool:
    return array.shape[1] == 1


def is_stereo(array: np.ndarray) -> bool:
    return array.shape[1] == 2


def mono_to_stereo(array: np.ndarray) -> np.ndarray:
    return np.repeat(array, repeats=2, axis=1)


def count_max_peaks(array: np.ndarray) -> (float, int):
    max_value = np.abs(array).max()
    max_count = np.count_nonzero(
        np.logical_or(
            np.isclose(array, max_value),
            np.isclose(array, -max_value)
        )
    )
    return max_value, max_count


def lr_to_ms(array: np.ndarray) -> (np.ndarray, np.ndarray):
    array[:, 0] += array[:, 1]
    array[:, 0] *= 0.5
    mid = np.copy(array[:, 0])
    array[:, 0] -= array[:, 1]
    side = np.copy(array[:, 0])
    return mid, side


def ms_to_lr(mid_array: np.ndarray, side_array: np.ndarray) -> np.ndarray:
    return np.vstack((np.copy(mid_array + side_array), np.copy(mid_array - side_array))).T
