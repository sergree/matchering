"""
Audio player implementation.
"""

from typing import Optional, Callable, List
import threading
from enum import Enum
import time
import numpy as np
import soundfile as sf
from pathlib import Path
from .device import DeviceManager, DeviceInfo
from .engine import AudioEngine, AudioConfig, AudioProcessor

class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

class Player:
    """Audio player implementation."""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize player.
        
        Args:
            config: Optional audio configuration
        """
        self.config = config or AudioConfig()
        self.device_manager = DeviceManager()
        self.engine = AudioEngine(self.config)
        
        self._lock = threading.RLock()
        self._state = PlaybackState.STOPPED
        self._position = 0
        self._duration = 0
        self._audio_data: Optional[np.ndarray] = None
        self._audio_info: Optional[sf.info] = None
        
        # Callbacks
        self._state_callback: Optional[Callable[[PlaybackState], None]] = None
        self._position_callback: Optional[Callable[[float, float], None]] = None
        
        # Start update thread
        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop)
        self._update_thread.daemon = True
        self._update_thread.start()
        
    def __del__(self):
        """Cleanup resources."""
        self.stop()
        self._running = False
        if self._update_thread.is_alive():
            self._update_thread.join()
        
    @property
    def state(self) -> PlaybackState:
        """Current playback state."""
        return self._state
        
    @property
    def position(self) -> float:
        """Current playback position in seconds."""
        return self._position
        
    @property
    def duration(self) -> float:
        """Audio duration in seconds."""
        return self._duration
        
    def load_file(self, filepath: str) -> bool:
        """Load audio file.
        
        Args:
            filepath: Path to audio file
            
        Returns:
            True if file was loaded successfully
        """
        with self._lock:
            try:
                self._set_state(PlaybackState.LOADING)
                
                # Stop current playback
                self.stop()
                
                # Load audio file
                audio_data, sample_rate = sf.read(filepath, dtype=np.float32)
                audio_info = sf.info(filepath)
                
                # Convert to stereo if needed
                if audio_data.ndim == 1:
                    audio_data = np.column_stack((audio_data, audio_data))
                elif audio_data.ndim == 2 and audio_data.shape[1] > 2:
                    audio_data = audio_data[:, :2]
                
                # Store audio data
                self._audio_data = audio_data
                self._audio_info = audio_info
                self._duration = len(audio_data) / audio_info.samplerate
                self._position = 0
                
                # Update config if needed
                if audio_info.samplerate != self.config.sample_rate:
                    self.config.sample_rate = audio_info.samplerate
                    self.engine = AudioEngine(self.config)
                
                self._set_state(PlaybackState.STOPPED)
                return True
                
            except Exception as e:
                print(f"Error loading audio file: {e}")
                self._set_state(PlaybackState.ERROR)
                return False
                
    def play(self):
        """Start or resume playback."""
        with self._lock:
            if self._state in (PlaybackState.STOPPED, PlaybackState.PAUSED):
                if self._audio_data is None:
                    return
                    
                # Open output stream if needed
                if self.device_manager.current_device is None:
                    self.device_manager.open_output_stream(self.config)
                    
                self._set_state(PlaybackState.PLAYING)
                
    def pause(self):
        """Pause playback."""
        with self._lock:
            if self._state == PlaybackState.PLAYING:
                self._set_state(PlaybackState.PAUSED)
                
    def stop(self):
        """Stop playback."""
        with self._lock:
            if self._state != PlaybackState.STOPPED:
                self._set_state(PlaybackState.STOPPED)
                self._position = 0
                self.device_manager.close()
                
    def seek(self, position: float):
        """Seek to position.
        
        Args:
            position: Position in seconds
        """
        with self._lock:
            if self._audio_data is None:
                return
                
            # Clamp position
            position = max(0, min(position, self._duration))
            
            # Convert to samples
            sample_pos = int(position * self._audio_info.samplerate)
            
            # Update position
            self._position = position
            
            # Notify position change
            if self._position_callback:
                self._position_callback(position, self._duration)
                
    def add_processor(self, processor: AudioProcessor):
        """Add audio processor to chain.
        
        Args:
            processor: Audio processor instance
        """
        self.engine.add_processor(processor)
        
    def remove_processor(self, processor: AudioProcessor):
        """Remove audio processor from chain.
        
        Args:
            processor: Audio processor instance
        """
        self.engine.remove_processor(processor)
        
    def set_device(self, device: DeviceInfo):
        """Set output device.
        
        Args:
            device: Device to use
        """
        with self._lock:
            was_playing = self._state == PlaybackState.PLAYING
            
            # Stop current playback
            self.stop()
            
            # Open new device
            self.device_manager.open_output_stream(self.config, device)
            
            # Resume playback if needed
            if was_playing:
                self.play()
                
    def set_state_callback(self, callback: Optional[Callable[[PlaybackState], None]]):
        """Set state change callback.
        
        Args:
            callback: Callback function
        """
        self._state_callback = callback
        
    def set_position_callback(self, callback: Optional[Callable[[float, float], None]]):
        """Set position change callback.
        
        Args:
            callback: Callback function
        """
        self._position_callback = callback
        
    def _set_state(self, state: PlaybackState):
        """Set playback state.
        
        Args:
            state: New state
        """
        self._state = state
        if self._state_callback:
            self._state_callback(state)
            
    def _update_loop(self):
        """Update loop for playback."""
        buffer_size = self.config.buffer_size
        update_interval = buffer_size / self.config.sample_rate
        
        while self._running:
            with self._lock:
                if self._state == PlaybackState.PLAYING:
                    if self._audio_data is not None:
                        # Calculate current position in samples
                        current_sample = int(self._position * self._audio_info.samplerate)
                        
                        # Get next chunk of audio
                        if current_sample + buffer_size <= len(self._audio_data):
                            chunk = self._audio_data[current_sample:current_sample + buffer_size]
                            
                            # Process audio
                            chunk = self.engine.process_block(chunk)
                            
                            # Write to output
                            self.device_manager.write(chunk)
                            
                            # Update position
                            self._position += update_interval
                            
                            # Notify position change
                            if self._position_callback:
                                self._position_callback(self._position, self._duration)
                        else:
                            # End of file
                            self.stop()
                            
            # Sleep for half the buffer duration
            time.sleep(update_interval * 0.5)