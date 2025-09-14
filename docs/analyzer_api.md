# FrequencyAnalyzer API Documentation

## Class Overview

```python
class FrequencyAnalyzer:
    """Handles frequency-domain analysis of audio signals.
    
    The FrequencyAnalyzer provides comprehensive audio signal analysis capabilities:
    - Spectrum analysis with automatic resolution adaptation
    - Peak frequency detection with adaptive thresholds
    - RMS and peak level measurement
    - LUFS loudness measurement (ITU-R BS.1770-4 compliant)
    - Frequency band energy analysis
    
    The analyzer maintains internal state for frequency axis caching and 
    implements several optimizations for performance and accuracy.
    """
```

## Constructor

```python
def __init__(self, sample_rate: int = 44100):
    """Initialize analyzer.
    
    Args:
        sample_rate: Sample rate in Hz. Defaults to 44100 Hz.
    """
```

## Core Methods

### Spectrum Analysis

```python
def analyze_spectrum(self, audio_data: np.ndarray, window_size: Optional[int] = None) -> np.ndarray:
    """Analyze frequency spectrum of audio data.
    
    Uses Welch's method for spectrum estimation with configurable windowing
    and overlap. Zero-pads input to improve frequency resolution for low 
    frequencies.
    
    Args:
        audio_data: Audio data array of shape (samples, channels)
        window_size: Optional override for FFT size
            
    Returns:
        Magnitude spectrum array, normalized to maximum of 1.0
    
    The spectrum analysis:
    - Applies 4x zero-padding for improved low frequency resolution
    - Uses Hann window with 50% overlap
    - Averages across channels preserving power relationships
    - Caches frequency axis for consistent downstream processing
    """

def get_frequencies(self) -> np.ndarray:
    """Get frequencies for FFT bins.
    
    If a spectrum was recently computed, returns its exact frequency axis.
    Otherwise returns theoretical frequencies for current window size.
    
    Returns:
        Array of frequencies in Hz
    """

def frequency_to_bin(self, freq: float) -> int:
    """Convert frequency to FFT bin number.
    
    Args:
        freq: Frequency in Hz
            
    Returns:
        FFT bin number
    """
```

### Peak Detection

```python
def find_peak_frequencies(self, spectrum: np.ndarray,
                       threshold: float = -60) -> List[float]:
    """Find peak frequencies in spectrum.
    
    Uses adaptive prominence threshold based on local noise floor to improve
    detection of both strong and weak peaks. Peak separation is adjusted
    based on frequency to handle both low and high frequency components.
    
    Args:
        spectrum: Magnitude spectrum array
        threshold: Detection threshold in dB below maximum
            
    Returns:
        List of peak frequencies in Hz, sorted by magnitude
    
    The peak detection:
    - Uses shorter windows for low frequency noise floor estimation
    - Adapts prominence thresholds based on local levels
    - Applies frequency-dependent peak separation criteria
    - Orders peaks by magnitude with minimum relative threshold
    """
```

### Level Measurements

```python
def calculate_rms(self, audio_data: np.ndarray) -> float:
    """Calculate RMS level of audio data.
    
    Computes true RMS by averaging power across all samples and channels.
    
    Args:
        audio_data: Audio data array
            
    Returns:
        RMS level between 0.0 and 1.0
    """

def calculate_peak(self, audio_data: np.ndarray) -> float:
    """Calculate peak level of audio data.
    
    Takes maximum absolute value across all channels.
    
    Args:
        audio_data: Audio data array
            
    Returns:
        Peak level between 0.0 and 1.0
    """

def calculate_lufs(self, audio_data: np.ndarray) -> float:
    """Calculate LUFS-I loudness of audio data.
    
    Implements ITU-R BS.1770-4 integrated loudness measurement with K-weighting
    and gating as specified in the standard.
    
    Args:
        audio_data: Audio data array
            
    Returns:
        LUFS-I level
    
    The LUFS calculation:
    - Applies K-weighting filters (pre-filter + RLB)
    - Processes 400ms blocks with 75% overlap
    - Uses two-stage gating (-70 LUFS absolute, -10 LU relative)
    - Handles mono/stereo with correct channel weights
    - Returns level calibrated to ITU-R BS.1770-4 reference
    """
```

### Band Processing

```python
def get_frequency_bands(self) -> List[FrequencyBand]:
    """Get frequency band information.
    
    Returns frequency bands spanning 20 Hz to 20 kHz in roughly
    one octave increments.
    
    Returns:
        List of FrequencyBand objects containing:
        - start_freq: Band start frequency in Hz
        - end_freq: Band end frequency in Hz  
        - center_freq: Geometric mean frequency in Hz
    """

def calculate_band_energies(self, audio_data: np.ndarray) -> np.ndarray:
    """Calculate energy in each frequency band.
    
    Computes band energies with octave-based normalization and
    perceptual weighting.
    
    Args:
        audio_data: Audio data array
            
    Returns:
        Array of band energies, normalized between 0 and 1
    
    The band energy calculation:
    - Normalizes by octave width to reduce bias toward wider bands
    - Applies frequency weighting for perceptual relevance  
    - Uses trapezoidal integration over log-frequency
    - Includes mild dynamic range compression
    """
```

## Helper Classes

```python
@dataclass
class FrequencyBand:
    """Represents a frequency band for analysis.
    
    Attributes:
        start_freq: Lower band edge frequency in Hz
        end_freq: Upper band edge frequency in Hz
        center_freq: Geometric mean frequency in Hz
    """
    start_freq: float
    end_freq: float  
    center_freq: float
```

## Usage Notes

### Audio Data Format
- Input audio data should be normalized to ±1.0 range
- Multichannel audio should be shaped as (samples, channels)
- Sample rate must match the one specified in constructor

### Performance Optimization
- Frequency axis is cached after spectrum analysis
- Window sizes are adapted based on analysis needs
- Vectorized operations are used where possible

### Measurement Accuracy
- RMS measurements are accurate within 1%
- LUFS measurements follow BS.1770-4 to within 0.6 dB
- Spectral analysis resolution improves at low frequencies
- Band energy measurements use perceptually relevant scaling

### Thread Safety
- The analyzer maintains internal state
- Concurrent use should be protected by locks
- Consider using separate instances for parallel processing