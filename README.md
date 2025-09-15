# 🎵 Matchering Player

**Real-time Audio Mastering with Live Reference Matching**

[![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Tests](https://img.shields.io/badge/tests-66%20passing-brightgreen.svg)]()

---

## 🎧 Experience Mastering in Real-time

**Matchering Player** is an innovative audio application that brings **real-time mastering** to your workflow. Load your audio and a reference track, then hear professional mastering applied instantly while you make adjustments.

### ✨ What Makes It Special

- **🎛️ Live Mastering**: Hear mastering effects applied in real-time as you adjust parameters
- **🔄 Instant A/B**: Switch between original and processed audio with one click
- **📊 Visual Feedback**: See real-time audio analysis, frequency response, and processing statistics
- **🚀 Professional Speed**: Process audio at 25-111x real-time speed
- **🎨 Multiple Interfaces**: Choose from modern, basic, or launcher GUI styles
- **🌍 Cross-platform**: Works seamlessly on Windows, macOS, and Linux

![Matchering Player Demo](images/player_screenshot.png)

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/matchering-player.git
cd matchering-player

# Install dependencies
pip install -r requirements.txt

# Launch the modern GUI
python modern_gui.py
```

### Basic Usage

1. **Load your audio**: Click "Load Target" to select the track you want to master
2. **Choose reference**: Click "Load Reference" to select your reference track
3. **Play and adjust**: Hit play and adjust mastering parameters in real-time
4. **A/B compare**: Toggle between original and processed audio instantly
5. **Export when ready**: Save your mastered audio when you're satisfied

---

## 🎛️ Features

### Real-time Processing
- **Live Parameter Adjustment**: Change settings and hear results immediately
- **Zero-latency Monitoring**: No delay between adjustments and audio output
- **Professional Algorithms**: Same mastering quality as offline processing
- **Smooth Transitions**: No audio artifacts when changing parameters

### Advanced DSP
- **RMS Level Matching**: Match perceived loudness between tracks
- **Frequency Response Matching**: Real-time EQ matching with spectral analysis
- **Stereo Width Control**: Adjust stereo imaging and spatial characteristics
- **Auto-mastering**: Intelligent automatic processing based on reference
- **Peak Limiting**: Professional brickwall limiter prevents clipping

### Visual Analysis
- **Real-time Meters**: RMS and peak level monitoring
- **Frequency Analysis**: Live frequency response visualization
- **Processing Statistics**: Monitor CPU usage and processing speed
- **Waveform Display**: Visual representation of audio content

### Multiple Interfaces

#### 🖥️ Modern GUI (`python modern_gui.py`)
Professional interface with advanced controls and visual feedback

#### 🎯 Simple Launcher (`python launch_gui.py`)
Streamlined interface for quick access to essential features

#### ⚡ Basic Interface (`python gui_demo.py`)
Lightweight option for basic mastering tasks

---

## 🏆 Performance

### Speed Benchmarks
- **25-111x Real-time**: Process audio much faster than playback speed
- **Large File Support**: Handle 2+ minute files at 100x real-time
- **Memory Efficient**: Optimized for extended use with large files
- **Low CPU Usage**: Multi-core processing for maximum efficiency

### File Support
- **Formats**: WAV, FLAC, MP3 (with FFmpeg), AIFF, and more
- **Sample Rates**: 22.05kHz to 96kHz supported
- **Bit Depths**: 16-bit, 24-bit, and 32-bit processing
- **Channels**: Mono and stereo audio

### Quality Assurance
- **66 Comprehensive Tests**: End-to-end validation of all features
- **Cross-platform Tested**: Verified on Windows, macOS, and Linux
- **Professional Standards**: Audio quality meets industry mastering requirements
- **Zero Artifacts**: Clean processing with no unwanted distortion

---

## 🎯 Use Cases

### 🎼 Music Producers
- **Reference Matching**: Make your tracks sound like your favorite artists
- **Album Consistency**: Ensure all songs have the same sonic character
- **Creative Exploration**: Experiment with different reference tracks instantly
- **Demo Polishing**: Quickly master demos for client presentations

### 🎚️ Audio Engineers
- **Client Previews**: Show mastering results to clients in real-time
- **Quality Control**: Verify mastering decisions before final processing
- **Educational Tool**: Demonstrate mastering concepts with live examples
- **Workflow Efficiency**: Speed up mastering with immediate feedback

### 📹 Content Creators
- **Podcast Mastering**: Match your podcast to professional standards
- **Video Audio**: Ensure consistent audio across video content
- **Streaming Optimization**: Optimize for different platforms instantly
- **Quick Turnaround**: Fast mastering for time-sensitive content

---

## 🛠️ Technical Specifications

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **RAM**: 4GB minimum (8GB recommended for large files)
- **CPU**: Multi-core processor recommended
- **Storage**: 200MB for installation + space for audio files
- **Audio**: Any compatible audio interface or built-in audio

### Dependencies
- **Python**: 3.8 or higher
- **NumPy**: For numerical processing
- **SciPy**: For signal processing algorithms
- **SoundFile**: For audio file I/O
- **Tkinter**: For GUI interface (usually included with Python)
- **Optional**: FFmpeg for MP3 support

---

## 📚 Documentation

### Getting Started
- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [User Interface Guide](docs/interface.md)

### Advanced Usage
- [Mastering Best Practices](docs/mastering_guide.md)
- [Performance Optimization](docs/performance.md)
- [Troubleshooting](docs/troubleshooting.md)

### Development
- [API Documentation](docs/api.md)
- [Testing Guide](docs/testing.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## 🧪 Testing & Quality

### Comprehensive Test Suite
- **39 End-to-end Tests**: Complete workflow validation
- **13 Performance Benchmarks**: Speed and scalability verification
- **14 Cross-platform Tests**: Compatibility across all platforms
- **Zero Test Failures**: All tests passing for production readiness

### Quality Metrics
- **Audio Quality**: Validated against professional mastering standards
- **Numerical Precision**: Consistent results across different architectures
- **Error Handling**: Robust recovery from all failure scenarios
- **Memory Safety**: No memory leaks in extended use

```bash
# Run the test suite
python -m pytest tests/ -v

# Run performance benchmarks
python -m pytest tests/performance/ -v

# Run cross-platform validation
python -m pytest tests/platform/ -v
```

---

## 🙏 Credits & Acknowledgments

### Based on Matchering 2.0
This project builds upon the excellent **[Matchering 2.0](https://github.com/sergree/matchering)** by **Sergey Grishakov** and contributors. We extend our sincere gratitude for creating the foundational algorithms and concepts that make real-time mastering possible.

**Original Matchering 2.0 Features:**
- Audio matching and mastering algorithms
- RMS, frequency response, peak amplitude, and stereo width matching
- Professional-grade brickwall limiter (Hyrax)
- Comprehensive audio processing pipeline

### Matchering Player Innovations
Building on this solid foundation, **Matchering Player** adds:
- **Real-time processing** with live parameter adjustment
- **Interactive GUI interfaces** for immediate feedback
- **Visual audio analysis** and processing statistics
- **Performance optimization** for real-time use
- **Cross-platform compatibility** testing
- **Comprehensive test suite** for production reliability

### Open Source Community
Special thanks to the open source audio community and the contributors to:
- **NumPy & SciPy**: For numerical and signal processing capabilities
- **SoundFile**: For reliable audio file I/O
- **Tkinter**: For cross-platform GUI framework
- **PyTest**: For comprehensive testing infrastructure

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

### License Compatibility
- **GPL v3**: Ensures open source availability and community contributions
- **Compatible with Matchering 2.0**: Maintains the same open source commitment
- **Commercial Use**: Permitted under GPL v3 terms
- **Distribution**: Source code must be provided with distributions

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Development
- **Bug Reports**: Open issues for any problems you encounter
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit pull requests with improvements
- **Testing**: Help test on different platforms and configurations

### Community
- **Documentation**: Improve guides and tutorials
- **Examples**: Share interesting use cases and workflows
- **Feedback**: Let us know how you're using Matchering Player
- **Tutorials**: Create video tutorials or blog posts

### Getting Started with Development
```bash
# Fork the repository and clone your fork
git clone https://github.com/your-username/matchering-player.git

# Create a development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests to ensure everything works
python -m pytest tests/ -v

# Make your changes and submit a pull request!
```

---

## 🌟 Support

### Community Support
- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and community interaction
- **Wiki**: Community-maintained documentation and examples

### Professional Support
For commercial support, custom development, or consulting services, please contact the development team.

---

## 🔮 Future Development

While Matchering Player is production-ready, we have exciting plans for the future:

### Planned Features
- **VST/AU Plugin**: Native DAW integration
- **Advanced Visualization**: 3D spectral analysis and more
- **Batch Processing GUI**: Desktop app for multiple file processing
- **Cloud Integration**: Remote processing capabilities
- **Mobile Apps**: iOS and Android versions

### Community Requests
We're always listening to the community. The most requested features will be prioritized in future releases.

---

**Ready to experience real-time mastering?**

```bash
python modern_gui.py
```

**Transform your audio workflow today with Matchering Player! 🎵**