# -*- coding: utf-8 -*-

"""
Auralis Core Audio Processor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Main audio processing and mastering engine

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.

Refactored from Matchering 2.0 by Sergree and contributors
"""

from ..utils.logging import Code, info, debug, debug_line, ModuleError
from .config import Config
from ..io.results import Result
from ..io.loader import load
from ..dsp.stages import main
from ..io.saver import save
from ..utils.preview_creator import create_preview
from ..utils.helpers import get_temp_folder
from ..utils.checker import check, check_equality
from ..dsp.basic import channel_count, size


def process(
    target: str,
    reference: str,
    results: list,
    config: Config = None,
    preview_target: Result = None,
    preview_result: Result = None,
):
    """
    Process audio files with reference-based mastering

    Args:
        target: Path to target audio file to be mastered
        reference: Path to reference audio file for matching
        results: List of Result objects or file paths for output
        config: Processing configuration (optional)
        preview_target: Preview target result (optional)
        preview_result: Preview result output (optional)
    """
    if config is None:
        config = Config()

    # Ensure results is a list
    if not isinstance(results, list):
        results = [results]

    # Convert string paths to Result objects with default parameters
    results = [
        res if isinstance(res, Result) else Result(
            res,  # File path
            subtype='PCM_16',  # Use PCM_16 as default format
            use_limiter=True,  # Use limiter by default
            normalize=False  # Don't normalize by default
        )
        for res in results
    ]

    debug("Auralis - Real-time Audio Mastering Engine")
    debug("Based on Matchering 2.0 - https://github.com/sergree/matchering")
    debug_line()
    info(Code.INFO_LOADING)

    if not results:
        raise RuntimeError("The result list is empty")

    # Get a temporary folder for converting audio files
    temp_folder = config.temp_folder if config.temp_folder else get_temp_folder(results)

    # Load both files and capture original target rate for output
    target_audio, target_sample_rate = load(target, "target", temp_folder)
    output_sample_rate = target_sample_rate  # Save original target rate for output

    # Load reference
    reference_audio, reference_sample_rate = load(reference, "reference", temp_folder)

    # Set internal rate to the maximum for best quality
    config.internal_sample_rate = max(target_sample_rate, reference_sample_rate)
    debug(f"Using internal sample rate: {config.internal_sample_rate} Hz")

    # Analyze target and reference, resampling if needed
    target_audio, _ = check(target_audio, target_sample_rate, config, "target")
    reference_audio, _ = check(reference_audio, reference_sample_rate, config, "reference")

    # Analyze the target and the reference together
    if not config.allow_equality:
        check_equality(target_audio, reference_audio)

    # Always use target's sample rate as the output rate
    output_sample_rate = target_sample_rate

    # Use highest rate for internal processing to maintain quality
    config.internal_sample_rate = max(target_sample_rate, reference_sample_rate)
    debug(f"Using internal sample rate: {config.internal_sample_rate} Hz")
    debug(f"Output will use target sample rate: {output_sample_rate} Hz")

    # Validation of the most important conditions
    if (
        not (target_sample_rate == reference_sample_rate)  # Files must match
        or not (channel_count(target_audio) == channel_count(reference_audio) == 2)
        or not (size(target_audio) > config.fft_size and size(reference_audio) > config.fft_size)
    ):
        raise ModuleError(Code.ERROR_VALIDATION)

    # Process using the main DSP pipeline
    result, result_no_limiter, result_no_limiter_normalized = main(
        target_audio,
        reference_audio,
        config,
        need_default=any(rr.use_limiter for rr in results),
        need_no_limiter=any(not rr.use_limiter and not rr.normalize for rr in results),
        need_no_limiter_normalized=any(
            not rr.use_limiter and rr.normalize for rr in results
        ),
    )

    # Clean up memory
    del reference_audio
    if not (preview_target or preview_result):
        del target_audio

    debug_line()
    info(Code.INFO_EXPORTING)

    # Save all requested results
    for required_result in results:
        if required_result.use_limiter:
            correct_result = result
        else:
            if required_result.normalize:
                correct_result = result_no_limiter_normalized
            else:
                correct_result = result_no_limiter
        save(
            required_result.file,
            correct_result,
            output_sample_rate,  # Use original target rate for output
            required_result.subtype,
        )

    # Creating a preview (if needed)
    if preview_target or preview_result:
        result = next(
            item
            for item in [result, result_no_limiter, result_no_limiter_normalized]
            if item is not None
        )
        create_preview(target_audio, result, config, preview_target, preview_result)

    debug_line()
    info(Code.INFO_COMPLETED)