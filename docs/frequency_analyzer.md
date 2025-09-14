# Frequency Analyzer Documentation

The frequency analyzer component (`FrequencyAnalyzer`) provides comprehensive audio signal analysis capabilities including spectrum analysis, loudness measurement, and frequency band processing. This document details its implementation, key features, and technical specifications.

## Core Features

### 1. Spectrum Analysis
- **Window-based FFT analysis** using Welch's method with 50% overlap
- **Automatic resolution adaptation** for low frequencies via zero-padding
- **Cached frequency axis** to ensure consistent analysis across operations
- Support for custom window sizes to balance time/frequency resolution

### 2. Peak Detection
- **Adaptive prominence thresholds** based on local noise floor
- **Frequency-dependent peak separation** to handle both low and high frequencies
- **Logarithmic frequency scaling** for peak prominence calculation
- Output ordered by magnitude with optional minimum threshold

### 3. Band Energy Analysis
- **Octave-band division** from 20 Hz to 20 kHz
- **Power density normalization** per octave width
- **Logarithmic frequency weighting** to match perceptual sensitivity
- **Dynamic range compression** for more balanced band comparison

### 4. Level Measurements

#### RMS Calculation
```python
def calculate_rms(self, audio_data: np.ndarray) -> float:
    squared = audio_data ** 2
    mean_power = np.mean(squared)  # Average power across all samples
    return float(np.sqrt(mean_power))
```

The RMS calculation considers all samples equally to compute true average power, regardless of channel count. This ensures accurate power measurement even with complex multichannel signals.

#### Peak Level Detection
```python
def calculate_peak(self, audio_data: np.ndarray) -> float:
    channel_peaks = np.max(np.abs(audio_data), axis=0)
    return float(np.max(channel_peaks))
```

Finds the absolute peak value across all channels, essential for headroom analysis and normalization.

### 5. LUFS Loudness Measurement

The analyzer implements the ITU-R BS.1770-4 loudness measurement algorithm with the following key components:

#### K-weighting Filters
```python
# High-shelf filter (+4 dB @ 1681 Hz)
b_high = [1.53512485958697, -2.69169618940638, 1.19839281085285]
a_high = [1.0, -1.69065929318241, 0.73248077421585]

# High-pass filter (-3 dB @ 38 Hz)
b_hp = [1.0, -2.0, 1.0]
a_hp = [1.0, -1.99004745483398, 0.99007225036621]
```

These filters implement the K-weighting curve specified in BS.1770:
- Pre-filter: High-shelf boost simulating head diffraction
- RLB-weighting: Roll-off below 38 Hz

#### Block Processing
- 400ms blocks with 75% overlap
- Gating in two stages:
  1. Absolute gate at -70 LUFS
  2. Relative gate 10 LU below ungated level

#### Channel Weights
```python
# Stereo channel weights
self._channel_weights = [1.0, 1.0]  # L/R equal weighting
```

Channel weights follow BS.1770-4 specifications for typical channel configurations.

## Implementation Notes

### Test Signal Generation

The test framework uses a deterministic RNG to ensure reproducible results:

```python
self.rng = np.random.default_rng(12345)  # Fixed seed for reproducibility
```

This enables consistent validation of:
- White noise spectrum flatness
- Pink noise -3 dB/octave slope
- RMS levels and crest factors
- LUFS measurements

### Frequency Band Processing

Band energy calculation uses several techniques for accurate measurement:

1. **Power per Octave Normalization**
```python
octave_width = np.log2(band_freqs[-1] / band_freqs[0])
psd = band_spectrum**2 / df  # Power density spectrum
```

2. **Logarithmic Frequency Weighting**
```python
weighted_psd = psd * np.sqrt(band_freqs / 1000.0)
power = np.trapezoid(weighted_psd, np.log2(band_freqs))
```

3. **Dynamic Range Control**
```python
energies = energies / np.max(energies)  # Normalize
energies = np.power(energies, 0.8)      # Mild compression
```

### Tolerance Management

The analyzer manages measurement tolerances:
- RMS: Within 1% of expected values
- Peak: Within 1% of expected values
- LUFS: Within 0.6 dB of expected values
- Band slopes: Within 2 dB/decade for noise signals
- Band energy deviation: Maximum 20 dB variation

## Usage Examples

### Basic Spectrum Analysis
```python
analyzer = FrequencyAnalyzer(sample_rate=44100)
spectrum = analyzer.analyze_spectrum(audio_data)
peaks = analyzer.find_peak_frequencies(spectrum, threshold=-60)
```

### Loudness Measurement
```python
lufs = analyzer.calculate_lufs(audio_data)
rms = analyzer.calculate_rms(audio_data)
peak = analyzer.calculate_peak(audio_data)
```

### Band Energy Analysis
```python
bands = analyzer.get_frequency_bands()
energies = analyzer.calculate_band_energies(audio_data)
energy_db = 20 * np.log10(energies)
```

## Performance Considerations

- Uses zero-phase filtering where phase accuracy is critical
- Implements efficient block processing for LUFS calculation
- Caches frequency axes to avoid redundant computation
- Optimizes window sizes for various analysis tasks
- Employs vectorized operations for performance

## Test Suite Coverage

The comprehensive test suite validates:
1. Sine wave detection accuracy
2. Noise spectrum characteristics
3. RMS and peak level accuracy
4. LUFS measurement precision
5. Band division correctness
6. Energy distribution balance

Each test includes specific tolerance thresholds appropriate for the measurement type.

## References

1. ITU-R BS.1770-4: "Algorithms to measure audio programme loudness and true-peak audio level"
2. AES17-2015: "AES standard method for digital audio engineering - Measurement of digital audio equipment"
3. Welch's method: P. Welch, "The use of fast Fourier transform for the estimation of power spectra"