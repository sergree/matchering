# -*- coding: utf-8 -*-

"""
Main GUI Window for Matchering Player
Simple Tkinter interface for audio playback and DSP controls
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from typing import Optional
import os

from ..core.player import MatcheringPlayer
from ..core.config import PlayerConfig
from ..core.audio_manager import PlaybackState


class MatcheringPlayerGUI:
    """Main GUI window for Matchering Player"""
    
    def __init__(self):
        # Initialize the player
        try:
            config = PlayerConfig(
                buffer_size_ms=100.0,
                enable_level_matching=True,
                enable_frequency_matching=True,
                enable_stereo_width=True,
                enable_auto_mastering=True,  # Enable auto-mastering
                enable_visualization=True
            )
            self.player = MatcheringPlayer(config)
            
            # Set up callbacks
            self.player.set_position_callback(self._on_position_update)
            self.player.set_state_callback(self._on_state_change)
            
        except Exception as e:
            print(f"❌ Failed to initialize player: {e}")
            self.player = None
        
        # GUI state
        self.current_position = 0.0
        self.duration = 0.0
        self.is_seeking = False
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Matchering Player - Realtime Audio Matching")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Modern looking theme
        
        self._create_menu()
        self._create_widgets()
        
        # Start GUI update timer
        self._update_gui()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Target Track...", command=self._load_target_file)
        file_menu.add_command(label="Load Reference Track...", command=self._load_reference_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Processing Stats", command=self._show_stats)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === FILE LOADING SECTION ===
        file_frame = ttk.LabelFrame(main_frame, text="Audio Files", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Target file
        ttk.Label(file_frame, text="Target:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.target_file_var = tk.StringVar(value="No file loaded")
        self.target_label = ttk.Label(file_frame, textvariable=self.target_file_var,
                                     foreground="gray", font=("TkDefaultFont", 9))
        self.target_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(file_frame, text="Browse...", command=self._load_target_file).grid(row=0, column=2)
        
        # Reference file
        ttk.Label(file_frame, text="Reference:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.reference_file_var = tk.StringVar(value="No reference loaded")
        self.reference_label = ttk.Label(file_frame, textvariable=self.reference_file_var,
                                        foreground="gray", font=("TkDefaultFont", 9))
        self.reference_label.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        ttk.Button(file_frame, text="Browse...", command=self._load_reference_file).grid(row=1, column=2, pady=(10, 0))
        
        # === PLAYBACK CONTROLS SECTION ===
        controls_frame = ttk.LabelFrame(main_frame, text="Playback Controls", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Transport controls
        transport_frame = ttk.Frame(controls_frame)
        transport_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        self.play_button = ttk.Button(transport_frame, text="▶ Play", command=self._play_pause)
        self.play_button.grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(transport_frame, text="⏹ Stop", command=self._stop).grid(row=0, column=1, padx=5)
        
        # Position display
        position_frame = ttk.Frame(controls_frame)
        position_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        position_frame.columnconfigure(1, weight=1)
        
        self.position_var = tk.StringVar(value="00:00")
        ttk.Label(position_frame, textvariable=self.position_var).grid(row=0, column=0)
        
        # Progress bar / seek bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(position_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     variable=self.progress_var, command=self._on_seek)
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
        
        self.duration_var = tk.StringVar(value="00:00")
        ttk.Label(position_frame, textvariable=self.duration_var).grid(row=0, column=2)
        
        # === DSP CONTROLS SECTION ===
        dsp_frame = ttk.LabelFrame(main_frame, text="DSP Effects", padding="10")
        dsp_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        dsp_frame.columnconfigure(1, weight=1)
        
        # Level matching toggle
        self.level_matching_var = tk.BooleanVar(value=True)
        level_check = ttk.Checkbutton(dsp_frame, text="Level Matching",
                                     variable=self.level_matching_var,
                                     command=self._toggle_level_matching)
        level_check.grid(row=0, column=0, sticky=tk.W)

        # Frequency matching toggle
        self.frequency_matching_var = tk.BooleanVar(value=True)
        freq_check = ttk.Checkbutton(dsp_frame, text="Frequency Matching (EQ)",
                                    variable=self.frequency_matching_var,
                                    command=self._toggle_frequency_matching)
        freq_check.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # Stereo width toggle
        self.stereo_width_var = tk.BooleanVar(value=True)
        stereo_check = ttk.Checkbutton(dsp_frame, text="Stereo Width Control",
                                      variable=self.stereo_width_var,
                                      command=self._toggle_stereo_width)
        stereo_check.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))

        # Auto-mastering toggle
        self.auto_mastering_var = tk.BooleanVar(value=True)
        auto_check = ttk.Checkbutton(dsp_frame, text="🤖 Auto-Mastering (No Reference Needed!)",
                                    variable=self.auto_mastering_var,
                                    command=self._toggle_auto_mastering)
        auto_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Auto-mastering profile selection
        auto_profile_frame = ttk.Frame(dsp_frame)
        auto_profile_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        ttk.Label(auto_profile_frame, text="Profile:").grid(row=0, column=0, sticky=tk.W)

        self.auto_profile_var = tk.StringVar(value="adaptive")
        profile_combo = ttk.Combobox(auto_profile_frame, textvariable=self.auto_profile_var,
                                    values=["adaptive", "modern_pop", "electronic", "acoustic", "classical", "podcast"],
                                    state="readonly", width=15)
        profile_combo.grid(row=0, column=1, padx=(10, 0), sticky=tk.W)
        profile_combo.bind("<<ComboboxSelected>>", self._on_profile_change)

        self.auto_status_label = ttk.Label(auto_profile_frame, text="🧠 Analyzing...", foreground="blue")
        self.auto_status_label.grid(row=0, column=2, padx=(10, 0), sticky=tk.W)

        # Bypass all toggle
        self.bypass_var = tk.BooleanVar(value=False)
        bypass_check = ttk.Checkbutton(dsp_frame, text="Bypass All Effects",
                                      variable=self.bypass_var,
                                      command=self._toggle_bypass)
        bypass_check.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

        # Stereo width slider (manual control)
        stereo_control_frame = ttk.Frame(dsp_frame)
        stereo_control_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E), padx=(20, 0))

        ttk.Label(stereo_control_frame, text="Stereo Width:").grid(row=0, column=0, sticky=tk.W)

        self.stereo_width_scale = tk.DoubleVar(value=1.0)
        stereo_slider = ttk.Scale(stereo_control_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                                 variable=self.stereo_width_scale, command=self._on_stereo_width_change)
        stereo_slider.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(2, 0))
        stereo_control_frame.columnconfigure(0, weight=1)

        self.stereo_width_label = ttk.Label(stereo_control_frame, text="1.00")
        self.stereo_width_label.grid(row=2, column=0, pady=(2, 0))
        
        # === STATUS SECTION ===
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        # Status text
        self.status_text = tk.Text(status_frame, height=6, width=80, 
                                  font=("Courier", 9), wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for status
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, 
                                        command=self.status_text.yview)
        status_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.config(yscrollcommand=status_scrollbar.set)
        
        # === VISUALIZATION SECTION ===
        viz_frame = ttk.LabelFrame(main_frame, text="Visualization", padding="10")
        viz_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        
        # Simple canvas for waveform/levels
        self.viz_canvas = tk.Canvas(viz_frame, height=100, bg='black')
        self.viz_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame row weights
        main_frame.rowconfigure(4, weight=1)
        
        # Initial status
        self._update_status("Matchering Player initialized. Load a target file to begin.")
    
    def _load_target_file(self):
        """Load target audio file"""
        if not self.player:
            messagebox.showerror("Error", "Player not initialized")
            return
        
        filename = filedialog.askopenfilename(
            title="Select Target Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.aiff *.au"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("FLAC files", "*.flac"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self._update_status(f"Loading target file: {os.path.basename(filename)}")
            
            # Load in background thread
            def load_thread():
                success = self.player.load_file(filename)
                if success:
                    self.root.after(0, lambda: self._on_target_loaded(filename))
                else:
                    self.root.after(0, lambda: self._on_load_error("target", filename))
            
            threading.Thread(target=load_thread, daemon=True).start()
    
    def _load_reference_file(self):
        """Load reference audio file"""
        if not self.player:
            messagebox.showerror("Error", "Player not initialized")
            return
        
        filename = filedialog.askopenfilename(
            title="Select Reference Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.aiff *.au"),
                ("WAV files", "*.wav"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self._update_status(f"Loading reference file: {os.path.basename(filename)}")
            
            # Load in background thread
            def load_thread():
                success = self.player.load_reference_track(filename)
                if success:
                    self.root.after(0, lambda: self._on_reference_loaded(filename))
                else:
                    self.root.after(0, lambda: self._on_load_error("reference", filename))
            
            threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_target_loaded(self, filename):
        """Called when target file is loaded successfully"""
        basename = os.path.basename(filename)
        self.target_file_var.set(basename)
        self.target_label.config(foreground="black")
        
        # Update duration
        info = self.player.get_playback_info()
        self.duration = info.get('duration_seconds', 0)
        self.duration_var.set(self._format_time(self.duration))
        
        self._update_status(f"✅ Target loaded: {basename} ({self.duration:.1f}s)")
        self.play_button.config(state=tk.NORMAL)
    
    def _on_reference_loaded(self, filename):
        """Called when reference file is loaded successfully"""
        basename = os.path.basename(filename)
        self.reference_file_var.set(basename)
        self.reference_label.config(foreground="black")
        
        self._update_status(f"✅ Reference loaded: {basename}")
        self._update_status("🎛️  Level matching active - audio will be processed in real-time")
    
    def _on_load_error(self, file_type, filename):
        """Called when file loading fails"""
        basename = os.path.basename(filename)
        self._update_status(f"❌ Failed to load {file_type}: {basename}")
        messagebox.showerror("Load Error", f"Failed to load {file_type} file:\n{basename}")
    
    def _play_pause(self):
        """Toggle play/pause"""
        if not self.player:
            return
        
        state = self.player.get_state()
        
        if state == PlaybackState.PLAYING:
            self.player.pause()
        else:
            success = self.player.play()
            if not success:
                messagebox.showerror("Playback Error", "Failed to start playback")
    
    def _stop(self):
        """Stop playback"""
        if self.player:
            self.player.stop()
    
    def _on_seek(self, value):
        """Handle seek bar movement"""
        if self.is_seeking or not self.player or self.duration <= 0:
            return
        
        position = float(value) / 100.0 * self.duration
        self.player.seek(position)
    
    def _toggle_level_matching(self):
        """Toggle level matching effect"""
        if self.player:
            enabled = self.level_matching_var.get()
            self.player.set_effect_enabled('level_matching', enabled)
            status = "enabled" if enabled else "disabled"
            self._update_status(f"Level matching {status}")

    def _toggle_frequency_matching(self):
        """Toggle frequency matching effect"""
        if self.player:
            enabled = self.frequency_matching_var.get()
            self.player.set_effect_enabled('frequency_matching', enabled)
            status = "enabled" if enabled else "disabled"
            self._update_status(f"Frequency matching {status}")

    def _toggle_stereo_width(self):
        """Toggle stereo width control effect"""
        if self.player:
            enabled = self.stereo_width_var.get()
            self.player.set_effect_enabled('stereo_width', enabled)
            status = "enabled" if enabled else "disabled"
            self._update_status(f"Stereo width control {status}")

    def _on_stereo_width_change(self, value):
        """Handle stereo width slider changes"""
        if self.player:
            width = float(value)
            self.stereo_width_label.config(text=f"{width:.2f}")
            # Set manual stereo width via effect parameter
            self.player.set_effect_parameter('stereo_width', 'width', width)

    def _toggle_auto_mastering(self):
        """Toggle auto-mastering effect"""
        if self.player:
            enabled = self.auto_mastering_var.get()
            self.player.set_effect_enabled('auto_mastering', enabled)
            status = "enabled" if enabled else "disabled"
            self._update_status(f"🤖 Auto-mastering {status}")

            if enabled:
                self.auto_status_label.config(text="🧠 Analyzing...", foreground="blue")
            else:
                self.auto_status_label.config(text="❌ Disabled", foreground="gray")

    def _on_profile_change(self, event=None):
        """Handle auto-mastering profile selection"""
        if self.player:
            profile = self.auto_profile_var.get()
            self.player.set_effect_parameter('auto_mastering', 'profile', profile)
            self._update_status(f"🤖 Auto-mastering profile: {profile}")

            if profile == "adaptive":
                self.auto_status_label.config(text="🧠 Learning...", foreground="blue")
            else:
                self.auto_status_label.config(text=f"🎛️ {profile.title()}", foreground="green")

    def _toggle_bypass(self):
        """Toggle bypass all effects"""
        if self.player:
            bypass = self.bypass_var.get()
            self.player.set_effect_parameter('processor', 'bypass_all', bypass)
            status = "bypassed" if bypass else "active"
            self._update_status(f"All effects {status}")
    
    def _on_position_update(self, position):
        """Called when playback position updates"""
        self.current_position = position
        
        # Update GUI on main thread
        self.root.after(0, self._update_position_display)
    
    def _on_state_change(self, state):
        """Called when playback state changes"""
        # Update GUI on main thread
        self.root.after(0, lambda: self._update_playback_state(state))
    
    def _update_position_display(self):
        """Update position display"""
        if not self.is_seeking:
            self.position_var.set(self._format_time(self.current_position))
            
            if self.duration > 0:
                progress = (self.current_position / self.duration) * 100
                self.progress_var.set(progress)
    
    def _update_playback_state(self, state):
        """Update GUI based on playback state"""
        if state == PlaybackState.PLAYING:
            self.play_button.config(text="⏸ Pause")
        elif state in [PlaybackState.PAUSED, PlaybackState.STOPPED]:
            self.play_button.config(text="▶ Play")
        elif state == PlaybackState.LOADING:
            self.play_button.config(text="Loading...", state=tk.DISABLED)
        elif state == PlaybackState.ERROR:
            self.play_button.config(text="▶ Play", state=tk.DISABLED)
            self._update_status("❌ Playback error occurred")
        
        if state != PlaybackState.LOADING:
            self.play_button.config(state=tk.NORMAL if self.player else tk.DISABLED)
    
    def _update_status(self, message):
        """Add message to status display"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, formatted_message)
        self.status_text.see(tk.END)
    
    def _update_gui(self):
        """Periodic GUI updates"""
        if self.player:
            # Update DSP visualization
            self._update_visualization()
        
        # Schedule next update
        self.root.after(100, self._update_gui)  # 10 FPS
    
    def _update_visualization(self):
        """Update the visualization canvas"""
        try:
            # Get current DSP stats
            info = self.player.get_playback_info()
            dsp_stats = info.get('dsp', {})
            level_stats = dsp_stats.get('level_matching', {})
            
            # Clear canvas
            self.viz_canvas.delete("all")
            
            canvas_width = self.viz_canvas.winfo_width()
            canvas_height = self.viz_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # Draw level meters if we have data
            if level_stats.get('status') == 'active':
                mid_gain = level_stats.get('mid_gain_current', 1.0)
                side_gain = level_stats.get('side_gain_current', 1.0)
                
                # Convert to dB and normalize for display
                mid_db = 20 * np.log10(max(mid_gain, 1e-6))
                side_db = 20 * np.log10(max(side_gain, 1e-6))
                
                # Normalize to 0-1 range for display (-60dB to +20dB range)
                mid_norm = max(0, min(1, (mid_db + 60) / 80))
                side_norm = max(0, min(1, (side_db + 60) / 80))
                
                # Draw level bars
                bar_width = canvas_width // 2 - 20
                bar_height = canvas_height - 20
                
                # Mid channel bar
                mid_bar_height = int(bar_height * mid_norm)
                self.viz_canvas.create_rectangle(10, canvas_height - 10, 10 + bar_width, 
                                               canvas_height - 10 - mid_bar_height,
                                               fill="green", outline="white")
                self.viz_canvas.create_text(10 + bar_width // 2, canvas_height - 5, 
                                           text=f"Mid: {mid_db:.1f}dB", fill="white", anchor="s")
                
                # Side channel bar  
                side_bar_height = int(bar_height * side_norm)
                self.viz_canvas.create_rectangle(canvas_width // 2 + 10, canvas_height - 10,
                                               canvas_width // 2 + 10 + bar_width,
                                               canvas_height - 10 - side_bar_height,
                                               fill="blue", outline="white")
                self.viz_canvas.create_text(canvas_width // 2 + 10 + bar_width // 2, canvas_height - 5,
                                           text=f"Side: {side_db:.1f}dB", fill="white", anchor="s")
            else:
                # No processing active
                self.viz_canvas.create_text(canvas_width // 2, canvas_height // 2,
                                           text="No active processing", fill="gray")
                
        except Exception as e:
            pass  # Ignore visualization errors
    
    def _show_stats(self):
        """Show detailed processing statistics"""
        if not self.player:
            return
        
        info = self.player.get_playback_info()
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Processing Statistics")
        stats_window.geometry("600x400")
        
        text_widget = tk.Text(stats_window, wrap=tk.WORD, font=("Courier", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format stats nicely
        stats_text = "=== MATCHERING PLAYER STATISTICS ===\n\n"
        
        # Playback info
        stats_text += f"Playback State: {info.get('state', 'unknown')}\n"
        stats_text += f"Position: {info.get('position_seconds', 0):.2f}s\n"
        stats_text += f"Duration: {info.get('duration_seconds', 0):.2f}s\n"
        stats_text += f"File: {info.get('filename', 'None')}\n\n"
        
        # DSP stats
        dsp_stats = info.get('dsp', {})
        if dsp_stats:
            stats_text += "=== DSP PROCESSING ===\n"
            stats_text += f"Processing Active: {dsp_stats.get('processing_active', False)}\n"
            stats_text += f"CPU Usage: {dsp_stats.get('cpu_usage', 0) * 100:.1f}%\n"
            stats_text += f"Chunks Processed: {dsp_stats.get('chunks_processed', 0)}\n"
            stats_text += f"Performance Mode: {dsp_stats.get('performance_mode', False)}\n\n"
            
            # Level matching stats
            level_stats = dsp_stats.get('level_matching', {})
            if level_stats:
                stats_text += "=== LEVEL MATCHING ===\n"
                stats_text += f"Status: {level_stats.get('status', 'N/A')}\n"
                stats_text += f"Reference Loaded: {level_stats.get('reference_loaded', False)}\n"
                stats_text += f"Current Mid Gain: {level_stats.get('mid_gain_current', 1.0):.3f}\n"
                stats_text += f"Current Side Gain: {level_stats.get('side_gain_current', 1.0):.3f}\n"
        
        text_widget.insert(tk.END, stats_text)
        text_widget.config(state=tk.DISABLED)
    
    def _show_about(self):
        """Show about dialog"""
        about_text = """Matchering Player v0.1.0
        
Realtime Audio Matching and Mastering

Built with:
• Python & Tkinter
• Custom DSP processing engine
• Professional-grade level matching
• Real-time smoothing algorithms

Based on Matchering 2.0 by Sergree
        """
        
        messagebox.showinfo("About Matchering Player", about_text)
    
    def _format_time(self, seconds):
        """Format seconds as MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _on_closing(self):
        """Handle window closing"""
        if self.player:
            self.player.stop()
            if hasattr(self.player, 'audio_manager'):
                self.player.audio_manager.cleanup()
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        if not self.player:
            self._update_status("❌ Player initialization failed - limited functionality")
        
        self.root.mainloop()


def main():
    """Main entry point for the GUI application"""
    try:
        # Handle missing numpy for visualization
        global np
        try:
            import numpy as np
        except ImportError:
            print("⚠️  NumPy not available - visualization will be limited")
            np = None
        
        app = MatcheringPlayerGUI()
        app.run()
        
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
