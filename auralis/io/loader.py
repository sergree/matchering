# -*- coding: utf-8 -*-

"""
Auralis Audio Loader
~~~~~~~~~~~~~~~~~~~~

Audio file loading and validation

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import numpy as np
import soundfile as sf
from ..utils.logging import debug, info, Code


def load(file_path: str, file_type: str = "audio", temp_folder: str = None):
    """
    Load an audio file

    Args:
        file_path: Path to the audio file
        file_type: Type of file being loaded ("target", "reference", or "audio")
        temp_folder: Temporary folder for processing (unused for now)

    Returns:
        tuple: (audio_data, sample_rate)
    """
    debug(f"Loading {file_type} file: {file_path}")

    try:
        # Load audio file using SoundFile
        audio_data, sample_rate = sf.read(file_path, dtype=np.float32, always_2d=True)

        # Ensure stereo
        if audio_data.shape[1] == 1:
            # Convert mono to stereo
            audio_data = np.column_stack([audio_data[:, 0], audio_data[:, 0]])
        elif audio_data.shape[1] > 2:
            # Convert multi-channel to stereo (take first two channels)
            audio_data = audio_data[:, :2]

        info(f"Loaded {file_type}: {audio_data.shape[0]} samples, {sample_rate} Hz")
        return audio_data, sample_rate

    except Exception as e:
        raise RuntimeError(f"Failed to load {file_type} file '{file_path}': {e}")