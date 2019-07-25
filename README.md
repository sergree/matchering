# Matchering by Wokashi RG (ex. SOUND.TOOLS)

We're glad to share source code of closed [Matchering] project by **Wokashi RG (ex. SOUND.TOOLS)** to you.

[Matchering] was a novel online [mastering] service with a *simple idea* - you should upload 2 tracks: 
- **TARGET** (the track which you want to master, yours or not yours, you want it sounds like the reference);
- **REFERENCE** (another track, yours or not yours, you want your target sounds like it);

The result of **Matchering** is the **TARGET** track with the same [RMS], [FR], [peak amplitude], [stereo width] as the **REFERENCE** track has.

This information was at our site:
> We developed the unique automatic flexible processing algorithm, which offers a novel online mastering experience, where you show us: how your track should sound by sending the **REFERENCE**.
>
> Matchering will make your track sounds like you want:
> - 1st step - To match characteristics of your **TARGET** and the **REFERENCE** tracks;
> - 2nd step - To master your **TARGET** track with the **REFERENCE** track's mastering settings.
>
> It opens a wide range of opportunities:
> - You can make your track instantly sounds like your favorite artist's;
> - You can make all the tracks of your new album to sound the same very quickly;
> - You can find new aspects of your sound in experiments;
> - You can do everything as you want, because of: **Your References, Your Rules**.

And now you can make your own **Matchering** at home. Let's begin!

# Installation Prerequisites

## OS

Microsoft Windows 64-bit (for setup with [sound limiting]), or any OS which [MATLAB] supports.

## Basic Software

- [MATLAB] (tested on 2016a and newer);
- [Signal Processing Toolbox] for MATLAB;
- [Curve Fitting Toolbox] for MATLAB.

With this setup you will get results without [sound limiting]. If you have some **brickwall limiter plug-in** in your [DAW], you may use it with these results.

*(Optional)* If you want automated [sound limiting], get this:
- *(Optional)* `mrswatson64.exe` from [MrsWatson];
- *(Optional)* Some brickwall limiter VST2x64 DLL - original **Matchering** used `Elephant.dll` from [Voxengo Elephant].

### Why didn't we make limiting in MATLAB?

Making own quality brickwall limiting algorithm is very huge subject. And we had no time for it.

# Usage

1. Get our [scripts];
2. Place them in some place like `C:\matchering`;
3. Edit `runscript.m`:
   - `pathWorkspace` is the path to your tracks, for e.g. `'C:\matchering\workspace\'`;
   - `fileTarget` is your **TARGET** track, for e.g. `'target.wav'` ([supported formats]);
   - `fileReference` is your **REFERENCE** track, for e.g. `'reference.wav'` ([supported formats]);
   - `pathTemp` is the path for internal temp files, for e.g. `'C:\matchering\temp\'`;
   - `pathBin` is the path with `mrswatson64.exe` and some brickwall limiter VST2x64 DLL, for e.g. `'C:\matchering\bin\'`, keep it blank if you setup without [sound limiting], like `''`;
   - *(Optional)* `fileBrickwallLimiter` is the name of brickwall limiter VST2x64 DLL, ignored if `pathBin` is blank;
   - *Note: leave `\` in the end of all path variables, also these folders must exist and MATLAB should have proper folder permissions*;
   - Other DSP variables keep as is;
4. Run `run.bat` or `runconsole.bat`;
5. After processing your result file(s) will be in `pathWorkspace` folder.

If you have [sound limiting] setup, you will get two WAV files: limited 24-bit and 16-bit.

Otherwise you will get only one WAV file: not limited 32-bit floating point for future limiting in DAW.

## Error Codes

Our `matchering.m` module returns an integer that indicates a process, a success or a specific error.

| Code | Meaning                                                               |
|------|-----------------------------------------------------------------------|
| 2    | In queue for processing                                               |
| 3    | Loading and analysing                                                 |
| 4    | Matching levels                                                       |
| 5    | Matching frequencies                                                  |
| 6    | Correcting levels                                                     |
| 7    | Final processing and saving                                           |
| 8    | Export in various audio formats                                       |
| 9    | Task complete                                                         |
| 30   | Audio stream error in both files!                                     |
| 31   | Audio stream error in target file!                                    |
| 32   | Audio stream error in reference file!                                 |
| 33   | Track length exceeded in both files!                                  |
| 34   | Track length exceeded in target file!                                 |
| 35   | Track length exceeded in reference file!                              |
| 36   | Number of channels exceeded in both files!                            |
| 37   | Number of channels exceeded in target file!                           |
| 38   | Number of channels exceeded in reference file!                        |
| 39   | Track length is too small in both files!                              |
| 40   | Track length is too small in target file!                             |
| 41   | Track length is too small in reference file!                          |
| 42   | Track length exceeded in reference file and too small in target file! |
| 43   | Track length exceeded in target file and too small in reference file! |

## Donate

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)][donate]

If our script saved your time or money, you may [support us][donate].

**Thank you!**

# Our Thoughts

### Why can't such online service be succeed nowadays?

- Very little potential audience. Let's explain: **all audio people** (100%) minus **audio novices who don't know about mastering** (40%) minus **pro audio guys who can make mastering by themselves** (20%) minus **guys who don't believe in automated mastering** (30%), the remaining 10% is **the group of people who open to novel things**, but this group is too small;
- Mastering engineers think such services will replace them => no support from **pro audio guys** like [KVR community].

### It's just numbers!

We have bad news for you, if you think that good audio [mastering] can be done only with very expensive analog studio equipment. It's **a myth** that brings money to *a certain group of people*. The times of [vinyl] and [cassettes] are passed. All [audio] is digital now: it's all about [bytes] - [integers] and [floats]. All modern [audio] can be processed via [DSP techniques][DSP]. And [everything][DSPApps] can be done by [it][DSP]. Just use **good audio software and plug-ins** or learn [DSP] with *some suitable programming languages* to make **your own stuff**. 😉

### Why did [Matchering] close?

- Too much marketing investments needed to convince people that **Matchering** works. And it works with more precision than handmade [mastering] *in most cases*;
- Too much investments in hardware needed before going **paid**:
  - Paid online service needs to keep all done masterings at user's personal area => **too many HDDs needed**;
  - Also it needs to be quickly accessible anywhere in the world => **too many VPSes from different suppliers needed**;
  - Also it needs **highly qualified support service** for clients => **salary payments needed**;
  - Etc.

*This amount of money was unaffordable for three ordinary students from Eastern Europe*.

### Why was it supposed to be successful? (As we thought)

Do you remember [Prisma]? **Matchering** is like **audio-Prisma** for sound options like [RMS], [FR], [peak amplitude] and [stereo width].

### Why are online [mastering] services without references useless?

Online [mastering] services without possibility to upload a **REFERENCE** is a [black box]. How can it know how **your track** should sound? There are so much different *genres* and *styles*, and all of them need their individual approach to processing. And there are so much different *soundings* in them. And without a **REFERENCE** it's imposible to get good results. *It's pure mathematics.*

### Potential rewrite on open source platform

We believe that some *some enthusiasts* can rewrite **Matchering** on [Python]'s [NumPy].

## Press About Us

[MusicRadar](https://www.musicradar.com/news/tech/the-matchering-online-mastering-service-promises-to-make-your-tracks-sound-like-others-646454)

[Ask.Audio #1](https://ask.audio/articles/this-new-online-service-uses-reference-track-to-instantly-master-your-mixes)

[Ask.Audio #2](https://ask.audio/articles/sound-tools-instant-online-mastering-with-reference-matching-now-in-open-beta)

[Ask.Audio #3](https://ask.audio/articles/soundtools-online-sound-mastering-algorithm-source-code-available-free-on-github)

[Rekkerd #1](https://rekkerd.org/sound-tools-intros-matchering-online-mastering-service-with-matching/)

[Rekkerd #2](https://rekkerd.org/sound-tools-launches-matchering-public-beta/)

[Rekkerd #3](https://rekkerd.org/sound-tools-matchering-mastering-service-folds-now-open-source/)

[mixingroom.de #1](http://mixingroom.de/matchering-automatisiertes-online-mastering-mit-sound-tools/)

[mixingroom.de #2](http://mixingroom.de/sound-tools-gibt-oeffentliche-beta-phase-von-online-mastering-service-matchering-bekannt/)

[gearnews.de #1](https://www.gearnews.de/online-mastering-sound-tools-geht-in-public-beta-phase/)

[gearnews.de #2](https://www.gearnews.de/mastering-algorithmus-matchering-von-sound-tools-jetzt-auf-github/)

[Logic Loc](http://www.logiclocmusic.com/2017/01/05/the-matchering-online-mastering-service-promises-to-make-your-tracks-sound-like-others/)

**Thanks, guys!**

[Matchering]: http://sound.tools
[sound limiting]: https://en.wikipedia.org/wiki/Limiter
[MATLAB]: https://www.mathworks.com/campaigns/products/trials.html?prodcode=ML
[Signal Processing Toolbox]: https://www.mathworks.com/campaigns/products/trials.html?prodcode=SG
[Curve Fitting Toolbox]: https://www.mathworks.com/campaigns/products/trials.html?prodcode=CF
[DAW]: https://en.wikipedia.org/wiki/Digital_audio_workstation
[MrsWatson]: https://github.com/teragonaudio/MrsWatson
[Voxengo Elephant]: https://www.voxengo.com/product/elephant/
[scripts]: https://github.com/SOUNDTOOLS/Matchering/archive/master.zip
[supported formats]: https://www.mathworks.com/help/matlab/import_export/supported-file-formats.html
[donate]: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=HCZY8AJ9HNRGN&lc=US&item_name=Wokashi%2eRG%3a%20Matchering&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted
[NumPy]: http://www.numpy.org/
[Python]: https://www.python.org/
[Prisma]: https://prisma-ai.com/
[KVR community]: https://www.kvraudio.com/
[mastering]: https://en.wikipedia.org/wiki/Audio_mastering
[RMS]: https://en.wikipedia.org/wiki/Root_mean_square
[FR]: https://en.wikipedia.org/wiki/Frequency_response
[peak amplitude]: https://en.wikipedia.org/wiki/Amplitude
[stereo width]: https://en.wikipedia.org/wiki/Stereo_imaging
[black box]: https://en.wikipedia.org/wiki/Black_box
[vinyl]: https://en.wikipedia.org/wiki/Vinyl
[cassettes]: https://en.wikipedia.org/wiki/Compact_Cassette
[audio]: https://en.wikipedia.org/wiki/Digital_audio
[bytes]: https://en.wikipedia.org/wiki/Byte
[integers]: https://en.wikipedia.org/wiki/Integer
[floats]: https://en.wikipedia.org/wiki/Single-precision_floating-point_format
[DSP]: https://en.wikipedia.org/wiki/Digital_signal_processing
[DSPApps]: https://en.wikipedia.org/wiki/Digital_signal_processing#Applications
[CPP]: https://en.wikipedia.org/wiki/C%2B%2B
