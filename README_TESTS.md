# Matchering Test Suite

This directory contains a comprehensive test suite for the Matchering audio processing library and Matchering Player.

## Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Pytest configuration and fixtures
├── test_runner.py             # Convenient test runner script
├── unit/                      # Unit tests for individual components
│   ├── test_dsp_core.py      # Basic DSP functions and processors
│   ├── test_core_library.py  # Core matchering library components
│   ├── test_player_components.py # Player component tests
│   └── test_advanced_features.py # Advanced player features
└── integration/               # Integration tests across components
    ├── test_audio_pipeline.py # Complete audio processing pipeline
    └── test_error_handling.py # Error handling and edge cases
```

## Running Tests

### Prerequisites

Install required dependencies:
```bash
pip install pytest soundfile
```

Optional dependencies for full test coverage:
```bash
pip install pytest-cov pytest-xdist pytest-timeout
```

### Basic Usage

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test categories:
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Player-related tests
pytest -m player

# DSP functionality tests
pytest -m dsp

# Fast tests (exclude slow ones)
pytest -m "not slow"
```

### Using the Test Runner

The `test_runner.py` script provides convenient commands:

```bash
# Run all tests
python tests/test_runner.py all

# Run unit tests
python tests/test_runner.py unit

# Run integration tests
python tests/test_runner.py integration

# Run fast tests only
python tests/test_runner.py fast

# Run performance tests
python tests/test_runner.py performance
```

### Test Categories (Markers)

Tests are organized with the following markers:

- `unit` - Unit tests for individual components
- `integration` - Integration tests across components
- `slow` - Tests that take significant time
- `audio` - Tests requiring audio processing
- `files` - Tests requiring file I/O
- `player` - Tests for the matchering player
- `core` - Tests for the core matchering library
- `dsp` - Tests for DSP functionality
- `performance` - Performance and benchmark tests
- `error` - Error handling and edge case tests

### Running Specific Tests

Run a specific test file:
```bash
pytest tests/unit/test_dsp_core.py
```

Run a specific test method:
```bash
pytest tests/unit/test_dsp_core.py::TestDSPCore::test_basic_dsp_functions
```

Run tests matching a pattern:
```bash
pytest -k "dsp"
pytest -k "frequency"
```

### Coverage Reports

Generate coverage report:
```bash
pytest --cov=matchering --cov=matchering_player --cov-report=html
```

View coverage in terminal:
```bash
pytest --cov=matchering --cov=matchering_player --cov-report=term-missing
```

## Test Configuration

### pytest.ini

The `pytest.ini` file in the project root configures:
- Test discovery patterns
- Default markers
- Timeout settings
- Warning filters

### conftest.py

The `conftest.py` file provides:
- Shared fixtures for test data
- Audio generation utilities
- Configuration objects
- Dependency checking
- Assertion helpers

## Available Fixtures

### Configuration Fixtures
- `test_config` - Basic player configuration
- `full_config` - Full-featured configuration with all effects
- `sample_rates` - List of standard sample rates
- `bit_depths` - List of supported bit depths

### Audio Fixtures
- `sine_wave` - Generate sine wave test audio
- `white_noise` - Generate white noise test audio
- `audio_pair` - Generate quiet target and loud reference pair
- `test_audio_files` - Create standard test audio files

### Utility Fixtures
- `temp_dir` - Temporary directory for test files

## Writing New Tests

### Basic Test Structure

```python
import pytest
import numpy as np
from tests.conftest import assert_audio_equal

@pytest.mark.unit
@pytest.mark.dsp
def test_my_dsp_function(sine_wave):
    """Test my DSP function"""
    audio, sr = sine_wave(1.0, 44100, 440, 0.5)

    # Test your function
    result = my_dsp_function(audio)

    # Assertions
    assert result.shape == audio.shape
    assert_audio_equal(result, expected_result)
```

### Test Classes

```python
@pytest.mark.unit
@pytest.mark.player
class TestMyPlayerComponent:
    """Test my player component"""

    def test_initialization(self, test_config):
        """Test component initialization"""
        component = MyPlayerComponent(test_config)
        assert component is not None

    def test_processing(self, test_config, sine_wave):
        """Test component processing"""
        component = MyPlayerComponent(test_config)
        audio, sr = sine_wave()
        result = component.process(audio)
        assert result.shape == audio.shape
```

### Error Handling Tests

```python
@pytest.mark.unit
@pytest.mark.error
def test_invalid_input_handling():
    """Test handling of invalid inputs"""
    with pytest.raises(ValueError):
        my_function(invalid_input)

    # Or test graceful handling
    result = my_function(edge_case_input)
    assert result is not None
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.audio
@pytest.mark.slow
def test_full_pipeline(test_audio_files, temp_dir):
    """Test complete processing pipeline"""
    # Load test files
    input_file = test_audio_files["quiet_target.wav"]
    reference_file = test_audio_files["loud_reference.wav"]
    output_file = temp_dir / "output.wav"

    # Process
    process_audio(input_file, reference_file, output_file)

    # Verify
    assert output_file.exists()
    # Additional verification...
```

## Troubleshooting

### Common Issues

1. **ImportError for matchering modules**
   - Ensure the project is installed: `pip install -e .`
   - Check that PYTHONPATH includes the project root

2. **soundfile not available**
   - Install: `pip install soundfile`
   - Some tests will be skipped without soundfile

3. **PyAudio not available**
   - Player tests may be skipped
   - Install: `pip install pyaudio` (may require system dependencies)

4. **Tests timing out**
   - Increase timeout: `pytest --timeout=300`
   - Run fast tests only: `pytest -m "not slow"`

### Debugging Tests

Run with debugging output:
```bash
pytest -s -vv
```

Drop into debugger on failure:
```bash
pytest --pdb
```

Run specific test with full traceback:
```bash
pytest --tb=long tests/path/to/test.py::test_name
```

## Contributing

When adding new functionality:

1. Write unit tests for individual components
2. Write integration tests for cross-component functionality
3. Add appropriate markers to organize tests
4. Include error handling tests for edge cases
5. Add performance tests for computationally intensive features
6. Update fixtures and conftest.py if needed

### Test Coverage Goals

- Maintain >80% code coverage
- All public APIs should have unit tests
- Critical paths should have integration tests
- Error conditions should be tested
- Performance regressions should be caught by benchmarks