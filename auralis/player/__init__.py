# -*- coding: utf-8 -*-

"""
Auralis Player Module
~~~~~~~~~~~~~~~~~~~~~

Real-time audio player with live mastering

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Based on Matchering Player components
"""

from .audio_player import AudioPlayer
from .config import PlayerConfig

__all__ = ["AudioPlayer", "PlayerConfig"]