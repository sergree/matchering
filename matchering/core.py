from scipy import signal, interpolate
import numpy as np
import soundfile as sf
from resampy import resample
from time import time
import os
import math
from matchering.loader import load


class Log:
    def __init__(self, warning, info, debug):
        self.warning = warning
        self.info = info
        self.debug = debug


class DSPModule:
    def __init__(
            self,
            log=None,
            warning=None,
            info=None,
            debug=None
    ):
        log = self.__check_empty(log, lambda *args: None)
        self.log = Log(
            self.__check_empty(warning, log),
            self.__check_empty(info, log),
            self.__check_empty(debug, log)
        )

    @staticmethod
    def __check_empty(explicit_handler, default_handler):
        return explicit_handler if explicit_handler else default_handler

    def process(
            self,
            target: str,
            reference: str,
            results: list,
    ):
        # Load the target
        target = load(target, self.log)

        # Check the target

        # Load the reference
        reference = load(reference, self.log)

        # Check the reference

        # Process
        self.log.warning('Warning!')
        self.log.info('Info!')
        self.log.debug('Debug!')

        # Save
