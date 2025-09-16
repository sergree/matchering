# Matchering Player - Development Plan

## 🎯 Project Vision

**Matchering Player** is a realtime media player that gradually applies audio matching and mastering effects while playing, creating an adaptive listening experience that matches your music to a reference track's characteristics.

## 📋 Current Matchering Architecture Analysis

### ✅ Reusable Components from Matchering 2.0
- **DSP Functions** (`dsp.py`): All mathematical operations (RMS, amplify, normalize, lr_to_ms, etc.)
- **Level Analysis** (`stage_helpers/match_levels.py`): RMS calculation and level matching logic
- **Configuration System** (`defaults.py`): Config classes and parameter management
- **Mid-Side Processing**: Perfect for stereo width control
- **Limiter** (`limiter/`): Hyrax brickwall limiter for realtime use

### ⚠️ Components Requiring Adaptation
- **Batch Processing → Streaming**: Current `max_piece_size = 15 seconds` → Need `~100ms` chunks
- **File I/O → Audio Streams**: Replace `loader.py` with audio stream interfaces
- **Frequency Matching**: Complex FIR filtering needs optimization for realtime
- **Memory Management**: Current system loads entire files, need circular buffers

## 🏗️ Matchering Player Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Matchering Player                        │
├─────────────────────────────────────────────────────────────┤
│  Audio Input    │  Processing Engine  │    Audio Output     │
│  ─────────────  │  ──────────────────  │  ─────────────────  │
│  • File Reader  │  • Reference        │  • Stream Buffer    │
│  • Stream Input │    Analyzer         │  • Audio Device     │
│  • URL Stream   │  • Level Matcher    │  • File Writer      │
│                 │  • Freq. Matcher    │                     │
│                 │  • Realtime Limiter │                     │
│                 │  • Effect Chain     │                     │
├─────────────────────────────────────────────────────────────┤
│                    Control Interface                        │
│  • Playback Controls  • Effect Parameters  • Visualization │
└─────────────────────────────────────────────────────────────┘
```

### Processing Pipeline

```
Audio Input (44.1kHz)
    ↓
┌─────────────────────────────────────────┐
│ Audio Buffer Manager                    │
│ • Circular input buffer (1-2 seconds)   │
│ • Lookahead buffer (500ms)              │
│ • Output buffer (100ms)                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Reference Profile Manager               │
│ • Load/cache reference characteristics  │
│ • Adaptive reference learning           │
│ • Statistics persistence                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Realtime Processing Chain               │
│ 1. Mid-Side Conversion                  │
│ 2. Level Analysis (RMS calculation)     │
│ 3. Level Matching (gain adjustment)     │
│ 4. Frequency Matching (EQ/filtering)    │
│ 5. Limiting (Hyrax algorithm)           │
│ 6. Mid-Side to L/R Conversion           │
└─────────────────────────────────────────┘
    ↓
Audio Output (44.1kHz)
```

## 📱 MVP Requirements

### Phase 1: Core Player (Weeks 1-3)
**Goal**: Basic media player with level matching

**Features**:
- ✅ Play/pause/stop/seek audio files (WAV, MP3, FLAC)
- ✅ Basic GUI with waveform visualization
- ✅ Realtime level matching (RMS adjustment only)
- ✅ Reference track selection and caching
- ✅ Bypass/enable effect toggle

**Technical Specs**:
- Buffer size: 100ms chunks (4410 samples @ 44.1kHz)
- Processing latency: <10ms
- Supported formats: WAV, MP3 (via FFmpeg), FLAC
- Reference caching: Simple RMS statistics

### Phase 2: Enhanced Processing (Weeks 4-6)
**Goal**: Add frequency matching and improved analysis

**Features**:
- ✅ Frequency response matching (basic EQ curves)
- ✅ Stereo width adjustment
- ✅ Advanced reference analysis caching
- ✅ Real-time audio visualization (spectrum, levels)
- ✅ Effect intensity slider (0-100%)

### Phase 3: Advanced Features (Weeks 7-10)
**Goal**: Professional-grade features and optimization

**Features**:
- ✅ Multi-reference support (different references per genre/mood)
- ✅ Adaptive reference learning from listening history
- ✅ Export processed audio to file
- ✅ Plugin architecture for custom effects
- ✅ Performance optimization and multi-threading

### Phase 4: User Experience (Weeks 11-12)
**Goal**: Polish and user-friendly features

**Features**:
- ✅ Playlist management with per-track reference assignment
- ✅ Presets system (Rock Master, Pop Master, etc.)
- ✅ Audio preferences and quality settings
- ✅ Performance metrics and diagnostics

## 🛠️ Detailed Development Phases

### Phase 1: Foundation (Weeks 1-3)

#### Week 1: Core Infrastructure
```python
# Project structure
matchering_player/
├── __init__.py
├── core/
│   ├── audio_manager.py      # Audio I/O and buffer management
│   ├── processor.py          # Main processing engine
│   └── config.py            # Configuration management
├── dsp/                     # Adapted from Matchering
│   ├── __init__.py
│   ├── basic.py            # Core DSP functions
│   ├── levels.py           # Level analysis/matching
│   └── limiter.py          # Realtime limiting
├── ui/
│   ├── player_window.py    # Main GUI
│   └── controls.py         # Playback controls
└── utils/
    ├── file_loader.py      # File format support
    └── reference_cache.py  # Reference management
```

**Key Deliverables**:
1. **Audio Manager**: PyAudio-based playback with circular buffers
2. **Basic Processor**: Level matching only (using Matchering's RMS functions)
3. **Simple GUI**: Play/pause/stop with basic visualization
4. **File Loading**: WAV support first, then MP3/FLAC

#### Week 2: Processing Engine
**Focus**: Adapt Matchering's level matching for realtime

```python
class RealtimeProcessor:
    def __init__(self, config: MatcheringPlayerConfig):
        self.buffer_size = config.buffer_size  # 4410 samples (100ms)
        self.reference_rms = None
        self.level_smoother = ExponentialSmoother(alpha=0.1)
    
    def process_chunk(self, audio_chunk: np.ndarray) -> np.ndarray:
        # Convert to Mid-Side
        mid, side = lr_to_ms(audio_chunk)
        
        # Calculate RMS for this chunk
        current_rms = rms(mid)
        
        # Smooth the gain adjustment
        if self.reference_rms:
            gain = self.level_smoother.update(
                self.reference_rms / max(current_rms, config.min_value)
            )
            mid = amplify(mid, gain)
            side = amplify(side, gain)
        
        # Convert back to L/R
        return ms_to_lr(mid, side)
```

#### Week 3: Integration and Testing
- Reference track analysis and caching
- GUI integration with real-time effect toggle
- Performance optimization for consistent 44.1kHz processing
- Basic error handling and logging

### Phase 2: Enhanced Processing (Weeks 4-6)

#### Week 4: Frequency Analysis
**Challenge**: Adapt Matchering's frequency matching for realtime

**Solution**: Simplified approach using parametric EQ instead of FIR filters
```python
class RealtimeFrequencyMatcher:
    def __init__(self):
        # Use parametric EQ bands instead of full FFT analysis
        self.eq_bands = [
            ParametricEQ(freq=100, q=1.0),   # Sub-bass
            ParametricEQ(freq=300, q=1.0),   # Bass
            ParametricEQ(freq=1000, q=1.0),  # Midrange
            ParametricEQ(freq=3000, q=1.0),  # Upper-mid
            ParametricEQ(freq=8000, q=1.0),  # Presence
        ]
    
    def match_frequency_response(self, chunk, reference_spectrum):
        # Apply EQ adjustments based on reference spectrum
        for band in self.eq_bands:
            chunk = band.process(chunk)
        return chunk
```

#### Week 5-6: Stereo Width and Advanced Analysis
- Implement stereo width matching using Mid-Side processing
- Advanced reference analysis with spectrum caching
- Real-time visualization improvements

### Phase 3: Advanced Features (Weeks 7-10)

#### Technical Optimizations:
1. **Multi-threading**: Separate audio thread from processing thread
2. **SIMD Optimizations**: Use NumPy's optimized operations
3. **Memory Management**: Zero-copy buffer operations where possible
4. **Adaptive Quality**: Lower processing quality during high CPU load

#### Advanced Reference System:
```python
class AdaptiveReferenceManager:
    def learn_from_playback(self, audio_data, user_rating):
        """Learn reference characteristics from user behavior"""
        pass
    
    def get_contextual_reference(self, genre, mood, time_of_day):
        """Select optimal reference based on context"""
        pass
```

## 🚀 Technical Implementation Strategy

### Dependencies and Tools

**Core Audio**:
```bash
# Core dependencies
pip install numpy scipy soundfile pyaudio
pip install librosa  # For advanced audio analysis
pip install resampy  # Sample rate conversion
```

**GUI Framework**:
```bash
# Option 1: PyQt6 (recommended for professional look)
pip install PyQt6

# Option 2: Tkinter (built-in, simpler)
# Built into Python

# Option 3: Web-based (for cross-platform)
pip install flask socketio
```

**Audio Format Support**:
```bash
# FFmpeg for comprehensive format support
# System dependency - varies by OS
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Processing Latency | <10ms | Buffer to speaker |
| CPU Usage | <20% | During playback on modern CPU |
| Memory Usage | <100MB | Excluding audio buffers |
| Buffer Underruns | <0.1% | During continuous playback |

### Risk Mitigation

**Risk 1: Real-time Performance**
- *Mitigation*: Extensive profiling, fallback to lower quality processing
- *Testing*: Automated performance benchmarks

**Risk 2: Audio Quality Degradation**
- *Mitigation*: A/B testing system, bypass mode always available
- *Testing*: Golden ear testing with reference tracks

**Risk 3: Format Compatibility**
- *Mitigation*: FFmpeg integration, extensive format testing
- *Testing*: Automated tests with various file formats

## 📊 Success Metrics

### Technical Metrics:
- ✅ Consistent 44.1kHz playback without dropouts
- ✅ <10ms processing latency
- ✅ Support for major audio formats (WAV, MP3, FLAC, M4A)
- ✅ Memory usage <100MB during playback

### User Experience Metrics:
- ✅ Intuitive reference track selection process
- ✅ Immediate audio improvement perception
- ✅ Stable, crash-free operation
- ✅ Cross-platform compatibility (Windows, macOS, Linux)

### Advanced Metrics (Phase 3+):
- ✅ Machine learning-based reference optimization
- ✅ Plugin ecosystem support
- ✅ Professional studio integration capabilities

## 🎵 Demo Scenarios

### Scenario 1: "Make My Demo Sound Like a Hit"
- User loads their home recording
- Selects professional reference track
- Player gradually applies matching to make demo sound polished

### Scenario 2: "Consistent Album Experience"
- User loads playlist of various mastered songs
- Player normalizes loudness and tonal balance across tracks
- Creates cohesive listening experience

### Scenario 3: "Live Performance Enhancement"
- Real-time processing of live input (microphone/interface)
- Reference matching for consistent sound during live streams
- Export capability for recording sessions

---

*This development plan provides a roadmap for creating a revolutionary audio player that brings professional mastering capabilities to everyday music listening.*
