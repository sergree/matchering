#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matchering Player GUI Demo
Demonstrates the complete GUI without requiring PyAudio
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tempfile
import os
from pathlib import Path

try:
    import soundfile as sf
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False


class MockMatcheringPlayer:
    """Mock player that simulates the interface without PyAudio"""
    
    def __init__(self):
        self.current_file = None
        self.reference_file = None
        self.duration = 0
        self.position = 0
        self.state = "stopped"
        self.processing_active = False
        
    def load_file(self, filename):
        self.current_file = filename
        self.duration = 120  # Mock 2 minutes
        return True
    
    def load_reference_track(self, filename):
        self.reference_file = filename
        self.processing_active = True
        return True
    
    def play(self):
        self.state = "playing"
        return True
    
    def pause(self):
        self.state = "paused"
        return True
    
    def stop(self):
        self.state = "stopped" 
        self.position = 0
        return True
    
    def seek(self, position):
        self.position = position
        return True
    
    def get_playback_info(self):
        return {
            'state': self.state,
            'position_seconds': self.position,
            'duration_seconds': self.duration,
            'filename': os.path.basename(self.current_file) if self.current_file else None,
            'dsp': {
                'processing_active': self.processing_active,
                'cpu_usage': 0.05,
                'chunks_processed': 1250,
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


class MatcheringPlayerDemo:
    """Demo GUI for Matchering Player"""
    
    def __init__(self):
        self.player = MockMatcheringPlayer()
        
        # Create demo audio files
        if HAS_AUDIO:
            self.demo_files = self._create_demo_files()
        else:
            self.demo_files = None
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Matchering Player Demo - GUI Showcase")
        self.root.geometry("900x700")
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self._create_widgets()
        self._start_demo_updates()
        
    def _create_demo_files(self):
        """Create temporary demo audio files"""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Create demo target (quiet)
            duration = 5.0
            sample_rate = 44100
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples, False)
            
            # Quiet track
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
    
    def _create_widgets(self):
        """Create the demo GUI"""
        
        # Main notebook for different sections
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === PLAYER TAB ===
        player_frame = ttk.Frame(notebook)
        notebook.add(player_frame, text="Player")
        
        # File section
        file_frame = ttk.LabelFrame(player_frame, text="Audio Files", padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="Target:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.target_var = tk.StringVar(value="No file loaded")
        ttk.Label(file_frame, textvariable=self.target_var).grid(row=0, column=1, sticky=tk.W)
        ttk.Button(file_frame, text="Load Demo Target", 
                  command=self._load_demo_target).grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(file_frame, text="Reference:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.reference_var = tk.StringVar(value="No reference loaded")
        ttk.Label(file_frame, textvariable=self.reference_var).grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        ttk.Button(file_frame, text="Load Demo Reference", 
                  command=self._load_demo_reference).grid(row=1, column=2, padx=(10, 0), pady=(10, 0))
        
        # Controls section
        controls_frame = ttk.LabelFrame(player_frame, text="Playback Controls", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Transport buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(pady=5)
        
        self.play_btn = ttk.Button(button_frame, text="▶ Play", command=self._demo_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="⏸ Pause", command=self._demo_pause).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⏹ Stop", command=self._demo_stop).pack(side=tk.LEFT, padx=5)
        
        # Position display
        pos_frame = ttk.Frame(controls_frame)
        pos_frame.pack(fill=tk.X, pady=5)
        
        self.position_var = tk.StringVar(value="00:00")
        ttk.Label(pos_frame, textvariable=self.position_var).pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Scale(pos_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                variable=self.progress_var, command=self._demo_seek)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.duration_var = tk.StringVar(value="02:00")
        ttk.Label(pos_frame, textvariable=self.duration_var).pack(side=tk.RIGHT)
        
        # Effects section
        effects_frame = ttk.LabelFrame(player_frame, text="DSP Effects", padding="10")
        effects_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.level_matching_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(effects_frame, text="Level Matching (Realtime)", 
                       variable=self.level_matching_var,
                       command=self._toggle_level_matching).pack(side=tk.LEFT)
        
        # === VISUALIZATION TAB ===
        viz_frame = ttk.Frame(notebook)
        notebook.add(viz_frame, text="Visualization")
        
        # Level meters
        levels_frame = ttk.LabelFrame(viz_frame, text="DSP Level Meters", padding="10")
        levels_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(levels_frame, height=200, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # === STATS TAB ===
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")
        
        stats_text_frame = ttk.LabelFrame(stats_frame, text="Processing Statistics", padding="10")
        stats_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_text_frame, font=("Courier", 10), wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        stats_scrollbar = ttk.Scrollbar(stats_text_frame, command=self.stats_text.yview)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.config(yscrollcommand=stats_scrollbar.set)
        
        # === STATUS BAR ===
        self.status_var = tk.StringVar(value="Ready - Load demo files to see Matchering Player in action!")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial update
        self._update_stats()
    
    def _load_demo_target(self):
        """Load demo target file"""
        if self.demo_files:
            success = self.player.load_file(self.demo_files["target"])
            if success:
                self.target_var.set("demo_target.wav")
                self.status_var.set("✅ Demo target loaded (quiet home recording simulation)")
        else:
            self.target_var.set("demo_target.wav (simulated)")
            self.player.load_file("demo_target.wav")
            self.status_var.set("✅ Demo target loaded (simulated - no audio files created)")
    
    def _load_demo_reference(self):
        """Load demo reference file"""
        if self.demo_files:
            success = self.player.load_reference_track(self.demo_files["reference"])
            if success:
                self.reference_var.set("demo_reference.wav")
                self.status_var.set("✅ Demo reference loaded - Level matching now active!")
        else:
            self.reference_var.set("demo_reference.wav (simulated)")
            self.player.load_reference_track("demo_reference.wav")
            self.status_var.set("✅ Demo reference loaded - Level matching now active!")
    
    def _demo_play(self):
        """Demo play functionality"""
        self.player.play()
        self.play_btn.config(text="⏸ Pause")
        self.status_var.set("▶️ Playing with real-time DSP processing")
    
    def _demo_pause(self):
        """Demo pause functionality"""
        self.player.pause()
        self.play_btn.config(text="▶ Play")
        self.status_var.set("⏸️ Paused")
    
    def _demo_stop(self):
        """Demo stop functionality"""
        self.player.stop()
        self.play_btn.config(text="▶ Play")
        self.progress_var.set(0)
        self.position_var.set("00:00")
        self.status_var.set("⏹️ Stopped")
    
    def _demo_seek(self, value):
        """Demo seek functionality"""
        position = float(value) / 100.0 * self.player.duration
        self.player.seek(position)
        self._update_position_display()
    
    def _toggle_level_matching(self):
        """Toggle level matching"""
        enabled = self.level_matching_var.get()
        self.player.set_effect_enabled('level_matching', enabled)
        status = "enabled" if enabled else "disabled"
        self.status_var.set(f"🎛️ Level matching {status}")
    
    def _update_position_display(self):
        """Update position display"""
        minutes = int(self.player.position // 60)
        seconds = int(self.player.position % 60)
        self.position_var.set(f"{minutes:02d}:{seconds:02d}")
        
        if self.player.duration > 0:
            progress = (self.player.position / self.player.duration) * 100
            self.progress_var.set(progress)
    
    def _update_visualization(self):
        """Update the visualization canvas"""
        try:
            info = self.player.get_playback_info()
            level_stats = info.get('dsp', {}).get('level_matching', {})
            
            # Clear canvas
            self.canvas.delete("all")
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            if level_stats.get('status') == 'active':
                mid_gain = level_stats.get('mid_gain_current', 1.0)
                side_gain = level_stats.get('side_gain_current', 1.0)
                
                # Convert to dB
                if HAS_AUDIO:
                    mid_db = 20 * np.log10(max(mid_gain, 1e-6))
                    side_db = 20 * np.log10(max(side_gain, 1e-6))
                else:
                    mid_db = 8.0  # Mock values
                    side_db = 5.1
                
                # Draw level bars
                bar_width = canvas_width // 2 - 40
                bar_height = canvas_height - 40
                
                # Normalize for display
                mid_norm = max(0, min(1, (mid_db + 60) / 80))
                side_norm = max(0, min(1, (side_db + 60) / 80))
                
                # Mid channel
                mid_bar_height = int(bar_height * mid_norm)
                self.canvas.create_rectangle(20, canvas_height - 20, 20 + bar_width,
                                           canvas_height - 20 - mid_bar_height,
                                           fill="lime", outline="white", width=2)
                self.canvas.create_text(20 + bar_width // 2, canvas_height - 5,
                                      text=f"Mid: {mid_db:.1f}dB", fill="white", anchor="s")
                
                # Side channel
                side_bar_height = int(bar_height * side_norm)
                self.canvas.create_rectangle(canvas_width // 2 + 20, canvas_height - 20,
                                           canvas_width // 2 + 20 + bar_width,
                                           canvas_height - 20 - side_bar_height,
                                           fill="cyan", outline="white", width=2)
                self.canvas.create_text(canvas_width // 2 + 20 + bar_width // 2, canvas_height - 5,
                                      text=f"Side: {side_db:.1f}dB", fill="white", anchor="s")
                
                # Labels
                self.canvas.create_text(20 + bar_width // 2, 15,
                                      text="Mid Channel (Center)", fill="white", anchor="n")
                self.canvas.create_text(canvas_width // 2 + 20 + bar_width // 2, 15,
                                      text="Side Channel (Width)", fill="white", anchor="n")
            else:
                # No processing
                self.canvas.create_text(canvas_width // 2, canvas_height // 2,
                                      text="Load reference track to see level matching visualization",
                                      fill="gray", anchor="center", font=("TkDefaultFont", 12))
                
        except Exception as e:
            pass  # Ignore errors
    
    def _update_stats(self):
        """Update statistics display"""
        info = self.player.get_playback_info()
        
        stats_text = "=== MATCHERING PLAYER DEMO STATISTICS ===\\n\\n"
        
        # Playback info
        stats_text += f"State: {info.get('state', 'unknown')}\\n"
        stats_text += f"Position: {info.get('position_seconds', 0):.1f}s\\n"
        stats_text += f"Duration: {info.get('duration_seconds', 0):.1f}s\\n"
        stats_text += f"File: {info.get('filename', 'None')}\\n\\n"
        
        # DSP info
        dsp = info.get('dsp', {})
        stats_text += "=== DSP PROCESSING ===\\n"
        stats_text += f"Processing Active: {dsp.get('processing_active', False)}\\n"
        stats_text += f"CPU Usage: {dsp.get('cpu_usage', 0) * 100:.1f}%\\n"
        stats_text += f"Chunks Processed: {dsp.get('chunks_processed', 0)}\\n"
        stats_text += f"Performance Mode: {dsp.get('performance_mode', False)}\\n\\n"
        
        # Level matching
        level_stats = dsp.get('level_matching', {})
        stats_text += "=== LEVEL MATCHING ===\\n"
        stats_text += f"Status: {level_stats.get('status', 'inactive')}\\n"
        stats_text += f"Reference Loaded: {level_stats.get('reference_loaded', False)}\\n"
        
        if level_stats.get('status') == 'active':
            mid_gain = level_stats.get('mid_gain_current', 1.0)
            side_gain = level_stats.get('side_gain_current', 1.0)
            if HAS_AUDIO:
                mid_db = 20 * np.log10(max(mid_gain, 1e-6))
                side_db = 20 * np.log10(max(side_gain, 1e-6))
            else:
                mid_db = 8.0
                side_db = 5.1
            
            stats_text += f"Mid Gain: {mid_gain:.2f} ({mid_db:.1f} dB)\\n"
            stats_text += f"Side Gain: {side_gain:.2f} ({side_db:.1f} dB)\\n"
            stats_text += f"Target Mid RMS: {level_stats.get('target_rms_mid_db', 0):.1f} dB\\n"
            stats_text += f"Target Side RMS: {level_stats.get('target_rms_side_db', 0):.1f} dB\\n"
        
        stats_text += "\\n=== DEMO NOTES ===\\n"
        stats_text += "This is a demonstration of the Matchering Player GUI.\\n"
        if not HAS_AUDIO:
            stats_text += "Audio processing libraries not available - showing simulated values.\\n"
        stats_text += "In the full version with PyAudio, you would hear the processed audio!\\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def _start_demo_updates(self):
        """Start demo update timer"""
        self._update_stats()
        self._update_visualization()
        
        # Simulate playback progression
        if self.player.state == "playing":
            self.player.position = min(self.player.position + 1, self.player.duration)
            self._update_position_display()
            
            if self.player.position >= self.player.duration:
                self._demo_stop()
        
        self.root.after(1000, self._start_demo_updates)  # Update every second
    
    def run(self):
        """Run the demo"""
        
        # Welcome message
        welcome = """
        🎉 Welcome to Matchering Player Demo!
        
        This demonstrates the complete GUI interface for the Matchering Player.
        
        What you can try:
        1. Click "Load Demo Target" and "Load Demo Reference"
        2. Press Play to simulate audio playback
        3. Check the Visualization tab to see level meters
        4. View Statistics tab for processing details
        5. Toggle Level Matching on/off
        
        In the full version with PyAudio installed, you would hear 
        real audio processing with professional-grade level matching!
        """
        
        messagebox.showinfo("Matchering Player Demo", welcome)
        
        self.root.mainloop()
        
        # Cleanup
        if self.demo_files and os.path.exists(self.demo_files["temp_dir"]):
            import shutil
            shutil.rmtree(self.demo_files["temp_dir"])


def main():
    """Run the GUI demo"""
    print("🚀 Starting Matchering Player GUI Demo...")
    
    try:
        app = MatcheringPlayerDemo()
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
