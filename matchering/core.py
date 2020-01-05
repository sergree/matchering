from .log import Code, warning, info, debug, ModuleError
from . import MainConfig
from .loader import load
from .stages import main
from .saver import save
from .preview_maker import make_preview
from .utils import get_temp_folder
from .checker import check, check_equality
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

    # Process
    result, result_no_limiter, result_no_limiter_normalized = main(
        target,
        reference,
        config,
        need_default=any(rr.use_limiter for rr in results),
        need_no_limiter=any(not rr.use_limiter and not rr.normalize for rr in results),
        need_no_limiter_normalized=any(not rr.use_limiter and rr.normalize for rr in results),
    )

    info(Code.INFO_EXPORTING)

    # Save
    for required_result in results:
        if required_result.use_limiter:
            correct_result = result
        else:
            if required_result.normalize:
                correct_result = result_no_limiter_normalized
            else:
                correct_result = result_no_limiter
        save(required_result.file, correct_result, config.internal_sample_rate, required_result.subtype)

    # info(Code.INFO_MAKING_PREVIEWS)
    # Making previews (if needed)
    # DO STUFF HERE ---> ...
    # --- Make previews from first non-null value of (result, result_no_limiter, result_no_limiter_normalized)

    info(Code.INFO_COMPLETED)
