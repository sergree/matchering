"""
Audio device management module.
"""

from typing import Dict, List, Optional, Tuple
import threading
from dataclasses import dataclass
import numpy as np
try:
    import sounddevice as sd
    HAS_SD = True
except Exception:
    sd = None  # type: ignore
    HAS_SD = False
from .engine import AudioBuffer, AudioConfig

@dataclass
class DeviceInfo:
    """Audio device information."""
    id: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    supported_sample_rates: List[float]
    input_latency: Tuple[float, float]  # (low, high)
    output_latency: Tuple[float, float]  # (low, high)
    is_default_input: bool
    is_default_output: bool

class DeviceManager:
    """Audio device management."""
    
    def __init__(self):
        """Initialize device manager."""
        self._lock = threading.RLock()
        self._current_device: Optional[DeviceInfo] = None
        self._stream: Optional[sd.OutputStream] = None
        self._callback = None
        self._buffer = None
        
        # Initialize PortAudio if available
        try:
            if HAS_SD:
                sd.default.reset()
                test_buffer = np.zeros((1024, 2), dtype=np.float32)  # Test buffer
                test_stream = sd.OutputStream(
                    channels=2,
                    samplerate=44100,
                    dtype=np.float32
                )
                test_stream.start()
                test_stream.stop()
                test_stream.close()
                self._has_audio = True
            else:
                self._has_audio = False
        except Exception:
            print("Warning: Could not initialize PortAudio")
            self._has_audio = False
        
    @property
    def current_device(self) -> Optional[DeviceInfo]:
        """Currently selected audio device."""
        return self._current_device
        
    def get_devices(self) -> List[DeviceInfo]:
        """Get list of available audio devices.
        
        Returns:
            List of DeviceInfo objects
        """
        devices = []
        if not HAS_SD or not self._has_audio:
            # Fallback virtual device for environments without PortAudio or failed initialization
            devices.append(DeviceInfo(
                id=0,
                name="Virtual Device",
                max_input_channels=0,
                max_output_channels=2,
                default_sample_rate=44100.0,
                supported_sample_rates=[44100, 48000],
                input_latency=(0.0, 0.0),
                output_latency=(0.02, 0.05),
                is_default_input=False,
                is_default_output=True
            ))
            return devices
        
        default_input = sd.default.device[0]
        default_output = sd.default.device[1]
        
        for idx, device in enumerate(sd.query_devices()):
            devices.append(DeviceInfo(
                id=idx,
                name=device['name'],
                max_input_channels=device['max_input_channels'],
                max_output_channels=device['max_output_channels'],
                default_sample_rate=device['default_samplerate'],
                supported_sample_rates=self._get_supported_rates(device),
                input_latency=(device['default_low_input_latency'],
                             device['default_high_input_latency']),
                output_latency=(device['default_low_output_latency'],
                              device['default_high_output_latency']),
                is_default_input=(idx == default_input),
                is_default_output=(idx == default_output)
            ))
            
        return devices
        
    def get_default_device(self) -> Optional[DeviceInfo]:
        """Get default output device.
        
        Returns:
            Default DeviceInfo or None if no devices available
        """
        devices = self.get_devices()
        for device in devices:
            if device.is_default_output:
                return device
        return None if not devices else devices[0]
        
    def _get_supported_rates(self, device: Dict) -> List[float]:
        """Get supported sample rates for device.
        
        Args:
            device: Device dictionary from sounddevice
            
        Returns:
            List of supported sample rates
        """
        try:
            return sorted([
                rate for rate in [
                    8000, 11025, 16000, 22050, 32000,
                    44100, 48000, 88200, 96000, 192000
                ]
                if self._check_rate_support(device, rate)
            ])
        except Exception:
            # Return common rates if detection fails
            return [44100, 48000]
            
    def _check_rate_support(self, device: Dict, rate: float) -> bool:
        """Check if sample rate is supported by device.
        
        Args:
            device: Device dictionary from sounddevice
            rate: Sample rate to check
            
        Returns:
            True if rate is supported
        """
        if not HAS_SD:
            return rate in (44100, 48000)
        try:
            sd.check_output_settings(
                device=device['name'],
                channels=min(2, device['max_output_channels']),
                samplerate=rate
            )
            return True
        except Exception:
            return False
            
    def open_output_stream(self, config: AudioConfig,
                          device: Optional[DeviceInfo] = None) -> None:
        """Open audio output stream.
        
        Args:
            config: Audio configuration
            device: Optional device to use (default: system default)
        """
        with self._lock:
            # Close existing stream
            self.close()
            
            # Use default device if none specified
            if device is None:
                device = self.get_default_device()
                if device is None:
                    # If no real devices, fall back to virtual device
                    devices = self.get_devices()
                    if devices:
                        device = devices[0]
                    else:
                        raise RuntimeError("No audio output devices available")
                    
            # Create circular buffer for audio data
            buffer_size = int(config.sample_rate * 0.5)  # 500ms buffer
            self._buffer = AudioBuffer(buffer_size, config.channels, config.format)
            
            # Setup callback
            def callback(outdata: np.ndarray, frames: int,
                        time: object, status: sd.CallbackFlags) -> None:
                if status:
                    print(f"Audio callback status: {status}")
                
                # Get data from buffer
                data = self._buffer.read(frames)
                if len(data) < frames:
                    # Buffer underrun, pad with silence
                    outdata[:len(data)] = data
                    outdata[len(data):] = 0
                else:
                    outdata[:] = data
            
            # Open stream
            if not HAS_SD or not self._has_audio:
                # In test/headless environments, simulate an active stream
                self._current_device = device
                self._stream = None  # No real stream
                return
            
            self._stream = sd.OutputStream(
                device=device.id,
                channels=config.channels,
                samplerate=config.sample_rate,
                dtype=config.format,
                callback=callback,
                finished_callback=None
            )
            
            self._current_device = device
            self._stream.start()
            
    def close(self) -> None:
        """Close audio output stream."""
        with self._lock:
            if self._stream is not None:
                if HAS_SD:
                    self._stream.stop()
                    self._stream.close()
                self._stream = None
            self._buffer = None
            self._current_device = None
            
    def write(self, data: np.ndarray) -> int:
        """Write audio data to output stream.
        
        Args:
            data: Audio data to write
            
        Returns:
            Number of frames written
        """
        with self._lock:
            if self._buffer is None:
                return 0
            return self._buffer.write(data)
            
    def get_output_latency(self) -> float:
        """Get current output latency in seconds.
        
        Returns:
            Output latency in seconds
        """
        with self._lock:
            if self._stream is None or not HAS_SD:
                return 0.0
            return self._stream.latency
            
    def get_buffer_size(self) -> int:
        """Get current buffer size in frames.
        
        Returns:
            Buffer size in frames
        """
        with self._lock:
            if self._buffer is None:
                return 0
            return len(self._buffer.data)