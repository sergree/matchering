from .log import Code, warning, info, debug, ModuleError
from . import MainConfig
from .loader import load
from .utils import get_temp_folder


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

    # Check the target

    # Load the reference
    #debug(f'Loading REFERENCE file: {reference}...')
    #reference, reference_sample_rate = load(reference, 'reference')
    #debug('REFERENCE file is loaded')

    # Check the reference

    # Process
    result = target

    # Save
    pass
