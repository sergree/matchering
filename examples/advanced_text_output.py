import matchering as mg

from datetime import datetime


# Let's define a basic text output function that will also output the current datetime
def my_print(text):
    print(f"{datetime.now()}: {text}")


# The information output will be marked with a prefix
def info(text):
    my_print(f"INFO: {text}")


# The warning output will be highlighted with exclamation marks on both sides
def warning(text):
    my_print("!" * 20)
    my_print(f"! WARNING: {text}")
    my_print("!" * 20)


# Set new handlers
mg.log(warning_handler=warning, info_handler=info, debug_handler=my_print)

mg.process(
    target="my_song.wav",
    reference="some_popular_song.wav",
    results=[
        mg.pcm16("my_song_master_16bit.wav"),
        mg.pcm24("my_song_master_24bit.wav"),
    ],
)

# These settings will result in the following text output:
# ...
# 2020-01-11 11:03:29.225821: INFO: Loading and analysis
# 2020-01-11 11:03:29.225821: Loading the TARGET file: 'my_song.wav'...
# 2020-01-11 11:03:29.396622: The TARGET file is loaded
# 2020-01-11 11:03:29.396622: TARGET audio length: 22932000 samples (0:08:40)
# 2020-01-11 11:03:30.528787: !!!!!!!!!!!!!!!!!!!!
# 2020-01-11 11:03:30.528787: ! WARNING: The applied limiter is detected in the TARGET file...
# 2020-01-11 11:03:30.528787: !!!!!!!!!!!!!!!!!!!!
# 2020-01-11 11:03:30.528787: Loading the REFERENCE file: 'some_popular_song.wav'...
# ...

# You can bind any function that takes a string as input. It may not necessarily be the print().
# Just bind this to some database via a connector or ORM, or, for example, use a logging module, as done here:
# https://github.com/sergree/matchering-cli
