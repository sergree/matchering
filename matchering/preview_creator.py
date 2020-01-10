import numpy as np

from .log import Code, info, debug, debug_line
from .dsp import size, strided_app_2d, batch_rms_2d, fade
from . import MainConfig, Result
from .saver import save


def create_preview(
        target: np.ndarray,
        result: np.ndarray,
        config: MainConfig,
        preview_target: Result,
        preview_result: Result
) -> None:
    debug_line()
    info(Code.INFO_MAKING_PREVIEWS)

    target_pieces = strided_app_2d(target, config.preview_size, config.preview_analysis_step)
    result_pieces = strided_app_2d(result, config.preview_size, config.preview_analysis_step)

    result_loudest_piece_idx = np.argmax(batch_rms_2d(result_pieces))

    target_piece = target_pieces[result_loudest_piece_idx]
    result_piece = result_pieces[result_loudest_piece_idx]

    if size(result) != size(result_piece):
        fade_size = min(config.preview_fade_size, size(result_piece) // config.preview_fade_coefficient)
        target_piece, result_piece = fade(target_piece, fade_size), fade(result_piece, fade_size)

    if preview_target:
        save(preview_target.file, target_piece, config.internal_sample_rate, preview_target.subtype)

    if preview_result:
        save(preview_result.file, result_piece, config.internal_sample_rate, preview_result.subtype)
