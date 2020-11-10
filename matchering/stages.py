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
from .log import Code, info, debug, debug_line
from . import Config
from .utils import to_db
from .dsp import amplify, normalize, clip
from .stage_helpers import (
    normalize_reference,
    analyze_levels,
    get_fir,
    convolve,
    get_average_rms,
    get_lpis_and_match_rms,
    get_rms_c_and_amplify_pair,
)
from .limiter import limit


def __match_levels(
    target: np.ndarray, reference: np.ndarray, config: Config
) -> (
    np.ndarray,
    np.ndarray,
    float,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
    float,
):
    debug_line()
    info(Code.INFO_MATCHING_LEVELS)

    debug(
        f"The maximum size of the analyzed piece: {config.max_piece_size} samples "
        f"or {config.max_piece_size / config.internal_sample_rate:.2f} seconds"
    )

    reference, final_amplitude_coefficient = normalize_reference(reference, config)

    (
        target_mid,
        target_side,
        target_mid_loudest_pieces,
        target_side_loudest_pieces,
        target_match_rms,
        target_divisions,
        target_piece_size,
    ) = analyze_levels(target, "target", config)

    (
        reference_mid,
        reference_side,
        reference_mid_loudest_pieces,
        reference_side_loudest_pieces,
        reference_match_rms,
        *_,
    ) = analyze_levels(reference, "reference", config)

    rms_coefficient, target_mid, target_side = get_rms_c_and_amplify_pair(
        target_mid,
        target_side,
        target_match_rms,
        reference_match_rms,
        config.min_value,
        "target",
    )

    debug("Modifying the amplitudes of the extracted loudest TARGET pieces...")
    target_mid_loudest_pieces = amplify(target_mid_loudest_pieces, rms_coefficient)
    target_side_loudest_pieces = amplify(target_side_loudest_pieces, rms_coefficient)

    return (
        target_mid,
        target_side,
        final_amplitude_coefficient,
        target_mid_loudest_pieces,
        target_side_loudest_pieces,
        reference_mid_loudest_pieces,
        reference_side_loudest_pieces,
        target_divisions,
        target_piece_size,
        reference_match_rms,
    )


def __match_frequencies(
    target_mid: np.ndarray,
    target_side: np.ndarray,
    target_mid_loudest_pieces: np.ndarray,
    reference_mid_loudest_pieces: np.ndarray,
    target_side_loudest_pieces: np.ndarray,
    reference_side_loudest_pieces: np.ndarray,
    config: Config,
) -> (np.ndarray, np.ndarray):
    debug_line()
    info(Code.INFO_MATCHING_FREQS)

    mid_fir = get_fir(
        target_mid_loudest_pieces, reference_mid_loudest_pieces, "mid", config
    )
    side_fir = get_fir(
        target_side_loudest_pieces, reference_side_loudest_pieces, "side", config
    )

    del (
        target_mid_loudest_pieces,
        reference_mid_loudest_pieces,
        target_side_loudest_pieces,
        reference_side_loudest_pieces,
    )

    result, result_mid = convolve(target_mid, mid_fir, target_side, side_fir)

    return result, result_mid


def __correct_levels(
    result: np.ndarray,
    result_mid: np.ndarray,
    target_divisions: int,
    target_piece_size: int,
    reference_match_rms: float,
    config: Config,
) -> np.ndarray:
    debug_line()
    info(Code.INFO_CORRECTING_LEVELS)

    for step in range(1, config.rms_correction_steps + 1):
        debug(f"Applying RMS correction #{step}...")
        result_mid_clipped = clip(result_mid)

        _, clipped_rmses, clipped_average_rms = get_average_rms(
            result_mid_clipped, target_piece_size, target_divisions, "result"
        )

        _, result_mid_clipped_match_rms = get_lpis_and_match_rms(
            clipped_rmses, clipped_average_rms
        )

        rms_coefficient, result_mid, result = get_rms_c_and_amplify_pair(
            result_mid,
            result,
            result_mid_clipped_match_rms,
            reference_match_rms,
            config.min_value,
            "result",
        )

    return result


def __finalize(
    result_no_limiter: np.ndarray,
    final_amplitude_coefficient: float,
    need_default: bool,
    need_no_limiter: bool,
    need_no_limiter_normalized: bool,
    config: Config,
) -> (np.ndarray, np.ndarray, np.ndarray):
    debug_line()
    info(Code.INFO_FINALIZING)

    result_no_limiter_normalized = None
    if need_no_limiter_normalized:
        result_no_limiter_normalized, coefficient = normalize(
            result_no_limiter,
            config.threshold,
            config.min_value,
            normalize_clipped=True,
        )
        debug(
            f"The amplitude of the normalized RESULT should be adjusted by {to_db(coefficient)}"
        )
        if not np.isclose(final_amplitude_coefficient, 1.0):
            debug(
                f"And by {to_db(final_amplitude_coefficient)} after applying some brickwall limiter to it"
            )

    result = None
    if need_default:
        result = limit(result_no_limiter, config)
        result = amplify(result, final_amplitude_coefficient)

    result_no_limiter = result_no_limiter if need_no_limiter else None

    return result, result_no_limiter, result_no_limiter_normalized


def main(
    target: np.ndarray,
    reference: np.ndarray,
    config: Config,
    need_default: bool = True,
    need_no_limiter: bool = False,
    need_no_limiter_normalized: bool = False,
) -> (np.ndarray, np.ndarray, np.ndarray):
    (
        target_mid,
        target_side,
        final_amplitude_coefficient,
        target_mid_loudest_pieces,
        target_side_loudest_pieces,
        reference_mid_loudest_pieces,
        reference_side_loudest_pieces,
        target_divisions,
        target_piece_size,
        reference_match_rms,
    ) = __match_levels(target, reference, config)

    del target, reference

    result_no_limiter, result_no_limiter_mid = __match_frequencies(
        target_mid,
        target_side,
        target_mid_loudest_pieces,
        reference_mid_loudest_pieces,
        target_side_loudest_pieces,
        reference_side_loudest_pieces,
        config,
    )

    del (
        target_mid,
        target_side,
        target_mid_loudest_pieces,
        reference_mid_loudest_pieces,
        target_side_loudest_pieces,
        reference_side_loudest_pieces,
    )

    result_no_limiter = __correct_levels(
        result_no_limiter,
        result_no_limiter_mid,
        target_divisions,
        target_piece_size,
        reference_match_rms,
        config,
    )

    del result_no_limiter_mid

    result, result_no_limiter, result_no_limiter_normalized = __finalize(
        result_no_limiter,
        final_amplitude_coefficient,
        need_default,
        need_no_limiter,
        need_no_limiter_normalized,
        config,
    )

    return result, result_no_limiter, result_no_limiter_normalized
