# -*- coding: utf-8 -*-

"""
Auralis Preview Creator
~~~~~~~~~~~~~~~~~~~~~~

Preview generation for A/B comparison

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

import numpy as np
from .logging import debug, info


def create_preview(target: np.ndarray, result: np.ndarray, config, preview_target=None, preview_result=None):
    """
    Create preview files for A/B comparison

    Args:
        target: Original target audio
        result: Processed result audio
        config: Processing configuration
        preview_target: Preview target result object
        preview_result: Preview result result object
    """
    debug("Creating preview files")

    # For now, just save the full files
    # TODO: Implement proper preview creation with shorter duration
    if preview_target:
        from ..io.saver import save
        save(preview_target.file, target, config.internal_sample_rate, preview_target.subtype)

    if preview_result:
        from ..io.saver import save
        save(preview_result.file, result, config.internal_sample_rate, preview_result.subtype)

    info("Preview files created")