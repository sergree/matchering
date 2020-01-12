[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/sergree)

# Matchering 2.0

### Matching + Mastering = ❤️

**[Matchering 2.0]** is a novel ~~**Containerized Web Application**~~ *(coming soon!)* and **[Python Library][PyPI]** for audio matching and [mastering].

It follows a *simple idea* - you take TWO audio files and feed them into **Matchering**: 
- **TARGET** (the track you want to master, you want it to sound like the reference)
- **REFERENCE** (another track, like some kind of "wet" popular song, you want your target to sound like it)

Our algorithm matches both of these tracks and provides you the mastered **TARGET** track with the same [RMS], [FR], [peak amplitude] and [stereo width] as the **REFERENCE** track has.

So **Matchering 2.0** will make your song sound the way you want! It opens up a wide range of opportunities:
- You can make your music instantly sound like your favorite artist's music
- You can make all the tracks on your new album sound the same very quickly
- You can find new aspects of your sound in experiments
- You can do everything as you want! Because of **[Your References, Your Rules.™](https://macprovideo.com/article/audio-software/sound-tools-instant-online-mastering-with-reference-matching-now-in-open-beta)** *(just a little nostalgic note)* 🤭

> Differences from the previous major version:
> - Completely rewritten in [Python 3], based on open source tech stack (no more [MATLAB])
> - Our own open source [brickwall limiter] was implemented for it
> - Processing speed and accuracy have been increased
> - Now it is [the library][PyPI] that can be connected to **everything** in **the Python world**

# Installation and Usage

If you are a music producer or an audio engineer, choose the ~~**[Docker Image](#docker-image---the-easiest-way)**~~ *(coming soon!)*. 

If you are a developer, choose the **[Python Library](#python-library---for-developers)**.

# ~~Docker Image - The Easiest Way~~

### Coming soon! Stay tuned.

# Python Library - For Developers

## Installation

**[Python 3.6.0 or higher][Python 3] is required**

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
    target='my_song.wav',

    # Some "wet" reference track
    reference='some_popular_song.wav',

    # Where and how to save your results
    results=[
        mg.pcm16('my_song_master_16bit.wav'),
        mg.pcm24('my_song_master_24bit.wav'),
    ]
)

```

You can find more examples in the **[examples directory]**.

### Or you can use premade **Matchering 2.0 Command Line Application**: **[matchering-cli]**.

## A Coffee

If our package saved your time or money, you may:

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/sergree)

**Thank you!**

## Press About Us

- **MusicRadar: [#1](https://www.musicradar.com/news/tech/the-matchering-online-mastering-service-promises-to-make-your-tracks-sound-like-others-646454)**

- **Ask.Audio: [#1](https://ask.audio/articles/this-new-online-service-uses-reference-track-to-instantly-master-your-mixes) [#2](https://ask.audio/articles/sound-tools-instant-online-mastering-with-reference-matching-now-in-open-beta) [#3](https://ask.audio/articles/soundtools-online-sound-mastering-algorithm-source-code-available-free-on-github)**

- **Rekkerd: [#1](https://rekkerd.org/sound-tools-intros-matchering-online-mastering-service-with-matching/) [#2](https://rekkerd.org/sound-tools-launches-matchering-public-beta/) [#3](https://rekkerd.org/sound-tools-matchering-mastering-service-folds-now-open-source/)**

- **macProVideo.com: [#1](https://macprovideo.com/article/audio-software/this-new-online-service-uses-reference-track-to-instantly-master-your-mixes) [#2](https://macprovideo.com/article/audio-software/sound-tools-instant-online-mastering-with-reference-matching-now-in-open-beta) [#3](https://macprovideo.com/article/audio-software/soundtools-online-sound-mastering-algorithm-source-code-available-free-on-github)**

- **gearnews.de: [#1](https://www.gearnews.de/online-mastering-und-matching-der-naechste-versuch-mit-extra-sound-tools/) [#2](https://www.gearnews.de/online-mastering-sound-tools-geht-in-public-beta-phase/) [#3](https://www.gearnews.de/mastering-algorithmus-matchering-von-sound-tools-jetzt-auf-github/)**

- **Logic Loc: [#1](http://www.logiclocmusic.com/2017/01/05/the-matchering-online-mastering-service-promises-to-make-your-tracks-sound-like-others/)**

**Thanks, guys!**

## Links

- [Our Limiter Quality Test](https://github.com/sergree/matchering/blob/master/LIMITER_TEST.md)
- [Log Codes Overview](https://github.com/sergree/matchering/blob/master/LOG_CODES.md)
- [Our Thoughts](https://github.com/sergree/matchering/blob/master/THOUGHTS.md)

[Matchering]: https://github.com/sergree/matchering
[Matchering 2.0]: https://github.com/sergree/matchering
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
