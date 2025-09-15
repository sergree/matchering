#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matchering Player Modern GUI - Integrated Version
Beautiful CustomTkinter interface with REAL audio processing
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tempfile
import os
import math
from pathlib import Path
import threading
import time

try:
    import soundfile as sf
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

# Import the real Matchering Player
try:
    from matchering_player.core.player import MatcheringPlayer
    from matchering_player.core.config import PlayerConfig
    from matchering_player.core.audio_manager import PlaybackState
    HAS_REAL_PLAYER = True
    print("✅ Real MatcheringPlayer available")
except ImportError as e:
    print(f"⚠️  Real MatcheringPlayer not available: {e}")
    HAS_REAL_PLAYER = False

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class MockMatcheringPlayer:
    """Fallback mock player when real player is not available"""

    def __init__(self):
        self.current_file = None
        self.reference_file = None
        self.duration = 120
        self.position = 0
        self.state = "stopped"
        self.processing_active = False
        self.volume = 0.8
        self._callbacks = []

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def _notify_callbacks(self):
        for callback in self._callbacks:
            try:
                callback(self.get_playback_info())
            except:
                pass

    def load_file(self, filename):
        self.current_file = filename
        self.duration = 120
        self._notify_callbacks()
        return True

    def load_reference_track(self, filename):
        self.reference_file = filename
        self.processing_active = True
        self._notify_callbacks()
        return True

    def play(self):
        self.state = "playing"
        self._notify_callbacks()
        return True

    def pause(self):
        self.state = "paused"
        self._notify_callbacks()
        return True

    def stop(self):
        self.state = "stopped"
        self.position = 0
        self._notify_callbacks()
        return True

    def seek(self, position):
        self.position = max(0, min(position, self.duration))
        self._notify_callbacks()
        return True

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        self._notify_callbacks()

    def get_playback_info(self):
        return {
            'state': self.state,
            'position_seconds': self.position,
            'duration_seconds': self.duration,
            'volume': self.volume,
            'filename': os.path.basename(self.current_file) if self.current_file else None,
            'dsp': {
                'processing_active': self.processing_active,
                'cpu_usage': 0.05,
                'chunks_processed': int(self.position * 44.1),
                'performance_mode': False,
                'level_matching': {
                    'status': 'active' if self.processing_active else 'inactive',
                    'reference_loaded': self.reference_file is not None,
                    'mid_gain_current': 2.5 if self.processing_active else 1.0,
                    'side_gain_current': 1.8 if self.processing_active else 1.0,
                    'target_rms_mid_db': -18.0 if self.processing_active else 0,
                    'target_rms_side_db': -24.0 if self.processing_active else 0,
                }
            }
        }

    def set_effect_enabled(self, effect, enabled):
        if effect == 'level_matching':
            self.processing_active = enabled
            self._notify_callbacks()


class RealPlayerAdapter:
    """Adapter to make real MatcheringPlayer compatible with GUI interface"""

    def __init__(self):
        try:
            # Initialize with optimal settings for GUI use
            config = PlayerConfig(
                buffer_size_ms=100,  # Low latency for responsive GUI
                sample_rate=44100,
                enable_level_matching=True,
                enable_frequency_matching=False,  # Start simple
                enable_stereo_width=False,
                enable_auto_mastering=False
            )

            self.player = MatcheringPlayer(config)
            self.current_file = None
            self.reference_file = None
            self._callbacks = []
            self._update_thread = None
            self._running = False

            print("🎵 Real MatcheringPlayer initialized for GUI")

        except Exception as e:
            print(f"❌ Failed to initialize real player: {e}")
            raise

    def __del__(self):
        """Clean up resources"""
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self._running = False
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=1.0)

    def add_callback(self, callback):
        """Add callback for state updates"""
        self._callbacks.append(callback)
        self._start_update_thread()

    def _start_update_thread(self):
        """Start the update thread if not already running"""
        if self._update_thread is None or not self._update_thread.is_alive():
            self._running = True
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()

    def _update_loop(self):
        """Update loop for real-time callbacks"""
        while self._running:
            try:
                info = self.get_playback_info()
                for callback in self._callbacks:
                    try:
                        callback(info)
                    except Exception as e:
                        print(f"Callback error: {e}")
                time.sleep(0.1)  # 10 FPS update rate
            except Exception as e:
                print(f"Update loop error: {e}")
                break

    def load_file(self, filename):
        """Load audio file"""
        try:
            success = self.player.load_file(filename)
            if success:
                self.current_file = filename
                print(f"📁 Loaded: {os.path.basename(filename)}")
            return success
        except Exception as e:
            print(f"❌ Failed to load file: {e}")
            return False

    def load_reference_track(self, filename):
        """Load reference track"""
        try:
            success = self.player.load_reference_track(filename)
            if success:
                self.reference_file = filename
                print(f"🎯 Reference loaded: {os.path.basename(filename)}")
            return success
        except Exception as e:
            print(f"❌ Failed to load reference: {e}")
            return False

    def play(self):
        """Start playback"""
        return self.player.play()

    def pause(self):
        """Pause playback"""
        return self.player.pause()

    def stop(self):
        """Stop playback"""
        return self.player.stop()

    def seek(self, position):
        """Seek to position"""
        return self.player.seek(position)

    def set_volume(self, volume):
        """Set volume (placeholder - not implemented in core player yet)"""
        # TODO: Implement volume control in core player
        pass

    def set_effect_enabled(self, effect, enabled):
        """Enable/disable effects"""
        try:
            self.player.set_effect_enabled(effect, enabled)
        except Exception as e:
            print(f"❌ Failed to set effect {effect}: {e}")

    def get_playback_info(self):
        """Get playback information with enhanced formatting for GUI"""
        try:
            info = self.player.get_playback_info()

            # Enhance the info structure for GUI compatibility
            enhanced_info = {
                'state': str(info.get('state', 'unknown')).lower(),
                'position_seconds': info.get('position_seconds', 0.0),
                'duration_seconds': info.get('duration_seconds', 0.0),
                'volume': 0.8,  # TODO: Get from actual player when implemented
                'filename': os.path.basename(self.current_file) if self.current_file else None,
                'dsp': {
                    'processing_active': info.get('level_matching', {}).get('enabled', False),
                    'cpu_usage': info.get('performance', {}).get('cpu_usage', 0.0),
                    'chunks_processed': info.get('performance', {}).get('chunks_processed', 0),
                    'performance_mode': info.get('performance', {}).get('mode') == 'performance',
                    'level_matching': {
                        'status': 'active' if info.get('level_matching', {}).get('enabled') else 'inactive',
                        'reference_loaded': self.reference_file is not None,
                        'mid_gain_current': info.get('level_matching', {}).get('current_gains', {}).get('mid', 1.0),
                        'side_gain_current': info.get('level_matching', {}).get('current_gains', {}).get('side', 1.0),
                        'target_rms_mid_db': info.get('level_matching', {}).get('target_levels', {}).get('mid_db', 0.0),
                        'target_rms_side_db': info.get('level_matching', {}).get('target_levels', {}).get('side_db', 0.0),
                    }
                }
            }

            return enhanced_info

        except Exception as e:
            print(f"❌ Failed to get playback info: {e}")
            # Return fallback info
            return {
                'state': 'error',
                'position_seconds': 0.0,
                'duration_seconds': 0.0,
                'volume': 0.8,
                'filename': None,
                'dsp': {'processing_active': False, 'cpu_usage': 0.0}
            }


class VisualizationFrame(ctk.CTkFrame):
    """Custom frame for audio visualization"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.canvas = ctk.CTkCanvas(self, height=200, bg="#212121", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.mid_gain = 1.0
        self.side_gain = 1.0
        self.active = False

    def update_levels(self, mid_gain, side_gain, active=True):
        """Update the level visualization"""
        self.mid_gain = mid_gain
        self.side_gain = side_gain
        self.active = active
        self.draw_levels()

    def draw_levels(self):
        """Draw the level meters"""
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        if not self.active:
            # Draw inactive state
            self.canvas.create_text(width//2, height//2,
                                  text="Load reference track for level visualization",
                                  fill="#666666", font=("Arial", 12))
            return

        # Convert to dB
        if HAS_AUDIO:
            mid_db = 20 * np.log10(max(self.mid_gain, 1e-6))
            side_db = 20 * np.log10(max(self.side_gain, 1e-6))
        else:
            mid_db = 8.0 + 2 * math.sin(time.time() * 2)  # Animated demo
            side_db = 5.1 + 1.5 * math.cos(time.time() * 1.5)

        # Draw level bars with gradient effect
        bar_width = (width - 60) // 2
        bar_height = height - 60

        # Normalize levels for display (-60dB to +20dB range)
        mid_norm = max(0, min(1, (mid_db + 60) / 80))
        side_norm = max(0, min(1, (side_db + 60) / 80))

        # Mid channel (left side)
        mid_bar_height = int(bar_height * mid_norm)
        self._draw_gradient_bar(20, height - 30 - mid_bar_height, bar_width, mid_bar_height,
                              "#00ff00", "#ffff00", "#ff0000")

        # Mid channel label and value
        self.canvas.create_text(20 + bar_width//2, height - 10,
                              text=f"Mid: {mid_db:.1f} dB",
                              fill="#ffffff", font=("Arial", 10, "bold"))
        self.canvas.create_text(20 + bar_width//2, 20,
                              text="MID CHANNEL",
                              fill="#00ff88", font=("Arial", 12, "bold"))

        # Side channel (right side)
        side_bar_height = int(bar_height * side_norm)
        self._draw_gradient_bar(40 + bar_width, height - 30 - side_bar_height, bar_width, side_bar_height,
                              "#00ffff", "#ffff00", "#ff0000")

        # Side channel label and value
        self.canvas.create_text(40 + bar_width + bar_width//2, height - 10,
                              text=f"Side: {side_db:.1f} dB",
                              fill="#ffffff", font=("Arial", 10, "bold"))
        self.canvas.create_text(40 + bar_width + bar_width//2, 20,
                              text="SIDE CHANNEL",
                              fill="#00ddff", font=("Arial", 12, "bold"))

    def _draw_gradient_bar(self, x, y, width, height, color_start, color_mid, color_end):
        """Draw a gradient bar"""
        if height <= 0:
            return

        # Simple gradient approximation with segments
        segments = max(1, height // 4)
        segment_height = height / segments

        for i in range(segments):
            # Calculate color based on position
            ratio = i / max(1, segments - 1)

            if ratio < 0.6:  # Green to yellow
                interp = ratio / 0.6
                color = self._interpolate_color("#00ff00", "#ffff00", interp)
            else:  # Yellow to red
                interp = (ratio - 0.6) / 0.4
                color = self._interpolate_color("#ffff00", "#ff0000", interp)

            seg_y = y + i * segment_height
            self.canvas.create_rectangle(x, seg_y, x + width, seg_y + segment_height + 1,
                                       fill=color, outline=color)

    def _interpolate_color(self, color1, color2, ratio):
        """Interpolate between two hex colors"""
        # Simple color interpolation
        c1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
        c2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]

        interpolated = [int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3)]
        return f"#{interpolated[0]:02x}{interpolated[1]:02x}{interpolated[2]:02x}"


class ModernMatcheringPlayer(ctk.CTk):
    """Modern GUI for Matchering Player with real audio processing"""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("🎵 Matchering Player - Modern Interface")
        self.geometry("1000x700")

        # Initialize player
        self.init_player()

        # GUI state
        self.seeking = False

        # Create interface
        self.create_interface()

        # Start player updates
        self.start_player_updates()

    def init_player(self):
        """Initialize the audio player"""
        if HAS_REAL_PLAYER:
            try:
                self.player = RealPlayerAdapter()
                self.player_type = "Real MatcheringPlayer"
                print("🎵 Using REAL MatcheringPlayer!")
            except Exception as e:
                print(f"⚠️  Failed to initialize real player, falling back to mock: {e}")
                self.player = MockMatcheringPlayer()
                self.player_type = "Mock Player (Demo Mode)"
        else:
            self.player = MockMatcheringPlayer()
            self.player_type = "Mock Player (Demo Mode)"

        # Add update callback
        self.player.add_callback(self._on_player_update)

    def create_interface(self):
        """Create the main interface"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=20, pady=20)

        title_label = ctk.CTkLabel(header_frame, text="🎵 Matchering Player",
                                 font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(side="left", padx=20, pady=15)

        # Player type indicator
        player_type_label = ctk.CTkLabel(header_frame, text=f"Engine: {self.player_type}",
                                       font=ctk.CTkFont(size=12),
                                       text_color="#00ff88" if HAS_REAL_PLAYER else "#ffaa00")
        player_type_label.pack(side="right", padx=20, pady=15)

        # Create tabbed interface
        self.create_tabbed_interface()

        # Status bar
        self.status_label = ctk.CTkLabel(self, text="Ready to load audio files",
                                       font=ctk.CTkFont(size=12))
        self.status_label.pack(side="bottom", pady=10)

    def create_tabbed_interface(self):
        """Create the tabbed interface"""
        # Tab selection frame
        tab_frame = ctk.CTkFrame(self)
        tab_frame.pack(fill="x", padx=20)

        self.current_tab = "player"

        # Tab buttons
        self.player_tab_btn = ctk.CTkButton(tab_frame, text="🎛️ Player",
                                          command=lambda: self.switch_tab("player"),
                                          fg_color="#1f538d", hover_color="#1e5380")
        self.player_tab_btn.pack(side="left", padx=5, pady=10)

        self.visualizer_tab_btn = ctk.CTkButton(tab_frame, text="📊 Visualizer",
                                              command=lambda: self.switch_tab("visualizer"),
                                              fg_color="#555555", hover_color="#666666")
        self.visualizer_tab_btn.pack(side="left", padx=5, pady=10)

        self.stats_tab_btn = ctk.CTkButton(tab_frame, text="📈 Statistics",
                                         command=lambda: self.switch_tab("statistics"),
                                         fg_color="#555555", hover_color="#666666")
        self.stats_tab_btn.pack(side="left", padx=5, pady=10)

        # Content frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Create tab contents
        self._create_player_tab()
        self._create_visualizer_tab()
        self._create_statistics_tab()

        # Show player tab initially
        self.switch_tab("player")

    def switch_tab(self, tab_name):
        """Switch between tabs"""
        # Update button colors
        buttons = {
            "player": self.player_tab_btn,
            "visualizer": self.visualizer_tab_btn,
            "statistics": self.stats_tab_btn
        }

        tabs = {
            "player": self.player_tab,
            "visualizer": self.visualizer_tab,
            "statistics": self.statistics_tab
        }

        for name, button in buttons.items():
            if name == tab_name:
                button.configure(fg_color="#1f538d")
            else:
                button.configure(fg_color="#555555")

        # Hide all tabs
        for tab in tabs.values():
            tab.pack_forget()

        # Show selected tab
        tabs[tab_name].pack(fill="both", expand=True)
        self.current_tab = tab_name

    def _create_player_tab(self):
        """Create the main player tab"""
        self.player_tab = ctk.CTkFrame(self.content_frame)

        # File loading section
        file_frame = ctk.CTkFrame(self.player_tab)
        file_frame.pack(fill="x", padx=20, pady=20)

        files_title = ctk.CTkLabel(file_frame, text="📁 Audio Files",
                                 font=ctk.CTkFont(size=18, weight="bold"))
        files_title.pack(pady=(15, 10))

        # Target file
        target_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        target_frame.pack(fill="x", padx=20, pady=5)

        target_btn = ctk.CTkButton(target_frame, text="📂 Load Target Track",
                                 width=200, command=self._load_target_file)
        target_btn.pack(side="left", padx=(0, 10))

        self.target_label = ctk.CTkLabel(target_frame, text="No target file loaded",
                                       text_color="#888888")
        self.target_label.pack(side="left")

        # Reference file
        ref_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        ref_frame.pack(fill="x", padx=20, pady=5)

        ref_btn = ctk.CTkButton(ref_frame, text="🎯 Load Reference Track",
                              width=200, command=self._load_reference_file)
        ref_btn.pack(side="left", padx=(0, 10))

        self.reference_label = ctk.CTkLabel(ref_frame, text="No reference loaded",
                                          text_color="#888888")
        self.reference_label.pack(side="left")

        # Transport controls
        controls_frame = ctk.CTkFrame(self.player_tab)
        controls_frame.pack(fill="x", padx=20, pady=10)

        controls_title = ctk.CTkLabel(controls_frame, text="🎛️ Playback Controls",
                                    font=ctk.CTkFont(size=18, weight="bold"))
        controls_title.pack(pady=(15, 10))

        # Transport buttons
        transport_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        transport_frame.pack(pady=10)

        self.play_btn = ctk.CTkButton(transport_frame, text="▶️ Play", width=100, height=40,
                                    command=self._toggle_play,
                                    font=ctk.CTkFont(size=14, weight="bold"))
        self.play_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(transport_frame, text="⏹️ Stop", width=100, height=40,
                                    command=self._stop,
                                    font=ctk.CTkFont(size=14, weight="bold"))
        self.stop_btn.pack(side="left", padx=5)

        # Position and progress
        progress_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20, pady=10)

        self.position_label = ctk.CTkLabel(progress_frame, text="00:00")
        self.position_label.pack(side="left")

        self.progress_slider = ctk.CTkSlider(progress_frame, from_=0, to=100,
                                           command=self._on_seek, width=200)
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=10)

        self.duration_label = ctk.CTkLabel(progress_frame, text="02:00")
        self.duration_label.pack(side="right")

        # Volume control
        volume_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        volume_frame.pack(pady=5)

        ctk.CTkLabel(volume_frame, text="🔊 Volume:").pack(side="left", padx=(0, 10))
        self.volume_slider = ctk.CTkSlider(volume_frame, from_=0, to=1,
                                         command=self._on_volume_change, width=200)
        self.volume_slider.set(0.8)
        self.volume_slider.pack(side="left")

        self.volume_label = ctk.CTkLabel(volume_frame, text="80%")
        self.volume_label.pack(side="left", padx=(10, 0))

        # Effects section
        effects_frame = ctk.CTkFrame(self.player_tab)
        effects_frame.pack(fill="x", padx=20, pady=10)

        effects_title = ctk.CTkLabel(effects_frame, text="🎛️ DSP Effects",
                                   font=ctk.CTkFont(size=18, weight="bold"))
        effects_title.pack(pady=(15, 10))

        self.level_matching_switch = ctk.CTkSwitch(effects_frame,
                                                 text="🎯 Real-time Level Matching",
                                                 command=self._toggle_level_matching,
                                                 font=ctk.CTkFont(size=14))
        self.level_matching_switch.pack(pady=10)
        self.level_matching_switch.select()  # Start enabled

    def _create_visualizer_tab(self):
        """Create the visualization tab"""
        self.visualizer_tab = ctk.CTkFrame(self.content_frame)

        viz_title = ctk.CTkLabel(self.visualizer_tab, text="📊 Real-time Audio Visualization",
                               font=ctk.CTkFont(size=20, weight="bold"))
        viz_title.pack(pady=20)

        # Level meters
        levels_frame = ctk.CTkFrame(self.visualizer_tab, height=300)
        levels_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.visualization = VisualizationFrame(levels_frame)
        self.visualization.pack(fill="both", expand=True, padx=10, pady=10)

        # Processing info
        proc_frame = ctk.CTkFrame(self.visualizer_tab)
        proc_frame.pack(fill="x", padx=20, pady=10)

        self.cpu_label = ctk.CTkLabel(proc_frame, text="💻 CPU: 5.0%",
                                    font=ctk.CTkFont(size=14))
        self.cpu_label.pack(side="left", padx=20, pady=10)

        self.chunks_label = ctk.CTkLabel(proc_frame, text="📊 Chunks: 0",
                                       font=ctk.CTkFont(size=14))
        self.chunks_label.pack(side="left", padx=20, pady=10)

        self.status_indicator = ctk.CTkLabel(proc_frame, text="🔴 Inactive",
                                           font=ctk.CTkFont(size=14))
        self.status_indicator.pack(side="right", padx=20, pady=10)

    def _create_statistics_tab(self):
        """Create the statistics tab"""
        self.statistics_tab = ctk.CTkFrame(self.content_frame)

        stats_title = ctk.CTkLabel(self.statistics_tab, text="📈 Player Statistics",
                                 font=ctk.CTkFont(size=20, weight="bold"))
        stats_title.pack(pady=20)

        # Statistics text display
        self.stats_textbox = ctk.CTkTextbox(self.statistics_tab, width=500, height=400,
                                          font=ctk.CTkFont(family="Courier", size=11))
        self.stats_textbox.pack(expand=True, fill="both", padx=20, pady=10)

    def start_player_updates(self):
        """Start periodic GUI updates"""
        def update_loop():
            while True:
                try:
                    # Update position for mock player during playback
                    if hasattr(self.player, 'state') and self.player.state == "playing":
                        if hasattr(self.player, 'position') and hasattr(self.player, 'duration'):
                            self.player.position = min(self.player.position + 0.1, self.player.duration)
                            if self.player.position >= self.player.duration:
                                self.player.stop()
                    time.sleep(0.1)
                except:
                    break

        # Only start update loop for mock player
        if not HAS_REAL_PLAYER:
            update_thread = threading.Thread(target=update_loop, daemon=True)
            update_thread.start()

    # Event handlers
    def _load_target_file(self):
        """Load target audio file"""
        filename = filedialog.askopenfilename(
            title="Select Target Audio File",
            filetypes=[
                ("Audio files", "*.wav *.flac *.mp3 *.m4a *.aac"),
                ("WAV files", "*.wav"),
                ("FLAC files", "*.flac"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )

        if filename:
            success = self.player.load_file(filename)
            if success:
                self.target_label.configure(text=f"✅ {os.path.basename(filename)}",
                                          text_color="#00ff88")
                self._update_status(f"🎵 Loaded: {os.path.basename(filename)}")
            else:
                self.target_label.configure(text="❌ Failed to load", text_color="#ff4444")
                self._update_status("❌ Failed to load target file")

    def _load_reference_file(self):
        """Load reference audio file"""
        filename = filedialog.askopenfilename(
            title="Select Reference Audio File",
            filetypes=[
                ("Audio files", "*.wav *.flac *.mp3 *.m4a *.aac"),
                ("WAV files", "*.wav"),
                ("FLAC files", "*.flac"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )

        if filename:
            success = self.player.load_reference_track(filename)
            if success:
                self.reference_label.configure(text=f"🎯 {os.path.basename(filename)}",
                                             text_color="#00ddff")
                self._update_status(f"🎯 Reference loaded: {os.path.basename(filename)}")
            else:
                self.reference_label.configure(text="❌ Failed to load", text_color="#ff4444")
                self._update_status("❌ Failed to load reference file")

    def _toggle_play(self):
        """Toggle play/pause"""
        try:
            info = self.player.get_playback_info()
            current_state = info.get('state', 'stopped')

            if current_state == "playing":
                self.player.pause()
                self.play_btn.configure(text="▶️ Play")
            else:
                self.player.play()
                self.play_btn.configure(text="⏸️ Pause")
        except Exception as e:
            print(f"❌ Playback error: {e}")
            self._update_status(f"❌ Playback error: {e}")

    def _stop(self):
        """Stop playback"""
        try:
            self.player.stop()
            self.play_btn.configure(text="▶️ Play")
        except Exception as e:
            print(f"❌ Stop error: {e}")

    def _on_seek(self, value):
        """Handle seek slider"""
        if not self.seeking:
            self.seeking = True
            try:
                info = self.player.get_playback_info()
                duration = info.get('duration_seconds', 0)
                position = float(value) / 100.0 * duration
                self.player.seek(position)
            except Exception as e:
                print(f"❌ Seek error: {e}")
            finally:
                self.seeking = False

    def _on_volume_change(self, value):
        """Handle volume change"""
        try:
            self.player.set_volume(float(value))
            self.volume_label.configure(text=f"{int(float(value) * 100)}%")
        except Exception as e:
            print(f"❌ Volume error: {e}")

    def _toggle_level_matching(self):
        """Toggle level matching"""
        try:
            enabled = self.level_matching_switch.get()
            self.player.set_effect_enabled('level_matching', enabled)
            status = "enabled" if enabled else "disabled"
            self._update_status(f"🎛️ Level matching {status}")
        except Exception as e:
            print(f"❌ Effect toggle error: {e}")

    def _update_status(self, message):
        """Update status bar"""
        self.status_label.configure(text=message)

    def _on_player_update(self, info):
        """Handle player state updates"""
        try:
            # Update position display
            if not self.seeking:
                position = info.get('position_seconds', 0)
                duration = info.get('duration_seconds', 0)

                pos_min, pos_sec = divmod(int(position), 60)
                dur_min, dur_sec = divmod(int(duration), 60)

                self.position_label.configure(text=f"{pos_min:02d}:{pos_sec:02d}")
                self.duration_label.configure(text=f"{dur_min:02d}:{dur_sec:02d}")

                if duration > 0:
                    progress = (position / duration) * 100
                    self.progress_slider.set(progress)

            # Update DSP visualization
            dsp = info.get('dsp', {})
            level_stats = dsp.get('level_matching', {})

            if level_stats.get('status') == 'active':
                mid_gain = level_stats.get('mid_gain_current', 1.0)
                side_gain = level_stats.get('side_gain_current', 1.0)
                self.visualization.update_levels(mid_gain, side_gain, True)

                # Update status indicators
                self.status_indicator.configure(text="🟢 Processing", text_color="#00ff00")
            else:
                self.visualization.update_levels(1.0, 1.0, False)
                self.status_indicator.configure(text="🔴 Inactive", text_color="#ff4444")

            # Update CPU and chunks
            cpu_usage = dsp.get('cpu_usage', 0) * 100
            chunks = dsp.get('chunks_processed', 0)

            self.cpu_label.configure(text=f"💻 CPU: {cpu_usage:.1f}%")
            self.chunks_label.configure(text=f"📊 Chunks: {chunks}")

            # Update statistics
            self._update_statistics(info)

        except Exception as e:
            print(f"❌ Update error: {e}")

    def _update_statistics(self, info):
        """Update statistics display"""
        try:
            stats_text = "=== MODERN MATCHERING PLAYER STATISTICS ===\\n\\n"

            # Player type
            stats_text += f"🎵 ENGINE TYPE: {self.player_type}\\n\\n"

            # Playback info
            stats_text += "🎵 PLAYBACK STATUS\\n"
            stats_text += f"State: {info.get('state', 'unknown').upper()}\\n"
            stats_text += f"Position: {info.get('position_seconds', 0):.1f}s\\n"
            stats_text += f"Duration: {info.get('duration_seconds', 0):.1f}s\\n"
            stats_text += f"Volume: {info.get('volume', 0) * 100:.0f}%\\n"
            stats_text += f"File: {info.get('filename', 'None')}\\n\\n"

            # DSP info
            dsp = info.get('dsp', {})
            stats_text += "🎛️ DSP PROCESSING\\n"
            stats_text += f"Active: {'✅ YES' if dsp.get('processing_active') else '❌ NO'}\\n"
            stats_text += f"CPU Usage: {dsp.get('cpu_usage', 0) * 100:.1f}%\\n"
            stats_text += f"Chunks Processed: {dsp.get('chunks_processed', 0)}\\n"
            stats_text += f"Performance Mode: {'✅ ON' if dsp.get('performance_mode') else '❌ OFF'}\\n\\n"

            # Level matching
            level_stats = dsp.get('level_matching', {})
            stats_text += "🎯 LEVEL MATCHING\\n"
            stats_text += f"Status: {level_stats.get('status', 'inactive').upper()}\\n"
            stats_text += f"Reference Loaded: {'✅ YES' if level_stats.get('reference_loaded') else '❌ NO'}\\n"
            stats_text += f"Mid Gain: {level_stats.get('mid_gain_current', 1.0):.2f}\\n"
            stats_text += f"Side Gain: {level_stats.get('side_gain_current', 1.0):.2f}\\n"
            stats_text += f"Target Mid RMS: {level_stats.get('target_rms_mid_db', 0):.1f} dB\\n"
            stats_text += f"Target Side RMS: {level_stats.get('target_rms_side_db', 0):.1f} dB\\n\\n"

            # System info
            stats_text += "💻 SYSTEM INFO\\n"
            stats_text += f"Audio Library: {'✅ Available' if HAS_AUDIO else '❌ Missing'}\\n"
            stats_text += f"Real Player: {'✅ Available' if HAS_REAL_PLAYER else '❌ Mock Mode'}\\n"

            # Update the textbox
            self.stats_textbox.delete("1.0", "end")
            self.stats_textbox.insert("1.0", stats_text)

        except Exception as e:
            print(f"❌ Statistics update error: {e}")

    def on_closing(self):
        """Handle window closing"""
        try:
            if hasattr(self.player, 'cleanup'):
                self.player.cleanup()
        except:
            pass
        self.destroy()


def main():
    """Main application entry point"""
    print("🎵 Starting Modern Matchering Player...")
    print(f"Audio support: {'✅ Available' if HAS_AUDIO else '❌ Missing'}")
    print(f"Real player: {'✅ Available' if HAS_REAL_PLAYER else '❌ Mock mode'}")

    app = ModernMatcheringPlayer()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()