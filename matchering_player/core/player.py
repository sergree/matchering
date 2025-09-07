# -*- coding: utf-8 -*-

"""
Main Matchering Player class
Now with full audio playback functionality!
"""

from typing import Optional, Callable, Dict, Any
from .config import PlayerConfig
from .audio_manager import AudioManager, PlaybackState


class MatcheringPlayer:
    """
    Main Matchering Player class
    Complete audio player with realtime DSP processing
    """
    
    def __init__(self, config: PlayerConfig = None):
        self.config = config or PlayerConfig()
        
        # Initialize audio manager
        try:
            self.audio_manager = AudioManager(self.config)
            print(f"📻 MatcheringPlayer initialized successfully!")
            print(f"    Buffer: {self.config.buffer_size_ms}ms")
            print(f"    Sample rate: {self.config.sample_rate}Hz")
            print(f"    Level matching: {'✅ Enabled' if self.config.enable_level_matching else '❌ Disabled'}")
        except Exception as e:
            print(f"❌ Failed to initialize MatcheringPlayer: {e}")
            raise
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'audio_manager'):
            self.audio_manager.cleanup()
    
    def load_file(self, file_path: str) -> bool:
        """Load audio file for playback"""
        return self.audio_manager.load_file(file_path)
    
    def play(self) -> bool:
        """Start playback"""
        return self.audio_manager.play()
    
    def pause(self) -> bool:
        """Pause playback"""
        return self.audio_manager.pause()
    
    def stop(self) -> bool:
        """Stop playback"""
        return self.audio_manager.stop()
    
    def seek(self, position_seconds: float) -> bool:
        """Seek to position in seconds"""
        return self.audio_manager.seek(position_seconds)
    
    def load_reference_track(self, reference_path: str) -> bool:
        """Load reference track for DSP matching"""
        return self.audio_manager.load_reference_track(reference_path)
    
    def set_effect_enabled(self, effect_name: str, enabled: bool):
        """Enable/disable DSP effects"""
        self.audio_manager.set_effect_enabled(effect_name, enabled)
    
    def set_effect_parameter(self, effect_name: str, parameter: str, value: Any):
        """Set DSP effect parameters"""
        self.audio_manager.set_effect_parameter(effect_name, parameter, value)
    
    def get_playback_info(self) -> Dict[str, Any]:
        """Get current playback information"""
        return self.audio_manager.get_playback_info()
    
    def get_state(self) -> PlaybackState:
        """Get current playback state"""
        return self.audio_manager.state
    
    def set_position_callback(self, callback: Callable[[float], None]):
        """Set callback for position updates during playback"""
        self.audio_manager.set_position_callback(callback)
    
    def set_state_callback(self, callback: Callable[[PlaybackState], None]):
        """Set callback for playback state changes"""
        self.audio_manager.set_state_callback(callback)
    
    def get_audio_devices(self) -> Dict[str, list]:
        """Get available audio output devices"""
        return self.audio_manager.get_audio_devices()
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get supported audio file formats"""
        return self.audio_manager.file_loader.get_supported_formats()
