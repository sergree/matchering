import matchering as mg

# Let's completely disable any text output here
# mg.log(print)

mg.process(
    target="my_song.wav",
    reference="some_popular_song.wav",
    results=[
        mg.pcm16("my_song_master_16bit.wav"),
        mg.pcm24("my_song_master_24bit.wav"),
    ],
    # Create a custom Config instance to edit matchering configuration
    # Think twice before you change something here
    config=mg.Config(
        # Increase the maximum length to 30 minutes from the default value of 15
        max_length=30 * 60,
        # Increase the internal and resulting sample rate to 96 kHz from the default value of 44.1 kHz
        internal_sample_rate=96000,
        # Change the threshold value (float, not dB) from the default value of 0.9981 (-0.01 dB)
        threshold=0.7079,  # -3 dB
        # Change the temp folder to work with ffmpeg
        temp_folder="/tmp",
        # Lower the preview length to 15 seconds from the default value of 30
        preview_size=15,
        # Allow matchering to accept the same files (useless in fact)
        allow_equality=True
        # Etc...
        # The remaining parameters will be filled with default values
        # Examine defaults.py to find other parameters
    ),
)
