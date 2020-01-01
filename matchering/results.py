import os
import soundfile as sf


class Result:
    def __init__(
            self,
            file: str,
            subtype: str,
            use_limiter: bool = True,
            normalize: bool = True,
    ):
        _, file_ext = os.path.splitext(file)
        file_ext = file_ext[1:].upper()
        if not sf.check_format(file_ext, subtype):
            raise TypeError(f'{file_ext} format doesn\'t have {subtype} subtype')
        self.file = file
        self.subtype = subtype
        self.use_limiter = use_limiter
        self.normalize = normalize


def pcm16(file: str):
    return Result(file, 'PCM_16')


def pcm24(file: str):
    return Result(file, 'PCM_24')
