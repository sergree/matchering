from .codes import Code


def __default(code: Code):
    return en[code]


def __verbose(code: Code):
    return f'{code}: {en[code]}'


def get_explanation_handler(show_codes=False):
    return __verbose if show_codes else __default


en = {
    Code.INFO_UPLOADING: 'Uploading files',
    Code.INFO_WAITING: 'Queued for processing',
    Code.INFO_LOADING: 'Loading and analysis',
    Code.INFO_MATCHING_LEVELS: 'Matching levels',
    Code.INFO_MATCHING_FREQS: 'Matching frequencies',
    Code.INFO_CORRECTING_LEVELS: 'Correcting levels',
    Code.INFO_FINALIZING: 'Final processing and saving',
    Code.INFO_EXPORTING: 'Exporting various audio formats',
    Code.INFO_MAKING_PREVIEWS: 'Making previews',
    Code.INFO_COMPLETED: 'The task is completed',

    Code.INFO_TARGET_IS_MONO: 'The TARGET audio is mono. Converting it to stereo...',
    Code.INFO_REFERENCE_IS_MONO: 'The REFERENCE audio is mono. Converting it to stereo...',
    Code.INFO_REFERENCE_IS_CLIPPING: 'Audio clipping is detected in the REFERENCE file',

    Code.WARNING_TARGET_IS_CLIPPING: 'Audio clipping is detected in the TARGET file. '
                                     'It is highly recommended to use the non-clipping version',
    Code.WARNING_TARGET_LIMITER_IS_APPLIED: 'The applied limiter is detected in the TARGET file. '
                                            'It is highly recommended to use the version without a limiter',
    Code.WARNING_TARGET_IS_RESAMPLED: 'The sample rate was not 44100 Hz in the TARGET file. '
                                      'It is resampled to 44100 Hz',

    Code.ERROR_TARGET_LOADING: 'Audio stream error in the TARGET file',
    Code.ERROR_REFERENCE_LOADING: 'Audio stream error in the REFERENCE file',
    Code.ERROR_TARGET_LENGTH_IS_EXCEEDED: 'Track length is exceeded in the TARGET file',
    Code.ERROR_REFERENCE_LENGTH_LENGTH_IS_EXCEEDED: 'Track length is exceeded in the REFERENCE file',
    Code.ERROR_TARGET_LENGTH_IS_TOO_SMALL: 'The track length is too small in the TARGET file',
    Code.ERROR_REFERENCE_LENGTH_LENGTH_TOO_SMALL: 'The track length is too small in the REFERENCE file',
    Code.ERROR_TARGET_NUM_OF_CHANNELS_IS_EXCEEDED: 'The number of channels exceeded in the TARGET file',
    Code.ERROR_REFERENCE_NUM_OF_CHANNELS_IS_EXCEEDED: 'The number of channels exceeded in the REFERENCE file',
    Code.ERROR_TARGET_EQUALS_REFERENCE: 'The TARGET and REFERENCE files are the same. '
                                        'They must be different so that Matchering makes sense',
}
