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
import soundfile as sf

from .log import debug


def save(
    file: str, result: np.ndarray, sample_rate: int, subtype: str, name: str = "result"
) -> None:
    name = name.upper()
    debug(f"Saving the {name} {sample_rate} Hz Stereo {subtype} to: '{file}'...")
    sf.write(file, result, sample_rate, subtype)
    debug(f"'{file}' is saved")
