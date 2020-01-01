from scipy import signal, interpolate
import numpy as np
import soundfile as sf
from resampy import resample
from time import time
import os
import math


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


class DSPModule:
    def __init__(
            self,
            warning=None,
            info=None,
            debug=None
    ):
        self.warning = warning if warning else self.__dummy
        self.info = info if info else self.__dummy
        self.debug = debug if debug else self.__dummy

    @staticmethod
    def __dummy(self, *args):
        pass

    def process(
            self,
            target: str,
            reference: str,
            results: list,
    ):
        # Load the target
        # Check the target
        # Load the reference
        # Check the reference
        self.warning('Warning!')
        self.info('Info!')
        self.debug('Debug!')
        pass
