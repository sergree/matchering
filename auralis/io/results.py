# -*- coding: utf-8 -*-

"""
Auralis Results and Output Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Result types and output format specifications

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import os
import soundfile as sf


class Result:
    """Represents an output result with format specifications"""

    def __init__(
        self,
        file: str,
        subtype: str = 'PCM_16',
        use_limiter: bool = True,
        normalize: bool = False
    ):
        """
        Initialize a Result object

        Args:
            file: Output file path
            subtype: Audio format subtype (PCM_16, PCM_24, etc.)
            use_limiter: Whether to apply limiting
            normalize: Whether to normalize the output
        """
        _, file_ext = os.path.splitext(file)
        file_ext = file_ext[1:].upper()

        if not sf.check_format(file_ext):
            raise TypeError(f"{file_ext} format is not supported")
        if not sf.check_format(file_ext, subtype):
            raise TypeError(f"{file_ext} format does not have {subtype} subtype")

        self.file = file
        self.subtype = subtype
        self.use_limiter = use_limiter
        self.normalize = normalize

    def __repr__(self):
        return (f"Result(file='{self.file}', subtype='{self.subtype}', "
                f"use_limiter={self.use_limiter}, normalize={self.normalize})")


def pcm16(file: str) -> Result:
    """Create a 16-bit PCM result"""
    return Result(file, "PCM_16")


def pcm24(file: str) -> Result:
    """Create a 24-bit PCM result"""
    return Result(file, "PCM_24")