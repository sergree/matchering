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

# Install test dependencies
pip install pytest soundfile pytest-cov
```

### Testing (Comprehensive Test Suite)
```bash
# Run all tests
pytest tests/

# Run with coverage report
python run_tests.py coverage-html

# Run specific test categories
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m integration   # Integration tests only
pytest tests/ -m "not slow"    # Fast tests only
pytest tests/ -m player        # Player-specific tests
pytest tests/ -m core          # Core library tests

# Using the convenient test runner
python tests/test_runner.py fast
python tests/test_runner.py performance
```

### Running Examples
```bash
# Basic usage example
python examples/basic.py

# Advanced results configuration
python examples/advanced_results.py

# With preview generation
python examples/with_preview.py
```

### Running GUI Demos
```bash
# Launch modern GUI demo (full-featured)
python modern_gui.py

# Launch basic GUI demo
python gui_demo.py

# Launch simple GUI launcher
python launch_gui.py

# Demo the player functionality
python demo_matchering_player.py
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
- **Test suite** in `tests/` directory with pytest configuration
- GUI demo files are at repository root (`*gui*.py`)
- Examples in `examples/` directory
- Core library code in `matchering/` package
- Player code in `matchering_player/` package
- Documentation files (`*.md`) contain development plans and technical details

## Test Suite Structure
```
tests/
├── conftest.py                   # Pytest configuration and fixtures
├── pytest.ini                   # Test settings and markers
├── unit/                         # Unit tests for individual components
│   ├── test_dsp_core.py         # DSP functions and processors
│   ├── test_core_library.py     # Core matchering library
│   ├── test_player_components.py # Player components
│   └── test_advanced_features.py # Advanced features (frequency/stereo/auto)
└── integration/                  # Integration tests across components
    ├── test_audio_pipeline.py   # Complete audio processing pipelines
    └── test_error_handling.py   # Error handling and edge cases
```

## Current Test Coverage
- **Overall Coverage**: 46% (Production ready for player, core library needs work)
- **Matchering Player**: 70-85% coverage (well-tested)
- **Core Library**: 15% coverage (needs significant improvement)

## Branch Information
- **Main branch**: `master`
- **Current branch**: `matchering_player` (development branch for real-time player features)
- **Active Development**: Player functionality with comprehensive test suite