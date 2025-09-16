# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Matchering 2.0 is a Python library and containerized web application for audio matching and mastering. It takes two audio files (TARGET and REFERENCE) and masters the target to match the RMS, frequency response, peak amplitude, and stereo width of the reference track.

## Core Architecture

The codebase follows a modular pipeline architecture:

### Main Processing Pipeline (`matchering/core.py`)
- **Entry Point**: `process()` function handles the complete mastering workflow
- **Flow**: Load → Validate → Process → Save → (Optional) Preview
- **Stats Caching**: Saves reference analysis to `.stats.pkl` files for performance

### Processing Stages (`matchering/stages.py`)
The mastering algorithm consists of three main stages executed in sequence:
1. **Level Matching** (`__match_levels`): Analyzes and matches RMS levels between target and reference
2. **Frequency Matching** (`__match_frequencies`): Creates and applies FIR filters to match frequency response  
3. **Level Correction** (`__correct_levels`): Iteratively corrects RMS levels after frequency processing
4. **Finalization** (`__finalize`): Applies limiting and normalization based on output requirements

### Key Components
- **Loader** (`loader.py`): Handles audio file loading with MP3 support via FFmpeg
- **Checker** (`checker.py`): Validates audio files and processing parameters
- **DSP** (`dsp.py`): Core digital signal processing utilities
- **Limiter** (`limiter/`): Custom brickwall limiter implementation (Hyrax algorithm)
- **Stage Helpers** (`stage_helpers/`): Specialized functions for level/frequency analysis
- **Results** (`results.py`): Output format configuration (PCM16, PCM24, custom formats)
- **Logging** (`log/`): Comprehensive logging system with error codes and explanations

### Mid-Side Processing
The algorithm processes audio in Mid-Side format:
- **Mid**: Sum of left and right channels (center information)  
- **Side**: Difference of left and right channels (stereo width information)
- Both channels are processed independently then recombined

## Development Commands

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Testing Library
```bash
# Basic test with example files
python examples/basic.py

# Advanced results test
python examples/advanced_results.py

# Test with custom configuration  
python examples/edited_config.py
```

### Building Package
```bash
# Build distribution packages
python setup.py sdist bdist_wheel

# Upload to PyPI (maintainers only)
python -m twine upload dist/*
```

### Docker Development
```bash
# Build Docker image locally
docker build -t matchering .

# Run containerized version
docker run -p 9999:9999 matchering
```

## Configuration

### Default Configuration (`defaults.py`)
Key parameters for audio processing:
- `internal_sample_rate`: 44100 Hz (fixed processing rate)
- `fft_size`: 32768 (for frequency analysis)
- `max_piece_size`: 5292000 samples (~2 minutes at 44.1kHz)
- `rms_correction_steps`: 3 (iterative level correction)
- `threshold`: -0.01 dB (limiting threshold)

### Custom Configuration
```python
import matchering as mg

config = mg.Config()
config.threshold = -1.0  # More conservative limiting
config.rms_correction_steps = 5  # More precise level matching

mg.process(target="song.wav", reference="ref.wav", 
          results=[mg.pcm24("output.wav")], config=config)
```

## Output Formats

### Built-in Shortcuts
- `mg.pcm16()`: 16-bit WAV with limiter
- `mg.pcm24()`: 24-bit WAV with limiter

### Custom Results
```python
mg.Result("output.flac", subtype="PCM_24", use_limiter=False, normalize=True)
```

### Processing Variants
- **With Limiter**: Standard mastered output (default)
- **No Limiter + Normalized**: Peaks at -0.01 dB, no limiting artifacts
- **No Limiter + Non-Normalized**: Raw output for further processing

## File Structure Patterns

- `matchering/`: Main package directory
  - `stage_helpers/`: Specialized processing functions
  - `limiter/`: Custom limiting algorithm  
  - `log/`: Logging system with error codes
- `examples/`: Usage examples and test scripts
- `input/`: Default directory for source audio files
- `output/`: Default directory for processed results

## Dependencies

Core audio processing stack:
- **numpy**: Numerical computations
- **scipy**: Scientific computing and signal processing
- **soundfile**: Audio I/O (requires libsndfile system library)
- **resampy**: Sample rate conversion
- **statsmodels**: Statistical analysis for level matching

## Performance Notes

- Processes stereo audio at 44.1kHz internally regardless of input format
- Memory usage scales with audio length; large files processed in chunks
- Reference analysis is cached as `.stats.pkl` files to avoid recomputation
- FFT operations are optimized for the fixed 32768 sample window size
