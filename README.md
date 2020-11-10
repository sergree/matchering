[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/sergree)

![Matchering 2.0](https://raw.githubusercontent.com/sergree/matchering/master/images/logo.png)

[![License](https://img.shields.io/pypi/l/matchering.svg)](https://pypi.python.org/pypi/matchering/)
[![PyPI Version](https://badge.fury.io/py/matchering.svg)](https://badge.fury.io/py/matchering)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/matchering.svg)](https://pypi.python.org/pypi/matchering/)
[![Mentioned in Awesome Python](https://awesome.re/mentioned-badge.svg)](https://github.com/vinta/awesome-python)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Matching + Mastering = ❤️

**[Matchering 2.0]** is a novel **[Containerized Web Application][Docker Image]** and **[Python Library][PyPI]** for audio matching and [mastering].

It follows a *simple idea* - you take TWO audio files and feed them into **Matchering**: 
- **TARGET** (the track you want to master, you want it to sound like the reference)
- **REFERENCE** (another track, like some kind of "wet" popular song, you want your target to sound like it)

Our algorithm matches both of these tracks and provides you the mastered **TARGET** track with the same [RMS], [FR], [peak amplitude] and [stereo width] as the **REFERENCE** track has.

Watch **[the video][Video]**:

[![Matchering 2.0 Promo Video](http://img.youtube.com/vi/8Su5STDYfcA/0.jpg)][Video]

So **Matchering 2.0** will make your song sound the way you want! It opens up a wide range of opportunities:
- You can make your music instantly sound like your favorite artist's music
- You can make all the tracks on your new album sound the same very quickly
- You can find new aspects of your sound in experiments
- You can do everything as you want! Because of **[Your References, Your Rules.™](https://macprovideo.com/article/audio-software/sound-tools-instant-online-mastering-with-reference-matching-now-in-open-beta)** *(just a little nostalgic note)* 🤭

![Matchering WEB GIF Animation](https://raw.githubusercontent.com/sergree/matchering/master/images/animation.gif "Matchering WEB")

> Differences from the previous major version:
> - Completely rewritten in [Python 3], based on open source tech stack (no more [MATLAB])
> - Our own open source [brickwall limiter] was implemented for it
> - Processing speed and accuracy have been increased
> - Now it is [the library][PyPI] that can be connected to **everything** in **the Python world**

# Installation and Usage

If you are a music producer or an audio engineer, choose the **[Docker Image]**. 

If you are a developer, choose the **[Python Library](#python-library---for-developers)**.

# Docker Image - The Easiest Way

**Matchering 2.0** works on all major platforms using **Docker**.

## Choose yours

### [Windows](https://github.com/sergree/matchering/blob/master/DOCKER_WINDOWS.md)
### [macOS](https://github.com/sergree/matchering/blob/master/DOCKER_MACOS.md)
### [Linux](https://github.com/sergree/matchering/blob/master/DOCKER_LINUX.md)

## Updating

If you need to update the version of the installed **Docker Image**, follow **[these instructions](https://github.com/sergree/matchering/blob/master/DOCKER_UPDATING.md)**.

# Python Library - For Developers

## Installation

**4 GB RAM machine with [Python 3.6.0 or higher][Python 3] is required**

### libsndfile

**Matchering 2.0** depends on the **[SoundFile]** library, which depends on the system library **[libsndfile]**. On Windows and macOS, it installs automatically. On Linux, you need to install **[libsndfile]** using your distribution's package manager, for example:

```sudo apt update && sudo apt -y install libsndfile1```

### python3-pip

On some Linux distributions, **python3-pip** is not installed by default. For example use this command on Ubuntu Linux to fix this:

```sudo apt -y install python3-pip```

### Matchering Python Package

Finally, install our `matchering` package:

```
# Linux / macOS
python3 -m pip install -U matchering

# Windows
python -m pip install -U matchering
```

### *(Optional) FFmpeg*

If you would like to enable *MP3 loading support*, you need to install the **[FFmpeg][FFmpeg]** library. For example use this command on Ubuntu Linux:

```sudo apt -y install ffmpeg```

Or follow these instructions: [Windows][FFmpeg-win], [macOS][FFmpeg-mac].

## Quick Example

```python
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

```

You can find more examples in the **[examples directory]**.

### Or you can use premade **Matchering 2.0 Command Line Application**: **[matchering-cli]**.

## A Coffee

If our package saved your time or money, you may:

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/sergree)

**Thank you!**

## Links

- [Press About Us](https://github.com/sergree/matchering/blob/master/PRESS.md)
- [Supporters](https://github.com/sergree/matchering/blob/master/SUPPORTERS.md)
- [Our Limiter Quality Test](https://github.com/sergree/matchering/blob/master/LIMITER_TEST.md)
- [Log Codes Overview](https://github.com/sergree/matchering/blob/master/LOG_CODES.md)
- [Our Thoughts](https://github.com/sergree/matchering/blob/master/THOUGHTS.md)

[Matchering]: https://github.com/sergree/matchering
[Matchering 2.0]: https://github.com/sergree/matchering
[Docker Image]: #docker-image---the-easiest-way
[mastering]: https://en.wikipedia.org/wiki/Audio_mastering
[RMS]: https://en.wikipedia.org/wiki/Root_mean_square
[FR]: https://en.wikipedia.org/wiki/Frequency_response
[peak amplitude]: https://en.wikipedia.org/wiki/Amplitude
[stereo width]: https://en.wikipedia.org/wiki/Stereo_imaging
[MATLAB]: https://www.mathworks.com/products/matlab.html
[Python 3]: https://www.python.org/
[brickwall limiter]: https://en.wikipedia.org/wiki/Dynamic_range_compression#Limiting
[PyPI]: https://pypi.org/project/matchering
[SoundFile]: https://github.com/bastibe/SoundFile#installation
[libsndfile]: http://www.mega-nerd.com/libsndfile/
[FFmpeg]: https://www.ffmpeg.org/download.html
[FFmpeg-win]: https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows
[FFmpeg-mac]: https://superuser.com/questions/624561/install-ffmpeg-on-os-x
[matchering-cli]: https://github.com/sergree/matchering-cli
[examples directory]: https://github.com/sergree/matchering/tree/master/examples
[Video]: http://www.youtube.com/watch?v=8Su5STDYfcA "Matchering 2.0 - Open Source Audio Matching and Mastering"
