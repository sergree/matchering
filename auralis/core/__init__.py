# -*- coding: utf-8 -*-

"""
Auralis Core Processing
~~~~~~~~~~~~~~~~~~~~~~

Core audio processing and mastering algorithms

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Based on Matchering 2.0 by Sergree and contributors
"""

from .processor import process
from .config import Config

__all__ = ["process", "Config"]