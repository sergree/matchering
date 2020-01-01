from scipy import signal, interpolate
import numpy as np
import soundfile as sf
from resampy import resample
from time import time
import os
import math
from matchering.loader import load


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
        target = load(target)

        # Check the target

        # Load the reference
        reference = load(reference)

        # Check the reference

        # Process

        # Save
