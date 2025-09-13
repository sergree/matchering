# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Matchering** is an audio matching and mastering Python library that takes two audio files (target and reference) and applies mastering effects to make the target sound like the reference. It matches RMS levels, frequency response, peak amplitude, and stereo width.

The repository contains two main components:
1. **Matchering 2.0** - The core audio processing library (`matchering/` directory)
2. **Matchering Player** - A real-time media player with gradual audio matching (`matchering_player/` directory)

## Architecture

### Core Matchering Library (`matchering/`)
- **`core.py`** - Main processing pipeline entry point (`process()` function)
- **`stages.py`** - Multi-stage processing pipeline (Level → Frequency → Limiting)
- **`dsp.py`** - Core DSP functions (RMS, normalize, amplify, mid-side processing)
- **`limiter/`** - Custom Hyrax brickwall limiter implementation
- **`stage_helpers/`** - Level matching and frequency matching algorithms
- **`loader.py`** - Audio file loading with format support
- **`saver.py`** - Audio file output handling
- **`log/`** - Comprehensive logging system with error codes

### Matchering Player (`matchering_player/`)
- **`core/`** - Player engine, audio management, and configuration
- **`dsp/`** - Real-time DSP processing, smoothing, and level matching
- **`ui/`** - GUI interface components

## Common Development Commands

### Installation and Setup
```bash
# Install package in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt
```

### Testing
```bash
# Run basic DSP tests
python test_dsp_core.py

# Run audio pipeline tests
python test_audio_pipeline.py
```

### Running Examples
```bash
# Basic usage example
python examples/simple.py

# Advanced results configuration
python examples/advanced_results.py
```

### Running GUI Demos
```bash
# Launch modern GUI demo
python modern_gui.py

# Launch basic GUI demo
python gui_demo.py

# Launch simple GUI launcher
python launch_gui.py
```

## Key Technical Details

### Audio Processing Pipeline
1. **Loading** - Supports WAV, FLAC, MP3 (with FFmpeg), and other formats via SoundFile
2. **Level Matching** - RMS analysis and amplitude matching
3. **Frequency Matching** - Spectral analysis and EQ curve application
4. **Limiting** - Custom Hyrax brickwall limiter for final stage
5. **Output** - Multiple format support (16-bit/24-bit PCM)

### Dependencies
- **numpy** (>=1.23.4) - Core numerical processing
- **scipy** (>=1.9.2) - Signal processing algorithms
- **soundfile** (>=0.11.0) - Audio I/O
- **resampy** (>=0.4.2) - Sample rate conversion
- **statsmodels** (>=0.13.2) - Statistical analysis

### Configuration
- Default processing parameters in `matchering/defaults.py`
- Player configuration in `matchering_player/core/config.py`
- Supports custom temp directories and internal sample rates

### File Structure Notes
- Test files are at repository root (`test_*.py`)
- GUI demo files are at repository root (`*gui*.py`)
- Examples in `examples/` directory
- Core library code in `matchering/` package
- Player code in `matchering_player/` package
- Documentation files (`*.md`) contain development plans and technical details

## Branch Information
- **Main branch**: `master`
- **Current branch**: `matchering_player` (development branch for real-time player features)