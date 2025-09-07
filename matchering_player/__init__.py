# -*- coding: utf-8 -*-

"""
Matchering Player
~~~~~~~~~~~~~~~~~

Realtime Audio Matching and Mastering Media Player

:copyright: (C) 2024 Matchering Player Team  
:license: GPLv3, see LICENSE for more details.

Based on Matchering 2.0 by Sergree
"""

__title__ = "matchering-player"
__version__ = "0.1.0"
__author__ = "Matchering Player Team"
__license__ = "GPLv3"
__copyright__ = "Copyright (C) 2024 Matchering Player Team"

from .core.player import MatcheringPlayer
from .core.config import PlayerConfig
from .dsp.processor import RealtimeProcessor

__all__ = ["MatcheringPlayer", "PlayerConfig", "RealtimeProcessor"]
