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
            warning=None,
            info=None,
            debug=None
    ):
        self.log = Log(
            self.__check_empty(warning),
            self.__check_empty(info),
            self.__check_empty(debug)
        )

    @staticmethod
    def __check_empty(handler):
        return handler if handler else lambda *args: None

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

        # Save
