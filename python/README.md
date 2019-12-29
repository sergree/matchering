# Matchering (Python Version)

A python version of matchering algorithm according to original matlab source code using Numpy package.

## Quick Start

### Ubuntu 18.04 LTS

1. `sudo apt update && sudo apt -y install libsndfile1 python3-pip python3-venv`
2. `git clone https://github.com/sergree/matchering && cd matchering/python`
3. Install requirements.
```
python3 -m venv matchering-env && . matchering-env/bin/activate && python3 -m pip install -r requirements.txt
```
4. Master your mix.
```
python3 matchering.py your_mix.wav reference.wav
```

## Usage
```
usage: Matchering DSP Module
https://github.com/sergree/matchering
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

## FAQ

> _Why can't I use MP3?_

It is a known **[libsndfile issue]**.

[libsndfile issue]: https://github.com/erikd/libsndfile/issues/258
