import numpy as np
from .log import Code, warning, info, debug, debug_line, ModuleError
from . import MainConfig
from .utils import to_db
from .dsp import amplify, clip
from .stage_helpers import normalize_reference, analyze_levels, get_fir, \
    convolve, get_average_rms, get_lpis_and_match_rms


def calculate_rms_coefficient(
        array_match_rms: float,
        reference_match_rms: float,
        epsilon: float
) -> float:
    rms_coefficient = reference_match_rms / max(epsilon, array_match_rms)
    debug(f'The RMS coefficient is: {to_db(rms_coefficient)}')
    return rms_coefficient


def calculate_rmsc_and_amplify_multiple(
        array_main: np.ndarray,
        array_additional: np.ndarray,
        array_main_match_rms: float,
        reference_match_rms: float,
        epsilon: float,
        name: str
) -> (float, np.ndarray, np.ndarray):
    name = name.upper()
    rms_coefficient = calculate_rms_coefficient(array_main_match_rms, reference_match_rms, epsilon)

    debug(f'Modifying the amplitudes of the {name} audio...')
    array_main = amplify(array_main, rms_coefficient)
    array_additional = amplify(array_additional, rms_coefficient)

    return rms_coefficient, array_main, array_additional


def __match_levels(
        target: np.ndarray,
        reference: np.ndarray,
        config: MainConfig
) -> (np.ndarray, np.ndarray, float, np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float):
    debug_line()
    info(Code.INFO_MATCHING_LEVELS)

    debug(f'The maximum size of the analyzed piece: {config.max_piece_size} samples '
          f'or {config.max_piece_size / config.internal_sample_rate:.2f} seconds')

    reference, final_amplitude_coefficient = normalize_reference(reference, config)

    target_mid, target_side,\
        target_mid_loudest_pieces, target_side_loudest_pieces,\
        target_match_rms, target_divisions, target_piece_size\
        = analyze_levels(target, 'target', config)

    reference_mid, reference_side,\
        reference_mid_loudest_pieces, reference_side_loudest_pieces,\
        reference_match_rms, *_\
        = analyze_levels(reference, 'reference', config)

    rms_coefficient, target_mid, target_side = calculate_rmsc_and_amplify_multiple(
        target_mid, target_side,
        target_match_rms, reference_match_rms,
        config.min_value, 'target'
    )

    debug('Modifying the amplitudes of the extracted loudest TARGET pieces...')
    target_mid_loudest_pieces = amplify(target_mid_loudest_pieces, rms_coefficient)
    target_side_loudest_pieces = amplify(target_side_loudest_pieces, rms_coefficient)

    return target_mid, target_side, final_amplitude_coefficient,\
        target_mid_loudest_pieces, target_side_loudest_pieces,\
        reference_mid_loudest_pieces, reference_side_loudest_pieces,\
        target_divisions, target_piece_size, reference_match_rms


def __match_frequencies(
        target_mid: np.ndarray,
        target_side: np.ndarray,
        target_mid_loudest_pieces: np.ndarray,
        reference_mid_loudest_pieces: np.ndarray,
        target_side_loudest_pieces: np.ndarray,
        reference_side_loudest_pieces: np.ndarray,
        config: MainConfig,
) -> (np.ndarray, np.ndarray):
    debug_line()
    info(Code.INFO_MATCHING_FREQS)

    mid_fir = get_fir(
        target_mid_loudest_pieces, reference_mid_loudest_pieces,
        'mid',
        config
    )
    side_fir = get_fir(
        target_side_loudest_pieces, reference_side_loudest_pieces,
        'side',
        config
    )

    result, result_mid = convolve(target_mid, mid_fir, target_side, side_fir)

    return result, result_mid


def __correct_levels(
        result: np.ndarray,
        result_mid: np.ndarray,
        target_divisions: int,
        target_piece_size: int,
        reference_match_rms: float,
        config: MainConfig
) -> np.ndarray:
    debug_line()
    info(Code.INFO_CORRECTING_LEVELS)
    name = 'result'

    for step in range(1, config.rms_correction_steps + 1):
        debug(f'Applying RMS correction #{step}...')
        result_mid_clipped = clip(result_mid)

        _, clipped_rmses, clipped_average_rms = get_average_rms(
            result_mid_clipped,
            target_piece_size,
            target_divisions,
            name
        )

        _, result_mid_clipped_match_rms = get_lpis_and_match_rms(clipped_rmses, clipped_average_rms)

        rms_coefficient, result_mid, result = calculate_rmsc_and_amplify_multiple(
            result_mid, result,
            result_mid_clipped_match_rms, reference_match_rms,
            config.min_value, name
        )

    return result


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
        reference_mid_loudest_pieces, reference_side_loudest_pieces, \
        target_divisions, target_piece_size, reference_match_rms\
        = __match_levels(target, reference, config)

    result, result_mid = __match_frequencies(
        target_mid, target_side,
        target_mid_loudest_pieces, reference_mid_loudest_pieces,
        target_side_loudest_pieces, reference_side_loudest_pieces,
        config
    )

    result = __correct_levels(
        result,
        result_mid,
        target_divisions,
        target_piece_size,
        reference_match_rms,
        config
    )

    debug_line()
    info(Code.INFO_FINALIZING)

    return result, result, result
