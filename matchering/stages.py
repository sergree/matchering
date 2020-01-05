import numpy as np

from .log import Code, warning, info, debug, ModuleError
from . import MainConfig


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

    info(Code.INFO_MATCHING_FREQS)

    info(Code.INFO_CORRECTING_LEVELS)

    info(Code.INFO_FINALIZING)

    return target, target, target
