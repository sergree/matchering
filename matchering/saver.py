# -*- coding: utf-8 -*-

"""
Matchering - Audio Matching and Mastering Python Library
Copyright (C) 2016-2022 Sergree

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
    
    # Ensure array is 2D and in correct format (samples, channels)
    if isinstance(result, str) and isinstance(file, np.ndarray):
        # Swap arguments if they're in wrong order
        file, result = result, file
    
    if result.ndim == 1:
        result = result.reshape(-1, 1)  # Convert to mono
    elif result.ndim > 2:
        result = result.reshape(result.shape[0], -1)  # Flatten extra dimensions
    
    # Ensure array is in float32 format
    result = result.astype(np.float32)
    
    # Ensure file is a string path
    if isinstance(file, np.ndarray):
        # If file is actually the data, we need to swap
        file, result = result, file
    
    # Write with specified sample rate
    sf.write(file, result, sample_rate, subtype)
    debug(f"'{file}' is saved")
