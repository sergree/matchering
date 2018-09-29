# Matchering by SOUND.TOOLS

We're glad to share source code of closed [Matchering][soundtools] project by **SOUND.TOOLS** to you.

[Matchering][soundtools] was a novel online mastering service with a *simple idea* - you should upload 2 tracks: 
- **TARGET** (the track which you want to master, yours or not yours, you want it sounds like the reference);
- **REFERENCE** (another track, yours or not yours, you want your target sounds like it);

The result of **Matchering** is the **TARGET** track with the same [RMS](https://en.wikipedia.org/wiki/Root_mean_square), [FR](https://en.wikipedia.org/wiki/Frequency_response), [peak amplitude](https://en.wikipedia.org/wiki/Amplitude), [stereo width](https://en.wikipedia.org/wiki/Stereo_imaging) as the **REFERENCE** track has.

This information was at our site:
> We developed the unique automatic flexible processing algorithm, which offers a novel online mastering experience, where you show us: how your track should sound by sending the **REFERENCE**.
>
> Matchering will make your track sounds like you want:
> 1st step - To match characteristics of your **TARGET** and the **REFERENCE** tracks;
> 2nd step - To master your **TARGET** track with the **REFERENCE** track's mastering settings.
>
> It opens a wide range of opportunities:
> - You can make your track instantly sounds like your favorite artist's;
> - You can make all the tracks of your new album to sound the same very quickly;
> - You can find new aspects of your sound in experiments;
> - You can do everything as you want, because of: **Your References, Your Rules**.

And now you can make your own **Matchering** at home. Let's begin!

# Installation Prerequisites

## OS

Microsoft Windows 64-bit (for setup with [sound limiting][limiter]), or any OS which [MATLAB][matlab] supports.

## Basic Software

- [MATLAB][matlab] (tested on 2016a and newer);
- [Signal Processing Toolbox][sptb] for MATLAB;
- [Curve Fitting Toolbox][cftb] for MATLAB.

With this setup you will get results without [sound limiting][limiter]. If you have some **brickwall limiter plug-in** in your [DAW][daw], you may use it with these results.

*(Optional)* If you want automated [sound limiting][limiter], get this:
- *(Optional)* `mrswatson64.exe` from [MrsWatson][mrswatson];
- *(Optional)* Some brickwall limiter VST2x64 DLL - original **Matchering** used `Elephant.dll` from [Voxengo Elephant][elephant].

### Why didn't we made limiting in MATLAB?

Making own quality brickwall limiting algorithm is very huge subject. And we had no time for it.

# Usage

1. Get our [scripts][scripts];
2. Place them in some place like `C:\matchering`;
3. Edit `runscript.m`:
   - `pathWorkspace` is the path to your tracks, for e.g. `'C:\matchering\workspace\'`;
   - `fileTarget` is your **TARGET** track, for e.g. `'target.wav'` ([supported formats][supformats]);
   - `fileReference` is your **REFERENCE** track, for e.g. `'reference.wav'` ([supported formats][supformats]);
   - `pathTemp` is the path for internal temp files, for e.g. `'C:\matchering\temp\'`;
   - `pathBin` is the path with `mrswatson64.exe` and some brickwall limiter VST2x64 DLL, for e.g. `'C:\matchering\bin\'`, keep it blank if you setup without [sound limiting][limiter], like `''`;
   - *(Optional)* `fileBrickwallLimiter` is the name of brickwall limiter VST2x64 DLL, ignored if `pathBin` is blank;
   - *Note: leave `\` in the end of all path variables, also these folders must exist and MATLAB should have proper folder permissions*;
   - Other DSP variables keep as is;
4. Run `run.bat` or `runconsole.bat`;
5. After processing your result file(s) will be in `pathWorkspace` folder.

If you have [sound limiting][limiter] setup, you will get two WAV files: limited 24-bit and 16-bit.

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

*This page is under construction, come back in few days, please.*

### Potential rewrite on open source platform?

*NumPy? This page is under construction, come back in few days, please.*

## Press About Us

[MusicRadar](https://www.musicradar.com/news/tech/the-matchering-online-mastering-service-promises-to-make-your-tracks-sound-like-others-646454)

[Ask.Audio #1](https://ask.audio/articles/this-new-online-service-uses-reference-track-to-instantly-master-your-mixes)

[Ask.Audio #2](https://ask.audio/articles/sound-tools-instant-online-mastering-with-reference-matching-now-in-open-beta)

[Rekkerd #1](https://rekkerd.org/sound-tools-intros-matchering-online-mastering-service-with-matching/)

[Rekkerd #2](https://rekkerd.org/sound-tools-launches-matchering-public-beta/)

[mixingroom.de #1](http://mixingroom.de/matchering-automatisiertes-online-mastering-mit-sound-tools/)

[mixingroom.de #2](http://mixingroom.de/sound-tools-gibt-oeffentliche-beta-phase-von-online-mastering-service-matchering-bekannt/)

[gearnews.de](https://www.gearnews.de/online-mastering-sound-tools-geht-in-public-beta-phase/)

[Logic Loc](http://www.logiclocmusic.com/2017/01/05/the-matchering-online-mastering-service-promises-to-make-your-tracks-sound-like-others/)

**Thanks, guys!**

[soundtools]: https://sound.tools/
[limiter]: https://en.wikipedia.org/wiki/Limiter
[matlab]: https://www.mathworks.com/campaigns/products/trials.html?prodcode=ML
[sptb]: https://www.mathworks.com/campaigns/products/trials.html?prodcode=SG
[cftb]: https://www.mathworks.com/campaigns/products/trials.html?prodcode=CF
[daw]: https://en.wikipedia.org/wiki/Digital_audio_workstation
[mrswatson]: https://github.com/teragonaudio/MrsWatson
[elephant]: https://www.voxengo.com/product/elephant/
[scripts]: https://github.com/SOUNDTOOLS/Matchering/archive/master.zip
[supformats]: https://www.mathworks.com/help/matlab/import_export/supported-file-formats.html
[donate]: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=HCZY8AJ9HNRGN&lc=US&item_name=SOUND%2eTOOLS%3a%20Matchering&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted
