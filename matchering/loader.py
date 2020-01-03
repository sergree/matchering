import numpy as np


def load(fname: str) -> np.ndarray:
    # Try to load with SoundFile

    # On exception try to convert with ffmpeg subprocess
    # https://stackoverflow.com/questions/9458480/read-mp3-in-python-3
    # ffmpeg -i song.mp3 song.wav
    pass
