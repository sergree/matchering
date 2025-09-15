# -*- coding: utf-8 -*-

"""
Auralis I/O Module
~~~~~~~~~~~~~~~~~

Audio input/output and result handling

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

from .loader import load
from .saver import save
from .results import Result, pcm16, pcm24

__all__ = ["load", "save", "Result", "pcm16", "pcm24"]