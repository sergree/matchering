from matchering import DSPModule, Result

module = DSPModule()
module.process(
    target='my_mix.wav',
    reference='reference.wav',
    results=[
        Result(
            'result_24bit.wav',
            'PCM_24'
        ),
        Result(
            'result_32bit_no_limiter.wav',
            'FLOAT',
            use_limiter=False,
            normalize=False
        ),
    ]
)
