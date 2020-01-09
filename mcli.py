import matchering as mg

mg.log(print, show_codes=True)

mg.process(
    target='audio/my mix.wav',
    reference='audio/reference.flac',
    results=[
        mg.pcm24('result_24bit.wav'),
        mg.pcm16('result_16bit.wav'),

        mg.Result(
            'custom_result_24bit_no_limiter.flac',
            'PCM_24',
            use_limiter=False
        ),
        mg.Result(
            'custom_result_32bit_no_limiter_non-normalized.aiff',
            'FLOAT',
            use_limiter=False,
            normalize=False
        ),
    ]
)
