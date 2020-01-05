import numpy as np

from .log import Code, warning, info, debug, ModuleError
from . import MainConfig
from .utils import to_db
from .dsp import lr_to_ms, ms_to_lr, length_nda


def __normalize_reference(
        reference: np.ndarray,
        config: MainConfig
) -> (np.ndarray, float):
    debug('Normalizing the REFERENCE...')
    reference_max_value = np.abs(reference).max()
    final_amplitude_coefficient = 1.
    if reference_max_value >= config.threshold:
        debug('The REFERENCE was not changed. There is no final amplitude coefficient')
    else:
        final_amplitude_coefficient = max(config.min_value, reference_max_value / config.threshold)
        reference /= final_amplitude_coefficient
        debug(f'The REFERENCE was normalized. '
              f'Final amplitude coefficient for the TARGET audio is: {to_db(final_amplitude_coefficient)}')
    return reference, final_amplitude_coefficient


def __calculate_piece_sizes(
        array: np.ndarray,
        max_piece_size: int,
        name: str,
        sample_rate: int,
) -> (int, int, int):
    size = length_nda(array)
    divisions = int(size / max_piece_size) + 1
    debug(f'The {name} will be didived into {divisions} pieces')
    part_size = int(size / divisions)
    debug(f'One piece of the {name} has a length of {part_size} samples or {part_size / sample_rate:.2f} seconds')
    return size, divisions, part_size


def main(
        target: np.ndarray,
        reference: np.ndarray,
        config: MainConfig,
        need_default: bool = True,
        need_no_limiter: bool = False,
        need_no_limiter_normalized: bool = False,
) -> (np.ndarray, np.ndarray, np.ndarray):
    info(Code.INFO_MATCHING_LEVELS)

    debug(f'The maximum size of the analyzed piece: {config.max_piece_size} samples '
          f'or {config.max_piece_size / config.internal_sample_rate:.2f} seconds')

    reference, final_amplitude_coefficient = __normalize_reference(reference, config)

    debug('Calculating mid and side channels of the TARGET...')
    target_mid, target_side = lr_to_ms(target)
    debug('Calculating mid and side channels of the REFERENCE...')
    reference_mid, reference_side = lr_to_ms(reference)
    del target, reference

    target_size, target_divisions, target_part_size = __calculate_piece_sizes(
        target_mid,
        config.max_piece_size,
        'TARGET',
        config.internal_sample_rate
    )
    reference_size, reference_divisions, reference_part_size = __calculate_piece_sizes(
        reference_mid,
        config.max_piece_size,
        'REFERENCE',
        config.internal_sample_rate
    )

    info(Code.INFO_MATCHING_FREQS)

    info(Code.INFO_CORRECTING_LEVELS)

    info(Code.INFO_FINALIZING)

    return target_mid, target_mid, target_mid
