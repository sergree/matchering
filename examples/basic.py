import matchering as mg

# Sending all log messages to the default print function
# Just delete the following line to work silently
mg.log(print)

mg.process(
    # The track you want to master
    target="my_song.wav",
    # Some "wet" reference track
    reference="some_popular_song.wav",
    # Where and how to save your results
    results=[
        mg.pcm16("my_song_master_16bit.wav"),
        mg.pcm24("my_song_master_24bit.wav"),
    ],
)
