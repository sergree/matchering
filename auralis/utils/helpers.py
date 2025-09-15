# -*- coding: utf-8 -*-

"""
Auralis Helper Functions
~~~~~~~~~~~~~~~~~~~~~~~~

General utility functions

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import tempfile
import os


def get_temp_folder(results):
    """
    Get a temporary folder for processing

    Args:
        results: List of result objects

    Returns:
        str: Path to temporary folder
    """
    return tempfile.gettempdir()