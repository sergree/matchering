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
- You can do everything as you want! Because of **[Your References, Your Rules.™][mpv1]** *(just a little nostalgic note)* 🤭

> Differences from the previous major version:
> - Completely rewritten in [Python 3], based on open source tech stack (no more [MATLAB])
> - Our own open source [brickwall limiter] was implemented for it
> - Processing speed and accuracy have been increased
> - Now it's [a library][PyPI] that can be connected to **everything** in **the Python world**

# Installation and Usage

If you are a music producer or an audio engineer, choose the ~~**[Docker Image](#docker-image---the-easiest-way)**~~ *(coming soon!)*. 

If you are a developer, choose the **[Python Library](#python-library---for-developers)**.

# ~~Docker Image - The Easiest Way~~

### Coming soon! Stay tuned.

# Python Library - For Developers

## Installation

**Python 3.6.0 or higher is required**

### libsndfile

**Matchering 2.0** depends on the **[SoundFile library]**, which depends on the system library **[libsndfile]**. On Windows and macOS, it installs automatically. On Linux, you need to install **[libsndfile]** using your distribution's package manager, for example:

```sudo apt update && sudo apt -y install libsndfile1```

### *FFmpeg (Optional)*

If you would like to enable *MP3 loading support*, you need to install the **[FFmpeg]** library. For example use this command on Ubuntu Linux:

```sudo apt -y install ffmpeg```

Or follow these instructions: [Windows][FFmpeg-win], [macOS][FFmpeg-mac]

## Quick Example

## Buy Me A Coffee

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/sergree)

# Our Thoughts?

## Links?

### Codes?

### Our Mastering Limiter Quality Test?

## Press About Us

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
[SoundFile library]: https://github.com/bastibe/SoundFile#installation
[libsndfile]: http://www.mega-nerd.com/libsndfile/
[FFmpeg]: https://www.ffmpeg.org/download.html
[FFmpeg-win]: https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows
[FFmpeg-mac]: https://superuser.com/questions/624561/install-ffmpeg-on-os-x

[mpv1]: https://macprovideo.com/article/audio-software/sound-tools-instant-online-mastering-with-reference-matching-now-in-open-beta
