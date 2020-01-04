import os
import random
import string


def get_temp_folder(results: list) -> str:
    first_result_file = results[0].file
    return os.path.dirname(os.path.abspath(first_result_file))


def random_str(size: int = 16) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=size))


def random_file(prefix: str = '', extension: str = 'wav') -> str:
    prefix = f'{prefix}-' if prefix else prefix
    return f'{prefix}{random_str()}.{extension}'
