import matchering as mg

mg.log(print)

mg.process(
    target='my_song.wav',
    reference='some_popular_song.wav',
    results=[
        mg.pcm16('my_song_master_16bit.wav'),
        mg.pcm24('my_song_master_24bit.wav'),
    ]
)
