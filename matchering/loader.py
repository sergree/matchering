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

import os
import numpy as np
import soundfile as sf
import subprocess

from .log import Code, warning, info, debug, ModuleError
from .utils import random_file


def load(file: str, file_type: str, temp_folder: str) -> (np.ndarray, int):
    file_type = file_type.upper()
    sound, sample_rate = None, None
    debug(f"Loading the {file_type} file: '{file}'...")
    try:
        sound, sample_rate = sf.read(file, always_2d=True)
    except RuntimeError as e:
        debug(e)
        if "unknown format" in str(e):
            sound, sample_rate = __load_with_ffmpeg(file, file_type, temp_folder)
    if sound is None or sample_rate is None:
        if file_type == "TARGET":
            raise ModuleError(Code.ERROR_TARGET_LOADING)
        else:
            raise ModuleError(Code.ERROR_REFERENCE_LOADING)
    debug(f"The {file_type} file is loaded")
    return sound, sample_rate


def __load_with_ffmpeg(
    file: str, file_type: str, temp_folder: str
) -> (np.ndarray, int):
    sound, sample_rate = None, None
    debug(f"Trying to load '{file}' with ffmpeg...")
    temp_file = os.path.join(temp_folder, random_file(prefix="temp"))
    with open(os.devnull, "w") as devnull:
        try:
            subprocess.check_call(
                ["ffmpeg", "-i", file, temp_file], stdout=devnull, stderr=devnull
            )
            sound, sample_rate = sf.read(temp_file, always_2d=True)
            if file_type == "TARGET":
                warning(Code.WARNING_TARGET_IS_LOSSY)
            else:
                info(Code.INFO_REFERENCE_IS_LOSSY)
            os.remove(temp_file)
        except FileNotFoundError:
            debug(
                "ffmpeg is not found in the system! "
                "Download, install and add it to PATH: https://www.ffmpeg.org/download.html"
            )
        except subprocess.CalledProcessError:
            debug(f"ffmpeg cannot convert '{file}' to .wav!")
    return sound, sample_rate
