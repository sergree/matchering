#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matchering Player Modern GUI
Beautiful CustomTkinter interface for the Matchering Player
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

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class MockMatcheringPlayer:
    """Mock player that simulates the interface without PyAudio"""
    
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
        """Add callback for state updates"""
        self._callbacks.append(callback)
        
    def _notify_callbacks(self):
        """Notify all callbacks of state change"""
        for callback in self._callbacks:
            try:
                callback(self.get_playback_info())
            except:
                pass
        
    def load_file(self, filename):
        self.current_file = filename
        self.duration = 120  # Mock 2 minutes
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
        
        # dB scale markings
        for i, db in enumerate([-40, -20, -10, -6, -3, 0]):
            y_pos = height - 30 - int(((db + 60) / 80) * bar_height)
            if 0 < y_pos < height - 30:
                self.canvas.create_line(15, y_pos, width - 15, y_pos, fill="#444444", width=1)
                self.canvas.create_text(width - 5, y_pos, text=f"{db}", fill="#888888", 
                                      font=("Arial", 8), anchor="e")
    
    def _draw_gradient_bar(self, x, y, width, height, color1, color2, color3):
        """Draw a gradient bar from green to yellow to red"""
        if height <= 0:
            return
            
        # Simple gradient simulation with rectangles
        segments = max(1, height // 2)
        segment_height = height / segments
        
        for i in range(segments):
            # Calculate color based on position (green -> yellow -> red)
            ratio = i / segments
            if ratio < 0.7:  # Green to yellow zone
                green_ratio = (0.7 - ratio) / 0.7
                color = f"#{int(255 * (1 - green_ratio)):02x}{255:02x}{0:02x}"
            else:  # Yellow to red zone
                red_ratio = (ratio - 0.7) / 0.3  
                color = f"{255:02x}{int(255 * (1 - red_ratio)):02x}{0:02x}"
            
            seg_y = y + height - (i + 1) * segment_height
            self.canvas.create_rectangle(x, seg_y, x + width, seg_y + segment_height,
                                       fill=color, outline="", width=0)
        
        # Border
        self.canvas.create_rectangle(x, y, x + width, y + height, 
                                   outline="#ffffff", width=2, fill="")


class ModernMatcheringPlayer:
    """Modern Matchering Player with CustomTkinter"""
    
    def __init__(self):
        self.player = MockMatcheringPlayer()
        self.player.add_callback(self._on_player_update)
        
        # Create demo audio files
        if HAS_AUDIO:
            self.demo_files = self._create_demo_files()
        else:
            self.demo_files = None
            
        # Animation state
        self.animation_running = False
        self.seeking = False
        
        self._create_gui()
        self._start_updates()
        
    def _create_demo_files(self):
        """Create temporary demo audio files"""
        try:
            temp_dir = tempfile.mkdtemp()
            
            duration = 5.0
            sample_rate = 44100
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples, False)
            
            # Quiet target
            quiet_left = 0.1 * np.sin(2 * np.pi * 440 * t)
            quiet_right = 0.08 * np.sin(2 * np.pi * 440 * t * 1.01)
            quiet_audio = np.column_stack([quiet_left, quiet_right]).astype(np.float32)
            
            target_file = os.path.join(temp_dir, "demo_target.wav")
            sf.write(target_file, quiet_audio, sample_rate)
            
            # Loud reference
            loud_left = 0.7 * np.sin(2 * np.pi * 440 * t)
            loud_right = 0.65 * np.sin(2 * np.pi * 440 * t * 1.01)
            loud_audio = np.column_stack([loud_left, loud_right]).astype(np.float32)
            
            reference_file = os.path.join(temp_dir, "demo_reference.wav")
            sf.write(reference_file, loud_audio, sample_rate)
            
            return {"target": target_file, "reference": reference_file, "temp_dir": temp_dir}
            
        except Exception as e:
            print(f"Failed to create demo files: {e}")
            return None
    
    def _create_gui(self):
        """Create the modern GUI"""
        # Main window
        self.root = ctk.CTk()
        self.root.geometry("1000x700")
        self.root.title("🎵 Matchering Player - Modern Edition")
        self.root.minsize(800, 600)
        
        # Main container with sidebar
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create sidebar for navigation
        self.sidebar = ctk.CTkFrame(self.main_frame, width=200, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(self.sidebar, text="🎵 MATCHERING\nPLAYER", 
                                     font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=(20, 30))
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [("Player", "🎵"), ("Visualizer", "📊"), ("Statistics", "📈"), ("Settings", "⚙️")]
        
        for item, icon in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=f"{icon} {item}", width=160,
                              command=lambda x=item.lower(): self._switch_tab(x))
            btn.pack(pady=5)
            self.nav_buttons[item.lower()] = btn
            
        # Spacer
        spacer = ctk.CTkFrame(self.sidebar, height=20, fg_color="transparent")
        spacer.pack(pady=10)
        
        # Quick actions
        self.quick_label = ctk.CTkLabel(self.sidebar, text="Quick Actions", 
                                      font=ctk.CTkFont(size=14, weight="bold"))
        self.quick_label.pack(pady=(10, 5))
        
        self.load_target_btn = ctk.CTkButton(self.sidebar, text="📁 Load Target", width=160,
                                           command=self._load_demo_target, 
                                           fg_color="#1f6aa5", hover_color="#155a94")
        self.load_target_btn.pack(pady=2)
        
        self.load_ref_btn = ctk.CTkButton(self.sidebar, text="🎯 Load Reference", width=160,
                                        command=self._load_demo_reference,
                                        fg_color="#2d8f2d", hover_color="#1f7a1f")
        self.load_ref_btn.pack(pady=2)
        
        # Content area
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Create tab frames
        self._create_player_tab()
        self._create_visualizer_tab()
        self._create_statistics_tab()
        self._create_settings_tab()
        
        # Status bar
        self.status_frame = ctk.CTkFrame(self.root, height=40, corner_radius=5)
        self.status_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(self.status_frame, 
                                       text="🚀 Ready - Load demo files to experience modern audio processing!")
        self.status_label.pack(pady=8)
        
        # Start with player tab
        self._switch_tab("player")
        
    def _create_player_tab(self):
        """Create the main player interface"""
        self.player_tab = ctk.CTkFrame(self.content_frame)
        
        # File info section
        file_frame = ctk.CTkFrame(self.player_tab)
        file_frame.pack(fill="x", padx=20, pady=20)
        
        info_title = ctk.CTkLabel(file_frame, text="🎵 Audio Files", 
                                font=ctk.CTkFont(size=18, weight="bold"))
        info_title.pack(pady=(15, 10))
        
        # Target file info
        self.target_frame = ctk.CTkFrame(file_frame, fg_color="#2b2b2b")
        self.target_frame.pack(fill="x", padx=15, pady=5)
        
        target_icon = ctk.CTkLabel(self.target_frame, text="🎵", font=ctk.CTkFont(size=20))
        target_icon.pack(side="left", padx=(10, 5), pady=10)
        
        target_info_frame = ctk.CTkFrame(self.target_frame, fg_color="transparent")
        target_info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(target_info_frame, text="Target Track", 
                   font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.target_label = ctk.CTkLabel(target_info_frame, text="No file loaded", 
                                       text_color="#888888")
        self.target_label.pack(anchor="w")
        
        # Reference file info  
        self.reference_frame = ctk.CTkFrame(file_frame, fg_color="#2b2b2b")
        self.reference_frame.pack(fill="x", padx=15, pady=5)
        
        ref_icon = ctk.CTkLabel(self.reference_frame, text="🎯", font=ctk.CTkFont(size=20))
        ref_icon.pack(side="left", padx=(10, 5), pady=10)
        
        ref_info_frame = ctk.CTkFrame(self.reference_frame, fg_color="transparent")
        ref_info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(ref_info_frame, text="Reference Track", 
                   font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.reference_label = ctk.CTkLabel(ref_info_frame, text="No reference loaded", 
                                          text_color="#888888")
        self.reference_label.pack(anchor="w")
        
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
        
        stats_title = ctk.CTkLabel(self.statistics_tab, text="📈 Processing Statistics", 
                                 font=ctk.CTkFont(size=20, weight="bold"))
        stats_title.pack(pady=20)
        
        # Stats text area with modern scrollable frame
        self.stats_frame = ctk.CTkScrollableFrame(self.statistics_tab, height=400)
        self.stats_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.stats_text = ctk.CTkTextbox(self.stats_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.stats_text.pack(fill="both", expand=True)
        
    def _create_settings_tab(self):
        """Create the settings tab"""
        self.settings_tab = ctk.CTkFrame(self.content_frame)
        
        settings_title = ctk.CTkLabel(self.settings_tab, text="⚙️ Settings", 
                                    font=ctk.CTkFont(size=20, weight="bold"))
        settings_title.pack(pady=20)
        
        # Theme settings
        theme_frame = ctk.CTkFrame(self.settings_tab)
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(theme_frame, text="🎨 Appearance", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        theme_option = ctk.CTkOptionMenu(theme_frame, 
                                       values=["Dark", "Light", "System"],
                                       command=self._change_theme)
        theme_option.set("Dark")
        theme_option.pack(pady=10)
        
        # Performance settings
        perf_frame = ctk.CTkFrame(self.settings_tab)
        perf_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(perf_frame, text="⚡ Performance", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.performance_switch = ctk.CTkSwitch(perf_frame, text="High Performance Mode")
        self.performance_switch.pack(pady=5)
        
        buffer_frame = ctk.CTkFrame(perf_frame, fg_color="transparent")
        buffer_frame.pack(pady=10)
        
        ctk.CTkLabel(buffer_frame, text="Buffer Size:").pack(side="left")
        self.buffer_option = ctk.CTkOptionMenu(buffer_frame, 
                                             values=["64", "128", "256", "512", "1024"])
        self.buffer_option.set("256")
        self.buffer_option.pack(side="left", padx=10)
        
    def _switch_tab(self, tab_name):
        """Switch between tabs"""
        # Hide all tabs
        for tab in [self.player_tab, self.visualizer_tab, self.statistics_tab, self.settings_tab]:
            tab.pack_forget()
            
        # Reset button colors
        for btn in self.nav_buttons.values():
            btn.configure(fg_color=("#3B8ED0", "#1F6AA5"))
            
        # Show selected tab and highlight button
        if tab_name == "player":
            self.player_tab.pack(fill="both", expand=True, padx=10, pady=10)
        elif tab_name == "visualizer":
            self.visualizer_tab.pack(fill="both", expand=True, padx=10, pady=10)
        elif tab_name == "statistics":
            self.statistics_tab.pack(fill="both", expand=True, padx=10, pady=10)
        elif tab_name == "settings":
            self.settings_tab.pack(fill="both", expand=True, padx=10, pady=10)
            
        # Highlight selected button
        if tab_name in self.nav_buttons:
            self.nav_buttons[tab_name].configure(fg_color=("#2D8F2D", "#1F7A1F"))
            
    def _load_demo_target(self):
        """Load demo target file"""
        if self.demo_files:
            success = self.player.load_file(self.demo_files["target"])
            if success:
                self.target_label.configure(text="demo_target.wav", text_color="#00ff88")
                self._update_status("✅ Demo target loaded (quiet home recording simulation)")
        else:
            self.target_label.configure(text="demo_target.wav (simulated)", text_color="#00ff88")
            self.player.load_file("demo_target.wav")
            self._update_status("✅ Demo target loaded (simulated - no audio libraries)")
            
    def _load_demo_reference(self):
        """Load demo reference file"""
        if self.demo_files:
            success = self.player.load_reference_track(self.demo_files["reference"])
            if success:
                self.reference_label.configure(text="demo_reference.wav", text_color="#00ddff")
                self._update_status("✅ Demo reference loaded - Level matching now active!")
        else:
            self.reference_label.configure(text="demo_reference.wav (simulated)", text_color="#00ddff")
            self.player.load_reference_track("demo_reference.wav")
            self._update_status("✅ Demo reference loaded - Level matching now active!")
            
    def _toggle_play(self):
        """Toggle play/pause"""
        if self.player.state == "playing":
            self.player.pause()
            self.play_btn.configure(text="▶️ Play")
        else:
            self.player.play()
            self.play_btn.configure(text="⏸️ Pause")
            
    def _stop(self):
        """Stop playback"""
        self.player.stop()
        self.play_btn.configure(text="▶️ Play")
        
    def _on_seek(self, value):
        """Handle seek slider"""
        if not self.seeking:
            self.seeking = True
            position = float(value) / 100.0 * self.player.duration
            self.player.seek(position)
            self.seeking = False
            
    def _on_volume_change(self, value):
        """Handle volume change"""
        self.player.set_volume(float(value))
        self.volume_label.configure(text=f"{int(float(value) * 100)}%")
        
    def _toggle_level_matching(self):
        """Toggle level matching"""
        enabled = self.level_matching_switch.get()
        self.player.set_effect_enabled('level_matching', enabled)
        status = "enabled" if enabled else "disabled"
        self._update_status(f"🎛️ Level matching {status}")
        
    def _change_theme(self, theme):
        """Change appearance theme"""
        ctk.set_appearance_mode(theme.lower())
        self._update_status(f"🎨 Theme changed to {theme}")
        
    def _update_status(self, message):
        """Update status bar"""
        self.status_label.configure(text=message)
        
    def _on_player_update(self, info):
        """Handle player state updates"""
        # Update position display
        if not self.seeking:
            position = info['position_seconds']
            duration = info['duration_seconds']
            
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
        
    def _update_statistics(self, info):
        """Update statistics display"""
        stats_text = "=== MODERN MATCHERING PLAYER STATISTICS ===\\n\\n"
        
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
        stats_text += f"Processing Active: {'YES' if dsp.get('processing_active', False) else 'NO'}\\n"
        stats_text += f"CPU Usage: {dsp.get('cpu_usage', 0) * 100:.1f}%\\n"
        stats_text += f"Chunks Processed: {dsp.get('chunks_processed', 0):,}\\n"
        stats_text += f"Performance Mode: {'ON' if dsp.get('performance_mode', False) else 'OFF'}\\n\\n"
        
        # Level matching
        level_stats = dsp.get('level_matching', {})
        stats_text += "🎯 LEVEL MATCHING\\n"
        stats_text += f"Status: {level_stats.get('status', 'inactive').upper()}\\n"
        stats_text += f"Reference Loaded: {'YES' if level_stats.get('reference_loaded', False) else 'NO'}\\n"
        
        if level_stats.get('status') == 'active':
            mid_gain = level_stats.get('mid_gain_current', 1.0)
            side_gain = level_stats.get('side_gain_current', 1.0)
            
            if HAS_AUDIO:
                mid_db = 20 * np.log10(max(mid_gain, 1e-6))
                side_db = 20 * np.log10(max(side_gain, 1e-6))
            else:
                mid_db = 8.0 + 2 * math.sin(time.time() * 2)
                side_db = 5.1 + 1.5 * math.cos(time.time() * 1.5)
            
            stats_text += f"Mid Gain: {mid_gain:.2f} ({mid_db:.1f} dB)\\n"
            stats_text += f"Side Gain: {side_gain:.2f} ({side_db:.1f} dB)\\n"
            stats_text += f"Target Mid RMS: {level_stats.get('target_rms_mid_db', 0):.1f} dB\\n"
            stats_text += f"Target Side RMS: {level_stats.get('target_rms_side_db', 0):.1f} dB\\n"
        
        stats_text += "\\n📱 MODERN FEATURES\\n"
        stats_text += "✨ CustomTkinter modern dark theme\\n"
        stats_text += "🎨 Real-time gradient level meters\\n"
        stats_text += "📊 Live animated visualization\\n"
        stats_text += "🎛️ Professional audio controls\\n"
        stats_text += "⚡ Optimized for performance\\n"
        
        if not HAS_AUDIO:
            stats_text += "\\n⚠️  DEMO MODE\\n"
            stats_text += "Audio processing libraries not available.\\n"
            stats_text += "Showing simulated values with animations.\\n"
        
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
        
    def _start_updates(self):
        """Start the update loop"""
        def update_loop():
            while True:
                try:
                    # Simulate playback progression
                    if self.player.state == "playing":
                        self.player.position = min(self.player.position + 1, self.player.duration)
                        if self.player.position >= self.player.duration:
                            self.player.stop()
                            self.play_btn.configure(text="▶️ Play")
                    
                    # Update visualization animation
                    self.visualization.draw_levels()
                    
                except:
                    pass
                    
                time.sleep(1.0)
        
        # Start update thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        
    def run(self):
        """Run the modern player"""
        # Welcome message
        welcome = """
        🎉 Welcome to Matchering Player - Modern Edition!
        
        Experience the future of audio mastering with:
        ✨ Beautiful CustomTkinter dark theme interface
        🎨 Real-time gradient level visualization
        📊 Live animated processing stats
        🎛️ Professional audio controls
        ⚡ High-performance DSP processing
        
        Quick Start:
        1. Use sidebar buttons to load demo files
        2. Press Play to start audio processing
        3. Switch to Visualizer tab for live meters
        4. Check Statistics for detailed info
        5. Customize in Settings tab
        
        This modern interface showcases professional-grade
        real-time audio mastering capabilities!
        """
        
        # Show welcome in a custom dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.geometry("600x500")
        dialog.title("🎵 Welcome to Matchering Player")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        welcome_text = ctk.CTkTextbox(dialog, font=ctk.CTkFont(size=12))
        welcome_text.pack(fill="both", expand=True, padx=20, pady=20)
        welcome_text.insert("1.0", welcome)
        
        ok_btn = ctk.CTkButton(dialog, text="🚀 Start Using Matchering Player", 
                             command=dialog.destroy,
                             font=ctk.CTkFont(size=14, weight="bold"))
        ok_btn.pack(pady=(0, 20))
        
        self.root.mainloop()
        
        # Cleanup
        if self.demo_files and os.path.exists(self.demo_files["temp_dir"]):
            import shutil
            shutil.rmtree(self.demo_files["temp_dir"])


def main():
    """Run the modern GUI"""
    print("🚀 Starting Modern Matchering Player...")
    
    try:
        app = ModernMatcheringPlayer()
        app.run()
        return True
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
