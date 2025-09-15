# -*- coding: utf-8 -*-

"""
Auralis Player Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration for real-time audio player

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering Player components
"""


class PlayerConfig:
    """Configuration for the real-time audio player"""

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 4410,
        enable_level_matching: bool = True,
        enable_frequency_matching: bool = False,
        enable_stereo_width: bool = False,
        enable_auto_mastering: bool = False,
        enable_advanced_smoothing: bool = True,
        max_db_change_per_second: float = 2.0,
    ):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.enable_level_matching = enable_level_matching
        self.enable_frequency_matching = enable_frequency_matching
        self.enable_stereo_width = enable_stereo_width
        self.enable_auto_mastering = enable_auto_mastering
        self.enable_advanced_smoothing = enable_advanced_smoothing
        self.max_db_change_per_second = max_db_change_per_second

    def __repr__(self):
        return (f"PlayerConfig(sample_rate={self.sample_rate}, "
                f"buffer_size={self.buffer_size}, "
                f"level_matching={self.enable_level_matching})")