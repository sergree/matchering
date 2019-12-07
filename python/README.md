# Matchering (python ver.)

A python version of matchering algorithm according to original matlab source code using Numpy package.

The limiter part is removed and make up to users personal choice.

## Quick Start

If this is your first time using python, we highly recommend using [Anaconda](https://docs.anaconda.com/anaconda/user-guide/getting-started/)
to get started, and build your python environment.

1. Open your terminal and activate a python environment.
2. `sudo apt install libsndfile-dev`
3. `cd Matchering/python`
4. Install requirements.
```
pip install requirements.txt
```
5. Master your mix.
```
python matchering.py your_mix.wav reference.wav
```

## Usage
```
usage: Matchering DSP Module 0.86 by Wokashi RG (ex. SOUND.TOOLS)
https://github.com/SOUNDTOOL
All non-44100 audio will be resampled to 44100 for now 
Only stereo and mono supported for now

positional arguments:
  target                inpurt target file, must be in .wav format
  reference             inpurt reference file, must be in .wav format

optional arguments:
  -h, --help            show this help message and exit
  --output_dir OUTPUT_DIR
                        directory to put the output file. default to working directory
  --time_area TIME_AREA
                        Max length of analyzed part (in seconds)
  --fft_size FFT_SIZE
  --lin_log_oversample LIN_LOG_OVERSAMPLE
                        Linear to log10 oversampling coefficient: x1, x2, x3 x4, etc.
  --peak_compensation_steps PEAK_COMPENSATION_STEPS

```
