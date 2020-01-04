import os
import numpy as np
import soundfile as sf
import subprocess

from .log import Code, debug, ModuleError
from .utils import random_file


codes_error_loading = {
    'TARGET': Code.ERROR_TARGET_LOADING,
    'REFERENCE': Code.ERROR_REFERENCE_LOADING,
}


def load(file: str, file_type: str, temp_folder: str) -> (np.ndarray, int):
    file_type = file_type.upper()
    sound, sample_rate = None, None
    debug(f'Loading {file_type} file: \'{file}\'...')
    try:
        sound, sample_rate = sf.read(file)
    except RuntimeError as e:
        debug(e)
        if 'unknown format' in str(e):
            sound, sample_rate = load_with_ffmpeg(file, temp_folder)
    if sound is None or sample_rate is None:
        raise ModuleError(codes_error_loading[file_type])
    debug(f'{file_type} file is loaded')
    return sound, sample_rate


def load_with_ffmpeg(file: str, temp_folder: str) -> (np.ndarray, int):
    sound, sample_rate = None, None
    debug(f'Trying to load \'{file}\' with ffmpeg...')
    temp_file = os.path.join(temp_folder, random_file(prefix='temp'))
    with open(os.devnull, 'w') as devnull:
        try:
            subprocess.check_call(
                [
                    'ffmpeg',
                    '-i',
                    file,
                    temp_file
                ],
                stdout=devnull,
                stderr=devnull
            )
            sound, sample_rate = sf.read(temp_file)
            os.remove(temp_file)
        except FileNotFoundError:
            debug('ffmpeg is not found in the system! '
                  'Download, install and add it to PATH: https://www.ffmpeg.org/download.html')
        except subprocess.CalledProcessError:
            debug(f'ffmpeg cannot convert \'{file}\' to .wav!')
    return sound, sample_rate
