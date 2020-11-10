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

from .codes import Code


def __default(code: Code) -> str:
    return __en[code]


def __verbose(code: Code) -> str:
    return f"{code}: {__en[code]}"


def get_explanation_handler(show_codes: bool = False):
    return __verbose if show_codes else __default


__en = {
    Code.INFO_UPLOADING: "Uploading files",
    Code.INFO_WAITING: "Queued for processing",
    Code.INFO_LOADING: "Loading and analysis",
    Code.INFO_MATCHING_LEVELS: "Matching levels",
    Code.INFO_MATCHING_FREQS: "Matching frequencies",
    Code.INFO_CORRECTING_LEVELS: "Correcting levels",
    Code.INFO_FINALIZING: "Final processing and saving",
    Code.INFO_EXPORTING: "Exporting various audio formats",
    Code.INFO_MAKING_PREVIEWS: "Making previews",
    Code.INFO_COMPLETED: "The task is completed",
    Code.INFO_TARGET_IS_MONO: "The TARGET audio is mono. Converting it to stereo...",
    Code.INFO_REFERENCE_IS_MONO: "The REFERENCE audio is mono. Converting it to stereo...",
    Code.INFO_REFERENCE_IS_RESAMPLED: "The REFERENCE audio was resampled",
    Code.INFO_REFERENCE_IS_LOSSY: "Presumably the REFERENCE audio format is lossy",
    Code.WARNING_TARGET_IS_CLIPPING: "Audio clipping is detected in the TARGET file. "
    "It is highly recommended to use the non-clipping version",
    Code.WARNING_TARGET_LIMITER_IS_APPLIED: "The applied limiter is detected in the TARGET file. "
    "It is highly recommended to use the version without a limiter",
    Code.WARNING_TARGET_IS_RESAMPLED: "The TARGET audio sample rate and internal sample rate were different. "
    "The TARGET audio was resampled",
    Code.WARNING_TARGET_IS_LOSSY: "Presumably the TARGET audio format is lossy. "
    "It is highly recommended to use lossless audio formats (WAV, FLAC, AIFF)",
    Code.ERROR_TARGET_LOADING: "Audio stream error in the TARGET file",
    Code.ERROR_TARGET_LENGTH_IS_EXCEEDED: "Track length is exceeded in the TARGET file",
    Code.ERROR_TARGET_LENGTH_IS_TOO_SMALL: "The track length is too small in the TARGET file",
    Code.ERROR_TARGET_NUM_OF_CHANNELS_IS_EXCEEDED: "The number of channels exceeded in the TARGET file",
    Code.ERROR_TARGET_EQUALS_REFERENCE: "The TARGET and REFERENCE files are the same. "
    "They must be different so that Matchering makes sense",
    Code.ERROR_REFERENCE_LOADING: "Audio stream error in the REFERENCE file",
    Code.ERROR_REFERENCE_LENGTH_LENGTH_IS_EXCEEDED: "Track length is exceeded in the REFERENCE file",
    Code.ERROR_REFERENCE_LENGTH_LENGTH_TOO_SMALL: "The track length is too small in the REFERENCE file",
    Code.ERROR_REFERENCE_NUM_OF_CHANNELS_IS_EXCEEDED: "The number of channels exceeded in the REFERENCE file",
    Code.ERROR_UNKNOWN: "Unknown error",
    Code.ERROR_VALIDATION: "Validation failed! Please let the developers know about this error!",
}
