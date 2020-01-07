import numpy as np
from .log import Code, warning, info, debug, debug_line, ModuleError
from . import MainConfig
from .utils import to_db
from .dsp import amplify
from .stage_helpers import normalize_reference, analyze_levels, get_fir, convolve


def __match_levels(
        target: np.ndarray,
        reference: np.ndarray,
        config: MainConfig
) -> (np.ndarray, np.ndarray, float, np.ndarray, np.ndarray, np.ndarray, np.ndarray):
    debug_line()
    info(Code.INFO_MATCHING_LEVELS)

    debug(f'The maximum size of the analyzed piece: {config.max_piece_size} samples '
          f'or {config.max_piece_size / config.internal_sample_rate:.2f} seconds')

    reference, final_amplitude_coefficient = normalize_reference(reference, config)

    target_mid, target_side,\
        target_mid_loudest_pieces, target_side_loudest_pieces,\
        target_match_rms\
        = analyze_levels(target, 'TARGET', config)

    reference_mid, reference_side,\
        reference_mid_loudest_pieces, reference_side_loudest_pieces,\
        reference_match_rms\
        = analyze_levels(reference, 'REFERENCE', config)

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

    output, output_mid = convolve(target_mid, mid_fir, target_side, side_fir)

    return output, output_mid


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

    output, output_mid = __match_frequencies(
        target_mid, target_side,
        target_mid_loudest_pieces, reference_mid_loudest_pieces,
        target_side_loudest_pieces, reference_side_loudest_pieces,
        config
    )

    debug_line()
    info(Code.INFO_CORRECTING_LEVELS)

    debug_line()
    info(Code.INFO_FINALIZING)

    return output, output, output
