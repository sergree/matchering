# -*- coding: utf-8 -*-

"""
Matchering Stages
~~~~~~~~~~~~~~~~~~~~~

Internal Matchering processing stage helpers.

:copyright: (C) 2016-2021 Sergree
:license: GPLv3, see LICENSE for more details.

"""

from .match_levels import (
    normalize_reference,
    analyze_levels,
    get_average_rms,
    get_lpis_and_match_rms,
    get_rms_c_and_amplify_pair,
)
from .match_frequencies import get_fir, convolve
