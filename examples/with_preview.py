import matchering as mg

# Let's keep only warning outputs here, muting everything else
mg.log(warning_handler=print)

mg.process(
    target="my_song.wav",
    reference="some_popular_song.wav",
    results=[
        mg.pcm16("my_song_master_16bit.wav"),
        mg.pcm24("my_song_master_24bit.wav"),
    ],
    # These two lines will allow you to create two 30-second FLAC files with the loudest parts of:
    # 'my_song.wav' and 'my_song_master_16bit.wav'
    # Use them to quickly compare the target audio with the resulting audio
    preview_target=mg.pcm16("preview_my_song.flac"),
    preview_result=mg.pcm16("preview_my_song_master.flac"),
)
