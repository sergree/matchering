import numpy as np
import soundfile as sf

from .log import debug


def save(
        file: str,
        result: np.ndarray,
        sample_rate: int,
        subtype: str,
        name: str = 'result'
) -> None:
    name = name.upper()
    debug(f'Saving the {name} {sample_rate} Hz Stereo {subtype} to: \'{file}\'...')
    sf.write(file, result, sample_rate, subtype)
    debug(f'\'{file}\' is saved')
