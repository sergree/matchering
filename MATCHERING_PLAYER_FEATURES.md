# 🎵 Matchering Player - Real-time Audio Mastering

## What's New in Matchering 2.0

**Matchering Player** brings real-time audio mastering capabilities to the Matchering suite, allowing you to hear reference matching applied to your audio instantly while making adjustments.

---

## 🚀 Key Features

### 🎧 **Real-time Mastering**
- **Live Processing**: Hear mastering effects applied to your audio in real-time
- **Instant Feedback**: No waiting for batch processing - hear changes immediately
- **A/B Comparison**: Switch between original and processed audio instantly
- **Professional Quality**: Same algorithms as batch processing, optimized for real-time use

### 🎛️ **Interactive Controls**
- **Level Matching**: Adjust target vs reference RMS levels on the fly
- **Frequency Response**: Real-time EQ matching with visual feedback
- **Stereo Width**: Control stereo imaging and spatial characteristics
- **Auto-mastering**: Let the algorithm handle all processing automatically
- **Bypass/Enable**: Toggle individual effects to hear their impact

### 📊 **Visual Feedback**
- **Real-time Analysis**: See audio levels, frequency response, and processing statistics
- **Performance Metrics**: Monitor processing speed and real-time factors
- **Visual EQ**: Frequency response curves for target, reference, and result
- **Level Meters**: RMS and peak level monitoring with professional accuracy

### 🎨 **Multiple Interfaces**
Choose the interface that works best for your workflow:

#### **Modern GUI** (`python modern_gui.py`)
- Advanced controls with visual feedback
- Real-time audio analysis and visualization
- Professional-grade interface for detailed work
- Full feature set with customizable parameters

#### **Simple Launcher** (`python launch_gui.py`)
- Quick access to essential features
- Streamlined interface for fast workflow
- Perfect for A/B reference comparisons
- Minimal resource usage

#### **Basic Interface** (`python gui_demo.py`)
- Lightweight option for basic mastering
- Essential controls without complexity
- Great for learning and experimentation
- Compatible with older systems

---

## ⚡ Performance

### **Speed & Efficiency**
- **25-111x Real-time**: Process audio much faster than playback speed
- **Low Latency**: Minimal delay for real-time parameter changes
- **Memory Efficient**: Optimized for long sessions with large files
- **CPU Optimized**: Multi-core processing for maximum performance

### **File Support**
- **Multiple Formats**: WAV, FLAC, MP3 (with FFmpeg), and more
- **High Resolution**: Up to 96kHz sample rates supported
- **Large Files**: Handle 2+ minute tracks efficiently
- **Batch Processing**: Process multiple files with consistent quality

### **Cross-platform**
- **Windows**: Full compatibility with Windows 10/11
- **macOS**: Native support for macOS 10.14+
- **Linux**: Complete Linux distribution support
- **Consistent Performance**: Same features and speed across all platforms

---

## 🎯 Use Cases

### **Music Producers**
- **Reference Matching**: Make your tracks sound like your favorite artists
- **Album Consistency**: Ensure all tracks have the same sonic character
- **A/B Testing**: Compare different mastering approaches in real-time
- **Creative Exploration**: Experiment with different reference tracks

### **Audio Engineers**
- **Client Previews**: Show clients mastering results instantly
- **Quality Control**: Verify mastering decisions before final processing
- **Workflow Efficiency**: Speed up the mastering process with real-time feedback
- **Educational Tool**: Demonstrate mastering concepts with live examples

### **Content Creators**
- **Podcast Mastering**: Match your podcast to professional standards
- **Video Audio**: Ensure consistent audio across video content
- **Streaming Optimization**: Optimize audio for different streaming platforms
- **Quick Masters**: Fast turnaround for time-sensitive content

---

## 🛠️ Technical Specifications

### **System Requirements**
- **RAM**: 4GB minimum (8GB recommended for large files)
- **CPU**: Multi-core processor recommended for real-time processing
- **Storage**: 100MB for installation + space for audio files
- **Audio Interface**: Any compatible audio device or built-in audio

### **Supported Formats**
- **Input**: WAV, FLAC, MP3 (with FFmpeg), AIFF, and more
- **Output**: WAV (16/24-bit), FLAC, preview formats
- **Sample Rates**: 22.05kHz to 96kHz supported
- **Channels**: Mono and stereo processing

### **Processing Features**
- **RMS Level Matching**: Match perceived loudness between tracks
- **Frequency Response Matching**: EQ matching with spectral analysis
- **Peak Limiting**: Professional brickwall limiter to prevent clipping
- **Stereo Width Control**: Adjust stereo imaging and spatial characteristics
- **Dynamic Range**: Preserve musical dynamics while matching levels

---

## 📚 Getting Started

### **Quick Start**
1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Launch Player**: `python modern_gui.py`
3. **Load Target**: Select the audio file you want to master
4. **Load Reference**: Choose your reference track
5. **Play & Adjust**: Listen while adjusting parameters in real-time

### **Best Practices**
- **Use High-Quality References**: Choose professionally mastered tracks
- **Monitor Levels**: Keep an eye on peak and RMS meters
- **A/B Compare**: Regularly switch between original and processed
- **Save Settings**: Export your preferred configurations for reuse

### **Tips for Best Results**
- **Match Genres**: Use reference tracks from the same musical genre
- **Consider Dynamics**: Don't over-compress dynamic music
- **Room Acoustics**: Use good monitoring in a treated space
- **Take Breaks**: Fresh ears are critical for good mastering decisions

---

## 🔧 Advanced Features

### **Real-time Parameter Smoothing**
- Smooth transitions when adjusting parameters
- No audio artifacts during parameter changes
- Professional-grade interpolation algorithms
- Configurable smoothing rates

### **Processing Statistics**
- Real-time factor monitoring (how fast processing is running)
- CPU usage and memory consumption
- Audio analysis metrics (RMS, peak, frequency content)
- Processing quality indicators

### **Customizable Settings**
- Adjustable buffer sizes for different latency requirements
- Configurable processing quality vs speed trade-offs
- Custom output formats and bit depths
- User-defined keyboard shortcuts

---

## 🎉 Why Matchering Player?

### **Professional Quality**
- **Same Algorithms**: Uses identical processing to batch Matchering
- **Studio Grade**: Meets professional mastering standards
- **No Compromise**: Real-time processing without quality loss
- **Industry Proven**: Based on established mastering techniques

### **Workflow Innovation**
- **Immediate Feedback**: Hear results as you make adjustments
- **Creative Flow**: Maintain musical inspiration with instant results
- **Efficiency**: Reduce mastering time with real-time decisions
- **Learning Tool**: Understand mastering through interactive experimentation

### **Open Source Advantage**
- **Transparent**: All algorithms are open and auditable
- **Customizable**: Modify and extend for your specific needs
- **Community Driven**: Improvements benefit everyone
- **Cost Effective**: Professional mastering tools without the price tag

---

**Ready to transform your audio workflow? Launch Matchering Player and experience real-time mastering today!**

```bash
python modern_gui.py
```