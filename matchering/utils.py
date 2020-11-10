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
import random
import string
import math
from datetime import timedelta


def get_temp_folder(results: list) -> str:
    first_result_file = results[0].file
    return os.path.dirname(os.path.abspath(first_result_file))


def random_str(size: int = 16) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=size))


def random_file(prefix: str = "", extension: str = "wav") -> str:
    prefix = f"{prefix}-" if prefix else prefix
    return f"{prefix}{random_str()}.{extension}"


def __to_db_int(value: float) -> float:
    return 20 * math.log10(value)


def to_db(value: float) -> str:
    return f"{__to_db_int(value):.4f} dB"


def ms_to_samples(value: float, sample_rate: int) -> int:
    return int(sample_rate * value * 1e-3)


def make_odd(value: int) -> int:
    return value + 1 if not value & 1 else value


def time_str(length, sample_rate) -> str:
    return str(timedelta(seconds=length // sample_rate))
