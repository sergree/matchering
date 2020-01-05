from .log import Code, warning, info, debug, ModuleError
from . import MainConfig
from .loader import load
from .utils import get_temp_folder
from .checks import check, check_equality
from .dsp import channel_count, length_nda


def process(
        target: str,
        reference: str,
        results: list,
        config: MainConfig = MainConfig(),
):
    info(Code.INFO_LOADING)

    # Get a temporary folder for converting mp3's
    temp_folder = config.temp_folder if config.temp_folder else get_temp_folder(results)

    # Load the target
    target, target_sample_rate = load(target, 'target', temp_folder)
    # Analyze the target
    target, target_sample_rate = check(target, target_sample_rate, config, 'target')

    # Load the reference
    reference, reference_sample_rate = load(reference, 'reference', temp_folder)
    # Analyze the reference
    reference, reference_sample_rate = check(reference, reference_sample_rate, config, 'reference')

    # Analyze the target and the reference together
    check_equality(target, reference)

    # Validation of the most important conditions
    if not (target_sample_rate == reference_sample_rate == config.internal_sample_rate)\
            or not (channel_count(target) == channel_count(reference) == 2)\
            or not (length_nda(target) > config.fft_size and length_nda(reference) > config.fft_size):
        return ModuleError(Code.ERROR_VALIDATION)

    debug(f'The maximum size of the analyzed piece: {config.max_piece_size} samples '
          f'or {config.max_piece_size / config.internal_sample_rate:.2f} seconds')

    # Process
    info(Code.INFO_MATCHING_LEVELS)
    result = target

    # Save
