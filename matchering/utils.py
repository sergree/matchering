import os
import random
import string
import math
from datetime import timedelta


def get_temp_folder(results: list) -> str:
    first_result_file = results[0].file
    return os.path.dirname(os.path.abspath(first_result_file))


def random_str(size: int = 16) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=size))


def random_file(prefix: str = '', extension: str = 'wav') -> str:
    prefix = f'{prefix}-' if prefix else prefix
    return f'{prefix}{random_str()}.{extension}'


def __to_db_int(value: float) -> float:
    return 20 * math.log10(value)


def to_db(value: float) -> str:
    return f'{__to_db_int(value):.4f} dB'


def ms_to_samples(value: float, sample_rate: int) -> int:
    return int(sample_rate * value * 1e-3)


def make_odd(value: int) -> int:
    return value + 1 if not value & 1 else value


def time_str(length, sample_rate) -> str:
    return str(timedelta(seconds=length // sample_rate))
