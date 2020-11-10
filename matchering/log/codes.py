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

from enum import IntEnum


class Code(IntEnum):
    INFO_UPLOADING = 2001
    INFO_WAITING = 2002
    INFO_LOADING = 2003
    INFO_MATCHING_LEVELS = 2004
    INFO_MATCHING_FREQS = 2005
    INFO_CORRECTING_LEVELS = 2006
    INFO_FINALIZING = 2007
    INFO_EXPORTING = 2008
    INFO_MAKING_PREVIEWS = 2009
    INFO_COMPLETED = 2010

    INFO_TARGET_IS_MONO = 2101
    INFO_REFERENCE_IS_MONO = 2201
    INFO_REFERENCE_IS_RESAMPLED = 2202
    INFO_REFERENCE_IS_LOSSY = 2203

    WARNING_TARGET_IS_CLIPPING = 3001
    WARNING_TARGET_LIMITER_IS_APPLIED = 3002
    WARNING_TARGET_IS_RESAMPLED = 3003
    WARNING_TARGET_IS_LOSSY = 3004

    ERROR_TARGET_LOADING = 4001
    ERROR_TARGET_LENGTH_IS_EXCEEDED = 4002
    ERROR_TARGET_LENGTH_IS_TOO_SMALL = 4003
    ERROR_TARGET_NUM_OF_CHANNELS_IS_EXCEEDED = 4004
    ERROR_TARGET_EQUALS_REFERENCE = 4005

    ERROR_REFERENCE_LOADING = 4101
    ERROR_REFERENCE_LENGTH_LENGTH_IS_EXCEEDED = 4102
    ERROR_REFERENCE_LENGTH_LENGTH_TOO_SMALL = 4103
    ERROR_REFERENCE_NUM_OF_CHANNELS_IS_EXCEEDED = 4104

    ERROR_UNKNOWN = 4201
    ERROR_VALIDATION = 4202
