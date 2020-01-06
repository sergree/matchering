import numpy as np

from .log import Code, warning, info, debug, debug_line, ModuleError
from . import MainConfig
from .utils import to_db
from .dsp import lr_to_ms, ms_to_lr, size, unfold, batch_rms, rms, amplify


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
    array_size = size(array)
    divisions = int(array_size / max_piece_size) + 1
    debug(f'The {name} will be didived into {divisions} pieces')
    part_size = int(array_size / divisions)
    debug(f'One piece of the {name} has a length of {part_size} samples or {part_size / sample_rate:.2f} seconds')
    return array_size, divisions, part_size


def __extract_loudest_pieces(
        rmses: np.ndarray,
        average_rms: float,
        unfolded_mid: np.ndarray,
        unfolded_side: np.ndarray,
        name: str,
) -> (np.ndarray, np.ndarray, float):
    debug(f'Extracting the loudest pieces of the {name} audio '
          f'with the RMS value more than average {to_db(average_rms)}...')
    loudest_piece_idxs = np.where(rmses >= average_rms)
    mid_loudest_pieces = unfolded_mid[loudest_piece_idxs]
    side_loudest_pieces = unfolded_side[loudest_piece_idxs]
    loudest_rmses = rmses[loudest_piece_idxs]
    match_rms = rms(loudest_rmses)
    return mid_loudest_pieces, side_loudest_pieces, match_rms


def __analyze_levels(
        array: np.ndarray,
        name: str,
        config: MainConfig,
) -> (np.ndarray, np.ndarray, np.ndarray, np.ndarray, float):
    debug(f'Calculating mid and side channels of the {name}...')
    mid, side = lr_to_ms(array)
    del array

    array_size, divisions, piece_size = __calculate_piece_sizes(
        mid,
        config.max_piece_size,
        name,
        config.internal_sample_rate
    )

    unfolded_mid = unfold(mid, piece_size, divisions)
    unfolded_side = unfold(side, piece_size, divisions)

    debug(f'Calculating RMSes of the {name} pieces...')
    rmses = batch_rms(unfolded_mid)
    average_rms = rms(rmses)

    mid_loudest_pieces, side_loudest_pieces, match_rms = __extract_loudest_pieces(
        rmses,
        average_rms,
        unfolded_mid,
        unfolded_side,
        name
    )

    return mid, side, mid_loudest_pieces, side_loudest_pieces, match_rms


def __match_levels(
        target: np.ndarray,
        reference: np.ndarray,
        config: MainConfig
) -> (np.ndarray, np.ndarray, float, np.ndarray, np.ndarray, np.ndarray, np.ndarray):
    debug_line()
    info(Code.INFO_MATCHING_LEVELS)

    debug(f'The maximum size of the analyzed piece: {config.max_piece_size} samples '
          f'or {config.max_piece_size / config.internal_sample_rate:.2f} seconds')

    reference, final_amplitude_coefficient = __normalize_reference(reference, config)

    target_mid, target_side,\
        target_mid_loudest_pieces, target_side_loudest_pieces,\
        target_match_rms\
        = __analyze_levels(target, 'TARGET', config)

    reference_mid, reference_side,\
        reference_mid_loudest_pieces, reference_side_loudest_pieces,\
        reference_match_rms\
        = __analyze_levels(reference, 'REFERENCE', config)

    rms_coefficient = reference_match_rms / max(config.min_value, target_match_rms)
    debug(f'The RMS coefficient is: {to_db(rms_coefficient)}')

    debug('Modifying the amplitudes of the TARGET audio...')
    target_mid = amplify(target_mid, rms_coefficient)
    target_side = amplify(target_side, rms_coefficient)

    debug('Modifying the amplitudes of the extracted loudest TARGET pieces...')
    target_mid_loudest_pieces = amplify(target_mid_loudest_pieces, rms_coefficient)
    target_side_loudest_pieces = amplify(target_side_loudest_pieces, rms_coefficient)

    return target_mid, target_side, final_amplitude_coefficient,\
        target_mid_loudest_pieces, target_side_loudest_pieces,\
        reference_mid_loudest_pieces, reference_side_loudest_pieces


def __match_frequencies():
    debug_line()
    info(Code.INFO_MATCHING_FREQS)


def main(
        target: np.ndarray,
        reference: np.ndarray,
        config: MainConfig,
        need_default: bool = True,
        need_no_limiter: bool = False,
        need_no_limiter_normalized: bool = False,
) -> (np.ndarray, np.ndarray, np.ndarray):

    target_mid, target_side, final_amplitude_coefficient,\
        target_mid_loudest_pieces, target_side_loudest_pieces,\
        reference_mid_loudest_pieces, reference_side_loudest_pieces\
        = __match_levels(target, reference, config)

    __match_frequencies()

    debug_line()
    info(Code.INFO_CORRECTING_LEVELS)

    debug_line()
    info(Code.INFO_FINALIZING)

    return target_mid, target_mid, target_mid
