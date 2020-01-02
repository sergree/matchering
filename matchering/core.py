from scipy import signal, interpolate
import numpy as np
import soundfile as sf
from resampy import resample
from time import time
import os
import math
from matchering.loader import load
from matchering.log import Code
from matchering.log import get_handler
from matchering.exceptions import ModuleError


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
            debug=None,
            show_codes=False
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
        # self.log.warning(Code.WARNING_TARGET_IS_CLIPPING)
        # self.log.info(Code.INFO_CORRECTING_LEVELS)

        self.log.warning(get_handler(show_codes=True)(Code.WARNING_TARGET_IS_CLIPPING))
        self.log.info(get_handler()(Code.INFO_CORRECTING_LEVELS))

        self.log.debug('Debug!')
        raise ModuleError(Code.ERROR_REFERENCE_LENGTH_LENGTH_IS_EXCEEDED)

        # Save
