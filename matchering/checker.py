import numpy as np
from resampy import resample
from datetime import timedelta

from .log import Code, warning, info, debug, ModuleError
from . import MainConfig
from .dsp import length_nda, is_mono, is_stereo, mono_to_stereo, count_max_peaks


def __check_sample_rate(
        array: np.ndarray,
        sample_rate: int,
        required_sample_rate: int,
        log_handler,
        log_code: Code
) -> (np.ndarray, int):
    if sample_rate != required_sample_rate:
        array = resample(array, sample_rate, required_sample_rate, axis=0)
        log_handler(log_code)
    return array, required_sample_rate


def __check_length(
        array: np.ndarray,
        sample_rate: int,
        max_length: int,
        min_length: int,
        name: str,
        error_code_max: Code,
        error_code_min: Code
) -> None:
    length = length_nda(array)
    debug(f'{name} audio length: {length} samples ({timedelta(seconds=length // sample_rate)})')
    if length > max_length:
        raise ModuleError(error_code_max)
    elif length < min_length:
        raise ModuleError(error_code_min)


def __check_channels(
        array: np.ndarray,
        info_code_mono: Code,
        error_code_not_stereo: Code,
) -> np.ndarray:
    if is_mono(array):
        info(info_code_mono)
        array = mono_to_stereo(array)
    elif not is_stereo(array):
        raise ModuleError(error_code_not_stereo)
    return array


def __check_clipping_limiting(
        array: np.ndarray,
        clipping_count_threshold: int,
        limiting_count_threshold: int,
        warning_code_clipping: Code,
        warning_code_limiting: Code,
) -> None:
    max_value, max_count = count_max_peaks(array)
    if max_count > clipping_count_threshold:
        if np.isclose(max_value, 1.):
            warning(warning_code_clipping)
        elif max_count > limiting_count_threshold:
            warning(warning_code_limiting)


def check(array: np.ndarray, sample_rate: int, config: MainConfig, audio_type: str) -> (np.ndarray, int):
    audio_type = audio_type.upper()

    array, sample_rate = __check_sample_rate(
        array,
        sample_rate,
        config.internal_sample_rate,
        warning if audio_type == 'TARGET' else info,
        Code.WARNING_TARGET_IS_RESAMPLED if audio_type == 'TARGET'
        else Code.INFO_REFERENCE_IS_RESAMPLED
    )

    __check_length(
        array,
        sample_rate,
        config.max_length * sample_rate,
        config.fft_size,
        audio_type,
        Code.ERROR_TARGET_LENGTH_IS_EXCEEDED if audio_type == 'TARGET'
        else Code.ERROR_REFERENCE_LENGTH_LENGTH_IS_EXCEEDED,
        Code.ERROR_TARGET_LENGTH_IS_TOO_SMALL if audio_type == 'TARGET'
        else Code.ERROR_REFERENCE_LENGTH_LENGTH_TOO_SMALL
    )

    array = __check_channels(
        array,
        Code.INFO_TARGET_IS_MONO if audio_type == 'TARGET' else Code.INFO_REFERENCE_IS_MONO,
        Code.ERROR_TARGET_NUM_OF_CHANNELS_IS_EXCEEDED if audio_type == 'TARGET'
        else Code.ERROR_REFERENCE_NUM_OF_CHANNELS_IS_EXCEEDED
    )

    if audio_type == 'TARGET':
        __check_clipping_limiting(
            array,
            config.clipping_count_threshold,
            config.limiting_count_threshold,
            Code.WARNING_TARGET_IS_CLIPPING,
            Code.WARNING_TARGET_LIMITER_IS_APPLIED
        )

    return array, sample_rate


def check_equality(target: np.ndarray, reference: np.ndarray) -> None:
    if target.shape == reference.shape and np.allclose(target, reference):
        raise ModuleError(Code.ERROR_TARGET_EQUALS_REFERENCE)
