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
    return np.vstack((mid_array + side_array, mid_array - side_array)).T


def unfold(array: np.ndarray, piece_size: int, divisions: int) -> np.ndarray:
    # (len(array),) -> (divisions, piece_size)
    return array[:piece_size * divisions].reshape(-1, piece_size)


def rms(array: np.ndarray) -> float:
    return np.sqrt(array @ array / array.shape[0])


def batch_rms(array: np.ndarray):
    piece_size = array.shape[1]
    # (divisions, piece_size) -> (divisions, 1, piece_size)
    multiplicand = array[:, None, :]
    # (divisions, piece_size) -> (divisions, piece_size, 1)
    multiplier = array[..., None]
    return np.sqrt(np.squeeze(multiplicand @ multiplier) / piece_size)


def amplify(array: np.ndarray, gain: float) -> np.ndarray:
    return array * gain


def smooth_lowess(
        array: np.ndarray,
        frac: float,
        it: int,
        delta: float
) -> np.ndarray:
    return sm.nonparametric.lowess(
        array,
        np.linspace(0, 1, len(array)),
        frac=frac,
        it=it,
        delta=delta
    )[:, 1]


def clip(array: np.ndarray) -> np.ndarray:
    return np.clip(array, -1, 1)
