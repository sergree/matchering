# Test Signal Generation Guide

This guide documents the test signals used for validating the FrequencyAnalyzer implementation. Each signal is designed to test specific aspects of the analysis pipeline.

## Basic Test Signals

### 1. Single Sine Wave
```python
def sine_wave(self, frequency: float = 1000.0, duration: float = 1.0,
            amplitude: float = 0.5):
    """1 kHz reference sine wave at -6 dBFS."""
    t = np.linspace(0, duration, int(self.sample_rate * duration))
    mono = amplitude * np.sin(2 * np.pi * frequency * t)
    return np.column_stack((mono, mono))  # Stereo
```

**Properties:**
- Frequency: 1 kHz (standard reference)
- Level: -6 dBFS peak (-9 dBFS RMS)
- LUFS: -8.81 LUFS (with K-weighting)
- Crest Factor: √2 (~3.01 dB)

**Test Coverage:**
- Peak detection accuracy
- Frequency bin mapping
- Level measurement calibration
- LUFS reference tone measurement

### 2. Dual Sine Wave
```python
def multi_sine(self, frequencies: List[float] = [100.0, 1000.0],
             amplitudes: List[float] = [0.3, 0.3]):
    """100 Hz + 1 kHz dual tone test."""
    t = np.linspace(0, duration, int(self.sample_rate * duration))
    mono = np.zeros_like(t)
    for freq, amp in zip(frequencies, amplitudes):
        mono += amp * np.sin(2 * np.pi * freq * t)
    return np.column_stack((mono, mono))
```

**Properties:**
- Frequencies: 100 Hz and 1 kHz
- Level: -4.4 dBFS peak (-10.5 dBFS RMS)
- LUFS: -11.08 LUFS
- Crest Factor: 2.0 (6 dB)

**Test Coverage:**
- Multi-peak detection
- Peak magnitude comparison
- Interaction between components
- Low frequency resolution

## Noise Signals

### 1. White Noise
```python
def white_noise(self, duration: float = 1.0, amplitude: float = 0.5):
    """White noise with flat spectrum."""
    samples = int(self.sample_rate * duration)
    mono = amplitude * (2 * self.rng.random(samples) - 1)
    return np.column_stack((mono, mono))
```

**Properties:**
- Spectrum: Flat (0 dB/decade slope)
- Level: -6 dBFS peak
- RMS: 0.289 (-10.8 dBFS)
- LUFS: -7.57 LUFS
- Distribution: Uniform [-0.5, 0.5]

**Test Coverage:**
- Spectral flatness
- RMS vs peak relationship
- Band energy distribution
- Statistical properties

### 2. Pink Noise
```python
def pink_noise(self, duration: float = 1.0, amplitude: float = 0.5):
    """Pink noise with -3 dB/octave slope."""
    # Generate white noise first
    white = self.white_noise(duration)
    
    # Pink filter coefficients (-3 dB/octave)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    
    # Filter and normalize
    mono = signal.lfilter(b, a, white[:, 0])
    mono = amplitude * mono / np.max(np.abs(mono))
    return np.column_stack((mono, mono))
```

**Properties:**
- Spectrum: -3 dB/octave slope
- Level: -6 dBFS peak
- RMS: 0.1335 (-17.5 dBFS)
- LUFS: -17.30 LUFS
- Crest Factor: ~3.75

**Test Coverage:**
- Spectral slope accuracy
- Filter implementation
- Loudness weighting
- Noise floor estimation

## Dynamic Signals

### Frequency Sweep
```python
def frequency_sweep(self, start_freq: float = 20.0,
                   end_freq: float = 20000.0,
                   duration: float = 5.0):
    """Logarithmic frequency sweep (chirp)."""
    t = np.linspace(0, duration, int(self.sample_rate * duration))
    phase = 2 * np.pi * start_freq * duration / np.log(end_freq/start_freq)
    mono = np.sin(phase * (np.exp(t * np.log(end_freq/start_freq) / duration) - 1))
    return np.column_stack((mono, mono))
```

**Properties:**
- Frequency Range: 20 Hz to 20 kHz
- Sweep Type: Logarithmic
- Duration: 5 seconds
- Level: 0 dBFS peak (-3 dBFS RMS)

**Test Coverage:**
- Band energy tracking
- Frequency resolution
- Time-frequency balance
- Window size adaptation

## Test Validation

### Level Tolerances
```python
# RMS test
assert abs(rms - info.expected_rms) < 0.01 * info.expected_rms

# Peak test  
assert abs(peak - info.expected_peak) < 0.01 * info.expected_peak

# LUFS test
assert abs(lufs - info.expected_lufs) < 0.6  # dB
```

### Spectral Tolerances
```python
# White noise slope
assert abs(slope) < 1.0  # dB/decade

# Pink noise slope
assert abs(slope + 10) < 2.0  # dB/decade from -10

# Peak detection
assert abs(peak_freq - 1000.0) < 10.0  # Hz
```

### Band Energy Tolerances
```python
# Energy distribution
max_deviation = np.max(energy_db) - np.min(energy_db)
assert max_deviation < 20  # dB

# Octave spacing
octaves = np.log2(band.end_freq / band.start_freq)
assert 0.8 < octaves < 1.2
```

## Implementation Notes

### Reproducibility
- Fixed random seed for noise generation
- Deterministic filter coefficients
- Consistent signal durations
- Standard reference levels

### Signal Generation
- All signals are stereo (identical channels)
- Sample rate matches analyzer setting
- Normalized to specified peak levels
- Defined segment boundaries

### Common Parameters
- Sample Rate: 44100 Hz
- Bit Depth: 32-bit float
- Duration: 1-5 seconds
- Channel Count: 2 (stereo)

## References

1. IEC 61260-1:2014 - Electroacoustics - Octave-band and fractional-octave-band filters
2. AES17-2015 - AES standard method for digital audio engineering
3. ITU-R BS.1770-4 - Algorithms to measure audio programme loudness
4. Meyer, David G. "Digital Signal Processing Techniques for Audio Testing"