import numpy as np


def len_nda(array: np.ndarray) -> int:
    return array.shape[0]


def is_mono(array: np.ndarray) -> bool:
    return array.shape[1] == 1


def is_stereo(array: np.ndarray) -> bool:
    return array.shape[1] == 2


def mono_to_stereo(array: np.ndarray) -> np.ndarray:
    return np.repeat(array, repeats=2, axis=1)
