from matchering import DSPModule, Result

module = DSPModule()
module.process(
    target='my_mix.wav',
    reference='reference.flac',
    results=[
        Result.wav_24bit('result_24bit.wav'),
        Result.wav_16bit('result_16bit.wav'),
        Result.wav_32bit_no_limiter('result_32bit_no_limiter.wav'),

        Result(
            'custom_result_16bit.flac',
            'PCM_16'
        ),
        Result(
            'custom_result_32bit_no_limiter_non-normalized.aiff',
            'FLOAT',
            use_limiter=False,
            normalize=False
        ),
    ]
)
