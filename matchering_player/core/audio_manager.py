# -*- coding: utf-8 -*-

"""
Audio Manager for Matchering Player
Handles realtime audio playback with PyAudio integration
"""

import numpy as np
import threading
import time
import queue
from typing import Optional, Callable, Dict, Any
from enum import Enum
import logging

# Try to import PyAudio
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

from .config import PlayerConfig
from ..dsp import RealtimeProcessor, CircularBuffer
from ..utils.file_loader import AudioFileLoader, AudioFileInfo

logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Playback states"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class AudioManager:
    """
    Audio Manager for realtime playback with DSP processing
    Handles file loading, PyAudio integration, and realtime processing
    """
    
    def __init__(self, config: PlayerConfig):
        self.config = config
        
        # Check PyAudio availability
        if not HAS_PYAUDIO:
            raise RuntimeError("PyAudio not available. Install with: pip install pyaudio")
        
        # Audio components
        self.pyaudio_instance = pyaudio.PyAudio()
        self.audio_stream: Optional[pyaudio.Stream] = None
        self.file_loader = AudioFileLoader(config.sample_rate, 2)  # Always stereo
        self.dsp_processor = RealtimeProcessor(config)
        
        # Audio data
        self.audio_data: Optional[np.ndarray] = None
        self.current_file_info: Optional[AudioFileInfo] = None
        
        # Playback state
        self.state = PlaybackState.STOPPED
        self.current_position = 0  # Current position in samples
        self.total_samples = 0
        
        # Threading
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.state_lock = threading.Lock()
        
        # Audio buffers
        self.playback_buffer = CircularBuffer(
            size=config.buffer_size_samples * 8,  # 8x buffer for stability
            channels=2
        )
        
        # Callbacks
        self.position_callback: Optional[Callable[[float], None]] = None
        self.state_callback: Optional[Callable[[PlaybackState], None]] = None
        
        logger.info("🎵 AudioManager initialized")
        logger.info(f"   PyAudio version: {pyaudio.__version__}")
        logger.info(f"   Buffer size: {config.buffer_size_samples} samples")
        logger.info(f"   Sample rate: {config.sample_rate}Hz")
    
    def __del__(self):
        """Clean up resources"""
        self.cleanup()
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop()
        if self.audio_stream:
            if not self.audio_stream.is_stopped():
                self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
    
    def get_audio_devices(self) -> Dict[str, list]:
        """Get available audio devices"""
        devices = {'input': [], 'output': []}
        
        for i in range(self.pyaudio_instance.get_device_count()):
            device_info = self.pyaudio_instance.get_device_info_by_index(i)
            device_data = {
                'index': i,
                'name': device_info['name'],
                'channels': device_info['maxOutputChannels'],
                'sample_rate': device_info['defaultSampleRate'],
            }
            
            if device_info['maxOutputChannels'] > 0:
                devices['output'].append(device_data)
            if device_info['maxInputChannels'] > 0:
                devices['input'].append(device_data)
        
        return devices
    
    def load_file(self, file_path: str) -> bool:
        """
        Load an audio file for playback
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.state_lock:
                self._set_state(PlaybackState.LOADING)
                
                # Stop any current playback
                self._stop_playback()
                
                # Get file info first
                self.current_file_info = self.file_loader.get_file_info(file_path)
                logger.info(f"📁 Loading file: {self.current_file_info}")
                
                # Load audio data
                self.audio_data, sample_rate = self.file_loader.load_audio_file(file_path)
                self.total_samples = len(self.audio_data)
                self.current_position = 0
                
                # Reset DSP processor
                self.dsp_processor.reset_all_effects()
                
                logger.info(f"✅ File loaded: {self.total_samples} samples "
                           f"({self.total_samples / sample_rate:.1f} seconds)")
                
                self._set_state(PlaybackState.STOPPED)
                return True
                
        except Exception as e:
            logger.error(f"❌ Error loading file {file_path}: {e}")
            self._set_state(PlaybackState.ERROR)
            return False
    
    def play(self) -> bool:
        """Start playback"""
        try:
            with self.state_lock:
                if self.audio_data is None:
                    logger.warning("⚠️  No audio file loaded")
                    return False
                
                if self.state == PlaybackState.PLAYING:
                    logger.info("▶️  Already playing")
                    return True
                
                # Initialize PyAudio stream if needed
                if not self._init_audio_stream():
                    return False
                
                # Start DSP processing
                self.dsp_processor.start_processing()
                
                # Start playback thread
                self.stop_event.clear()
                self.playback_thread = threading.Thread(
                    target=self._playback_loop,
                    daemon=True,
                    name="MatcheringPlayer-Playback"
                )
                self.playback_thread.start()
                
                # Start audio stream
                if not self.audio_stream.is_active():
                    self.audio_stream.start_stream()
                
                self._set_state(PlaybackState.PLAYING)
                logger.info("▶️  Playback started")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error starting playback: {e}")
            self._set_state(PlaybackState.ERROR)
            return False
    
    def pause(self) -> bool:
        """Pause playback"""
        try:
            with self.state_lock:
                if self.state != PlaybackState.PLAYING:
                    return False
                
                if self.audio_stream and self.audio_stream.is_active():
                    self.audio_stream.stop_stream()
                
                self._set_state(PlaybackState.PAUSED)
                logger.info("⏸️  Playback paused")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error pausing playback: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop playback"""
        try:
            with self.state_lock:
                self._stop_playback()
                self.current_position = 0
                self._set_state(PlaybackState.STOPPED)
                logger.info("⏹️  Playback stopped")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error stopping playback: {e}")
            return False
    
    def seek(self, position_seconds: float) -> bool:
        """Seek to position in seconds"""
        try:
            if self.audio_data is None:
                return False
            
            target_sample = int(position_seconds * self.config.sample_rate)
            target_sample = max(0, min(target_sample, self.total_samples))
            
            with self.state_lock:
                self.current_position = target_sample
                
                # Clear playback buffer
                self.playback_buffer = CircularBuffer(
                    size=self.config.buffer_size_samples * 8,
                    channels=2
                )
                
                logger.info(f"⏩ Seeked to {position_seconds:.1f}s (sample {target_sample})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error seeking: {e}")
            return False
    
    def _stop_playback(self):
        """Internal stop playback"""
        # Signal stop to playback thread
        if self.playback_thread and self.playback_thread.is_alive():
            self.stop_event.set()
            self.playback_thread.join(timeout=1.0)
        
        # Stop audio stream
        if self.audio_stream and self.audio_stream.is_active():
            self.audio_stream.stop_stream()
        
        # Stop DSP processing
        self.dsp_processor.stop_processing()
    
    def _init_audio_stream(self) -> bool:
        """Initialize PyAudio stream"""
        try:
            if self.audio_stream:
                return True
            
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=2,
                rate=self.config.sample_rate,
                output=True,
                frames_per_buffer=self.config.buffer_size_samples,
                callback=self._audio_callback,
                stream_callback=None  # We'll use the callback
            )
            
            logger.info("🎧 Audio stream initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize audio stream: {e}")
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for audio output"""
        try:
            # Read processed audio from buffer
            output_data = self.playback_buffer.read(frame_count)
            
            if output_data is None:
                # No data available - output silence
                output_data = np.zeros((frame_count, 2), dtype=np.float32)
            
            # Convert to bytes for PyAudio
            output_bytes = output_data.astype(np.float32).tobytes()
            
            return (output_bytes, pyaudio.paContinue)
            
        except Exception as e:
            logger.error(f"❌ Error in audio callback: {e}")
            return (np.zeros((frame_count, 2), dtype=np.float32).tobytes(), pyaudio.paComplete)
    
    def _playback_loop(self):
        """Main playback loop (runs in separate thread)"""
        logger.info("🔄 Playback thread started")
        
        chunk_size = self.config.buffer_size_samples
        
        try:
            while not self.stop_event.is_set():
                # Check if we have audio data
                if self.audio_data is None or self.current_position >= self.total_samples:
                    # End of file or no data
                    break
                
                # Calculate how much data we can read
                remaining_samples = self.total_samples - self.current_position
                samples_to_read = min(chunk_size, remaining_samples)
                
                if samples_to_read <= 0:
                    break
                
                # Get next chunk of audio
                end_position = self.current_position + samples_to_read
                audio_chunk = self.audio_data[self.current_position:end_position]
                
                # Pad if needed (shouldn't normally happen)
                if len(audio_chunk) < chunk_size:
                    padding = np.zeros((chunk_size - len(audio_chunk), 2), dtype=np.float32)
                    audio_chunk = np.vstack([audio_chunk, padding])
                
                # Process through DSP
                processed_chunk = self.dsp_processor.process_audio_chunk(audio_chunk)
                
                # Add to playback buffer (this will block if buffer is full)
                self.playback_buffer.write(processed_chunk)
                
                # Update position
                with self.state_lock:
                    self.current_position = end_position
                    
                    # Notify position callback
                    if self.position_callback:
                        position_seconds = self.current_position / self.config.sample_rate
                        self.position_callback(position_seconds)
                
                # Small sleep to prevent busy waiting
                time.sleep(0.001)  # 1ms
                
        except Exception as e:
            logger.error(f"❌ Error in playback loop: {e}")
            self._set_state(PlaybackState.ERROR)
        
        # End of playback
        if not self.stop_event.is_set():
            logger.info("🎵 Playback finished")
            self._set_state(PlaybackState.STOPPED)
        
        logger.info("🔄 Playback thread finished")
    
    def _set_state(self, new_state: PlaybackState):
        """Set playback state and notify callback"""
        if self.state != new_state:
            self.state = new_state
            if self.state_callback:
                self.state_callback(new_state)
            logger.debug(f"🎛️  State changed to: {new_state.value}")
    
    def load_reference_track(self, reference_path: str) -> bool:
        """Load reference track for DSP processing"""
        try:
            success = self.dsp_processor.load_reference_track(reference_path)
            if success:
                logger.info(f"📎 Reference track loaded: {reference_path}")
            return success
        except Exception as e:
            logger.error(f"❌ Error loading reference: {e}")
            return False
    
    def set_effect_enabled(self, effect_name: str, enabled: bool):
        """Enable/disable DSP effects"""
        self.dsp_processor.set_effect_enabled(effect_name, enabled)
    
    def set_effect_parameter(self, effect_name: str, parameter: str, value: Any):
        """Set DSP effect parameters"""
        self.dsp_processor.set_effect_parameter(effect_name, parameter, value)
    
    def get_playback_info(self) -> Dict[str, Any]:
        """Get current playback information"""
        info = {
            'state': self.state.value,
            'position_seconds': self.current_position / self.config.sample_rate if self.total_samples > 0 else 0,
            'duration_seconds': self.total_samples / self.config.sample_rate if self.total_samples > 0 else 0,
            'position_samples': self.current_position,
            'total_samples': self.total_samples,
        }
        
        # Add file info
        if self.current_file_info:
            info.update({
                'filename': self.current_file_info.filename,
                'file_format': self.current_file_info.format_info,
                'original_sample_rate': self.current_file_info.sample_rate,
                'original_channels': self.current_file_info.channels,
            })
        
        # Add DSP stats
        if self.dsp_processor:
            info['dsp'] = self.dsp_processor.get_processing_stats()
            info['dsp_health'] = self.dsp_processor.get_health_status()
        
        return info
    
    def set_position_callback(self, callback: Callable[[float], None]):
        """Set callback for position updates"""
        self.position_callback = callback
    
    def set_state_callback(self, callback: Callable[[PlaybackState], None]):
        """Set callback for state changes"""
        self.state_callback = callback
