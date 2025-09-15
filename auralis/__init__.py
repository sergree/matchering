# -*- coding: utf-8 -*-

"""
Auralis - Real-time Audio Mastering Player
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unified Audio Processing and Real-time Mastering System

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Based on Matchering 2.0 by Sergree and contributors
"""

__title__ = "auralis"
__version__ = "1.0.0"
__author__ = "Auralis Team"
__license__ = "GPLv3"
__copyright__ = "Copyright (C) 2024 Auralis Team"

# Core processing functions
from .core.processor import process
from .core.config import Config

# Real-time player
from .player.audio_player import AudioPlayer
from .player.enhanced_audio_player import EnhancedAudioPlayer
from .player.config import PlayerConfig

# Results and output handling
from .io.results import Result, pcm16, pcm24

# Logging
from .utils.logging import set_log_handler as log

# Main exports
__all__ = [
    "process",           # Core batch processing
    "Config",           # Core configuration
    "AudioPlayer",      # Basic real-time player
    "EnhancedAudioPlayer",  # Advanced player with DSP
    "PlayerConfig",     # Player configuration
    "Result", "pcm16", "pcm24",  # Output formats
    "log",              # Logging
]