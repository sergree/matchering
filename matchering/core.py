from .log import Code, warning, info, debug, ModuleError
from . import MainConfig
from .loader import load


def process(
        target: str,
        reference: str,
        results: list,
        config: MainConfig = MainConfig(),
):
    # Load the target
    target = load(target)

    # Check the target

    # Load the reference
    reference = load(reference)

    # Check the reference
    debug('Text')

    # Process
    warning(Code.WARNING_TARGET_IS_CLIPPING)

    # Save
    info(Code.INFO_TARGET_IS_MONO)

    raise ModuleError(Code.ERROR_TARGET_EQUALS_REFERENCE)
