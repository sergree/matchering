#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auralis Modern GUI
~~~~~~~~~~~~~~~~~

Professional music player interface with real-time mastering capabilities

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

try:
    import auralis
    from auralis import EnhancedAudioPlayer, PlayerConfig
    from auralis.library import LibraryManager
    HAS_AURALIS = True
    print("✅ Auralis library loaded successfully")
except ImportError as e:
    print(f"⚠️  Auralis not available: {e}")
    HAS_AURALIS = False


class RealTimeVisualization(ctk.CTkFrame):
    """Real-time audio visualization with mastering metrics"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.setup_ui()
        self.reset_data()

    def setup_ui(self):
        """Setup visualization UI components"""
        # Title
        title = ctk.CTkLabel(self, text="🎛️ Real-time Mastering",
                           font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(10, 5))

        # Main visualization canvas
        self.canvas = ctk.CTkCanvas(self, height=200, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=5)

        # Metrics frame
        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=10, pady=5)

        # Level meters info
        self.rms_label = ctk.CTkLabel(metrics_frame, text="RMS: -∞ dB", font=ctk.CTkFont(size=11))
        self.rms_label.pack(side="left", padx=5)

        self.peak_label = ctk.CTkLabel(metrics_frame, text="Peak: -∞ dB", font=ctk.CTkFont(size=11))
        self.peak_label.pack(side="left", padx=5)

        self.dr_label = ctk.CTkLabel(metrics_frame, text="DR: -- dB", font=ctk.CTkFont(size=11))
        self.dr_label.pack(side="left", padx=5)

        self.quality_label = ctk.CTkLabel(metrics_frame, text="Quality: --", font=ctk.CTkFont(size=11))
        self.quality_label.pack(side="right", padx=5)

    def reset_data(self):
        """Reset visualization data"""
        self.level_history = []
        self.max_history = 100
        self.current_rms = 0.0
        self.current_peak = 0.0
        self.mastering_active = False

    def update_levels(self, rms_db: float, peak_db: float, mastering_active: bool = False,
                     dr_rating: float = None, quality_score: float = None):
        """Update level displays"""
        self.current_rms = rms_db
        self.current_peak = peak_db
        self.mastering_active = mastering_active

        # Add to history
        self.level_history.append({'rms': rms_db, 'peak': peak_db, 'time': time.time()})
        if len(self.level_history) > self.max_history:
            self.level_history.pop(0)

        # Update labels
        self.rms_label.configure(text=f"RMS: {rms_db:.1f} dB")
        self.peak_label.configure(text=f"Peak: {peak_db:.1f} dB")

        if dr_rating is not None:
            self.dr_label.configure(text=f"DR: {dr_rating:.1f} dB")

        if quality_score is not None:
            self.quality_label.configure(text=f"Quality: {quality_score:.1%}")

        # Redraw visualization
        self.draw_visualization()

    def draw_visualization(self):
        """Draw the real-time visualization"""
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        # Draw background grid
        self._draw_grid(width, height)

        # Draw level history as waveform
        if len(self.level_history) > 1:
            self._draw_level_history(width, height)

        # Draw current level meters
        self._draw_level_meters(width, height)

        # Draw mastering status
        self._draw_mastering_status(width, height)

    def _draw_grid(self, width: int, height: int):
        """Draw background grid"""
        # Horizontal grid lines (dB levels)
        db_levels = [-60, -40, -20, -10, -6, -3, 0]
        for db in db_levels:
            y = height - ((db + 60) / 60 * height * 0.8)
            if 0 <= y <= height:
                color = "#00ff00" if db == 0 else "#333333"
                width_val = 2 if db == 0 else 1
                self.canvas.create_line(0, y, width, y, fill=color, width=width_val)

                # dB labels
                self.canvas.create_text(width - 30, y - 5, text=f"{db}dB",
                                      fill="#666666", font=("Arial", 8))

    def _draw_level_history(self, width: int, height: int):
        """Draw level history as a waveform"""
        if len(self.level_history) < 2:
            return

        points_rms = []
        points_peak = []

        for i, data in enumerate(self.level_history):
            x = (i / len(self.level_history)) * width

            # Convert dB to pixel position (-60dB to 0dB range)
            rms_y = height - ((data['rms'] + 60) / 60 * height * 0.8)
            peak_y = height - ((data['peak'] + 60) / 60 * height * 0.8)

            points_rms.extend([x, max(0, min(height, rms_y))])
            points_peak.extend([x, max(0, min(height, peak_y))])

        # Draw RMS line (green)
        if len(points_rms) >= 4:
            self.canvas.create_line(points_rms, fill="#00ff88", width=2, smooth=True)

        # Draw peak line (yellow)
        if len(points_peak) >= 4:
            self.canvas.create_line(points_peak, fill="#ffff00", width=1, smooth=True)

    def _draw_level_meters(self, width: int, height: int):
        """Draw current level meters on the right side"""
        meter_width = 40
        meter_start_x = width - meter_width - 10
        meter_height = height * 0.8

        # RMS meter (green)
        rms_fill_height = max(0, (self.current_rms + 60) / 60 * meter_height)
        self.canvas.create_rectangle(meter_start_x, height - rms_fill_height,
                                   meter_start_x + 15, height,
                                   fill="#00ff88", outline="#004422")

        # Peak meter (yellow)
        peak_fill_height = max(0, (self.current_peak + 60) / 60 * meter_height)
        self.canvas.create_rectangle(meter_start_x + 20, height - peak_fill_height,
                                   meter_start_x + 35, height,
                                   fill="#ffff00", outline="#444400")

        # Meter labels
        self.canvas.create_text(meter_start_x + 7, height + 15, text="RMS",
                              fill="#00ff88", font=("Arial", 9, "bold"))
        self.canvas.create_text(meter_start_x + 27, height + 15, text="PEAK",
                              fill="#ffff00", font=("Arial", 9, "bold"))

    def _draw_mastering_status(self, width: int, height: int):
        """Draw mastering status indicator"""
        status_text = "🎯 MASTERING ACTIVE" if self.mastering_active else "⚪ MASTERING INACTIVE"
        color = "#00ff00" if self.mastering_active else "#666666"

        self.canvas.create_text(width // 2, 20, text=status_text,
                              fill=color, font=("Arial", 12, "bold"))


class LibraryBrowser(ctk.CTkFrame):
    """Library browser with search and filtering"""

    def __init__(self, master, player_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.player_callback = player_callback
        self.library_manager = None
        self.tracks_data = []

        self.setup_ui()

    def setup_ui(self):
        """Setup library browser UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        title = ctk.CTkLabel(header, text="📚 Music Library",
                           font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(side="left")

        # Search box
        self.search_entry = ctk.CTkEntry(header, placeholder_text="🔍 Search library...", width=200)
        self.search_entry.pack(side="right", padx=(10, 0))
        self.search_entry.bind('<KeyRelease>', self._on_search)

        # Control buttons
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=10, pady=5)

        scan_btn = ctk.CTkButton(controls, text="📁 Scan Folder", width=100, command=self._scan_folder)
        scan_btn.pack(side="left", padx=(0, 5))

        refresh_btn = ctk.CTkButton(controls, text="🔄 Refresh", width=80, command=self._refresh_library)
        refresh_btn.pack(side="left", padx=5)

        stats_btn = ctk.CTkButton(controls, text="📊 Stats", width=80, command=self._show_stats)
        stats_btn.pack(side="left", padx=5)

        # Playlist management button
        playlist_btn = ctk.CTkButton(controls, text="📋 Playlists", width=100, command=self._show_playlist_manager)
        playlist_btn.pack(side="left", padx=5)

        # Filter options
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Filter:").pack(side="left")

        self.filter_var = ctk.StringVar(value="All")
        filter_menu = ctk.CTkOptionMenu(filter_frame, variable=self.filter_var,
                                      values=["All", "Favorites", "Recent", "High Quality"],
                                      command=self._on_filter_change, width=120)
        filter_menu.pack(side="left", padx=(5, 0))

        # Tracks list with drag-and-drop support
        self.tracks_frame = ctk.CTkScrollableFrame(self, label_text="Tracks")
        self.tracks_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Configure drag-and-drop
        self._setup_drag_drop()

        # Status
        self.status_label = ctk.CTkLabel(self, text="No library loaded",
                                       font=ctk.CTkFont(size=11), text_color="#888888")
        self.status_label.pack(pady=5)

    def set_library_manager(self, library_manager):
        """Set the library manager and refresh display"""
        self.library_manager = library_manager
        self._refresh_library()

    def _setup_drag_drop(self):
        """Setup drag-and-drop functionality for music files"""
        self._drag_drop_available = False

        try:
            # Import tkinterdnd2 for drag-and-drop support
            import tkinterdnd2 as tkdnd

            # Try to setup drag-and-drop
            try:
                # Register the tracks_frame for drop events
                self.tracks_frame.drop_target_register(tkdnd.DND_FILES)
                self.tracks_frame.dnd_bind('<<Drop>>', self._handle_drop)

                # Add visual feedback
                self.tracks_frame.dnd_bind('<<DragEnter>>', self._on_drag_enter)
                self.tracks_frame.dnd_bind('<<DragLeave>>', self._on_drag_leave)

                self._drag_drop_available = True
                print("✅ Drag-and-drop functionality enabled")

            except Exception as dnd_error:
                print(f"Drag-and-drop setup failed: {dnd_error}")
                # Fall back to basic UI without drag-and-drop
                self._drag_drop_available = False

        except ImportError:
            print("tkinterdnd2 not available - drag-and-drop disabled")
            self._drag_drop_available = False

        # Always create some form of drop zone (even if just for visual appeal)
        self._create_drop_zone()

    def _create_drop_zone(self):
        """Create visual drop zone indicator"""
        self.drop_zone = ctk.CTkFrame(self.tracks_frame, fg_color="#2B2B2B",
                                    border_width=2, border_color="#1F538D")
        self.drop_zone.pack(fill="both", expand=True, padx=20, pady=20)

        # Adjust text based on drag-and-drop availability
        if self._drag_drop_available:
            text = "🎵 Drag & Drop Music Files Here\n\nSupported formats: MP3, FLAC, WAV, OGG, M4A"
        else:
            text = "🎵 Music Import Available\n\nUse 'Scan Folder' button to add music\nSupported formats: MP3, FLAC, WAV, OGG, M4A"

        drop_label = ctk.CTkLabel(self.drop_zone, text=text,
                                font=ctk.CTkFont(size=14),
                                text_color="#888888")
        drop_label.pack(expand=True)

    def _on_drag_enter(self, event):
        """Visual feedback when files are dragged over"""
        if hasattr(self, 'drop_zone'):
            self.drop_zone.configure(border_color="#4A9EFF", fg_color="#1E3A5F")

    def _on_drag_leave(self, event):
        """Reset visual feedback when drag leaves"""
        if hasattr(self, 'drop_zone'):
            self.drop_zone.configure(border_color="#1F538D", fg_color="#2B2B2B")

    def _handle_drop(self, event):
        """Handle dropped files"""
        try:
            files = event.data.split()
            audio_files = []

            # Filter for audio files
            audio_extensions = {'.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma'}

            for file_path in files:
                # Remove curly braces if present (Windows)
                file_path = file_path.strip('{}')

                if Path(file_path).suffix.lower() in audio_extensions:
                    audio_files.append(file_path)
                elif Path(file_path).is_dir():
                    # If directory dropped, scan for audio files
                    for ext in audio_extensions:
                        audio_files.extend(Path(file_path).rglob(f'*{ext}'))

            if audio_files:
                self._import_audio_files(audio_files)
            else:
                messagebox.showwarning("No Audio Files", "No supported audio files found in the dropped items.")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to process dropped files: {e}")
        finally:
            # Reset visual feedback
            self._on_drag_leave(None)

    def _import_audio_files(self, file_paths):
        """Import audio files into the library"""
        if not self.library_manager:
            messagebox.showerror("Error", "No library manager available")
            return

        # Show progress dialog
        progress_dialog = self._create_import_progress_dialog(len(file_paths))

        imported_count = 0
        failed_count = 0

        for i, file_path in enumerate(file_paths):
            try:
                # Update progress
                progress_dialog.update_progress(i + 1, f"Importing: {Path(file_path).name}")

                # Import the file
                if self._import_single_file(str(file_path)):
                    imported_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"Failed to import {file_path}: {e}")
                failed_count += 1

        progress_dialog.destroy()

        # Show results
        if imported_count > 0:
            messagebox.showinfo("Import Complete",
                              f"Successfully imported {imported_count} files.\n"
                              f"Failed: {failed_count}")
            self._refresh_library()
        else:
            messagebox.showerror("Import Failed",
                               f"Failed to import any files.\nFailed: {failed_count}")

    def _import_single_file(self, file_path):
        """Import a single audio file"""
        try:
            import soundfile as sf
            from pathlib import Path

            # Read audio file info
            info = sf.info(file_path)
            file_stat = Path(file_path).stat()

            # Basic track info
            track_info = {
                'filepath': file_path,
                'title': Path(file_path).stem,
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'format': info.format,
                'filesize': file_stat.st_size,
            }

            # Try to extract metadata using mutagen
            try:
                from mutagen import File as MutagenFile
                audio_file = MutagenFile(file_path)

                if audio_file:
                    # Extract common metadata
                    track_info.update({
                        'title': self._get_tag(audio_file, ['TIT2', 'TITLE', '\xa9nam']) or Path(file_path).stem,
                        'artists': self._get_artists(audio_file),
                        'album': self._get_tag(audio_file, ['TALB', 'ALBUM', '\xa9alb']),
                        'track_number': self._get_track_number(audio_file),
                        'year': self._get_year(audio_file),
                        'genres': self._get_genres(audio_file),
                    })

            except ImportError:
                print("Mutagen not available - using filename for metadata")
            except Exception as e:
                print(f"Failed to extract metadata from {file_path}: {e}")

            # Add to library
            track = self.library_manager.add_track(track_info)
            return track is not None

        except Exception as e:
            print(f"Failed to import {file_path}: {e}")
            return False

    def _get_tag(self, audio_file, keys):
        """Get tag value from audio file"""
        for key in keys:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None

    def _get_artists(self, audio_file):
        """Get artist list from audio file"""
        artist_keys = ['TPE1', 'ARTIST', '\xa9ART']
        for key in artist_keys:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list):
                    return [str(v) for v in value]
                elif value:
                    return [str(value)]
        return []

    def _get_track_number(self, audio_file):
        """Get track number from audio file"""
        track_keys = ['TRCK', 'TRACKNUMBER', 'trkn']
        for key in track_keys:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list) and value:
                    value = value[0]
                try:
                    # Handle "track/total" format
                    if '/' in str(value):
                        return int(str(value).split('/')[0])
                    return int(value)
                except (ValueError, TypeError):
                    pass
        return None

    def _get_year(self, audio_file):
        """Get year from audio file"""
        year_keys = ['TDRC', 'DATE', '\xa9day', 'YEAR']
        for key in year_keys:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list) and value:
                    value = value[0]
                try:
                    year_str = str(value)[:4]  # Take first 4 digits
                    return int(year_str)
                except (ValueError, TypeError):
                    pass
        return None

    def _get_genres(self, audio_file):
        """Get genre list from audio file"""
        genre_keys = ['TCON', 'GENRE', '\xa9gen']
        for key in genre_keys:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list):
                    return [str(v) for v in value]
                elif value:
                    return [str(value)]
        return []

    def _create_import_progress_dialog(self, total_files):
        """Create progress dialog for import operation"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Importing Audio Files")
        dialog.geometry("400x150")
        dialog.resizable(False, False)

        # Center on parent
        dialog.transient(self)
        dialog.grab_set()

        # Progress bar
        progress_label = ctk.CTkLabel(dialog, text="Preparing import...")
        progress_label.pack(pady=10)

        progress_bar = ctk.CTkProgressBar(dialog, width=350)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        file_label = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
        file_label.pack(pady=5)

        def update_progress(current, filename):
            progress = current / total_files
            progress_bar.set(progress)
            progress_label.configure(text=f"Importing {current}/{total_files} files...")
            file_label.configure(text=filename)
            dialog.update()

        dialog.update_progress = update_progress
        return dialog

    def _scan_folder(self):
        """Scan a folder for music files using the advanced scanner"""
        folder = filedialog.askdirectory(title="Select Music Folder")
        if folder and self.library_manager:
            # Show scanning options dialog
            self._show_scan_options_dialog(folder)

    def _show_scan_options_dialog(self, folder_path):
        """Show advanced scanning options dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Folder Scan Options")
        dialog.geometry("500x400")
        dialog.resizable(False, False)

        # Center on parent
        dialog.transient(self)
        dialog.grab_set()

        # Header
        header_label = ctk.CTkLabel(dialog, text=f"Scan Folder: {Path(folder_path).name}",
                                  font=ctk.CTkFont(size=16, weight="bold"))
        header_label.pack(pady=10)

        path_label = ctk.CTkLabel(dialog, text=folder_path,
                                font=ctk.CTkFont(size=11), text_color="#888888")
        path_label.pack(pady=(0, 10))

        # Options frame
        options_frame = ctk.CTkFrame(dialog)
        options_frame.pack(fill="x", padx=20, pady=10)

        # Recursive scanning
        self.recursive_var = ctk.BooleanVar(value=True)
        recursive_cb = ctk.CTkCheckBox(options_frame, text="Scan subdirectories recursively",
                                     variable=self.recursive_var)
        recursive_cb.pack(anchor="w", padx=10, pady=5)

        # Skip existing files
        self.skip_existing_var = ctk.BooleanVar(value=True)
        skip_cb = ctk.CTkCheckBox(options_frame, text="Skip files already in library",
                                variable=self.skip_existing_var)
        skip_cb.pack(anchor="w", padx=10, pady=5)

        # Check modifications
        self.check_modifications_var = ctk.BooleanVar(value=True)
        mod_cb = ctk.CTkCheckBox(options_frame, text="Check for file modifications",
                               variable=self.check_modifications_var)
        mod_cb.pack(anchor="w", padx=10, pady=5)

        # Progress area
        progress_frame = ctk.CTkFrame(dialog)
        progress_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.scan_progress_label = ctk.CTkLabel(progress_frame, text="Ready to scan...")
        self.scan_progress_label.pack(pady=10)

        self.scan_progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        self.scan_progress_bar.pack(pady=10)
        self.scan_progress_bar.set(0)

        self.scan_details_text = ctk.CTkTextbox(progress_frame, height=100, width=400)
        self.scan_details_text.pack(pady=10, fill="both", expand=True)

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel",
                                 command=dialog.destroy, width=100)
        cancel_btn.pack(side="right", padx=(5, 0))

        self.scan_btn = ctk.CTkButton(button_frame, text="Start Scan",
                                    command=lambda: self._start_folder_scan(folder_path, dialog),
                                    width=100)
        self.scan_btn.pack(side="right")

    def _start_folder_scan(self, folder_path, dialog):
        """Start the folder scanning process"""
        try:
            # Disable scan button
            self.scan_btn.configure(state="disabled", text="Scanning...")

            # Get options
            recursive = self.recursive_var.get()
            skip_existing = self.skip_existing_var.get()
            check_modifications = self.check_modifications_var.get()

            # Update UI
            self.scan_progress_label.configure(text="Starting scan...")
            self.scan_details_text.delete("1.0", "end")
            self.scan_details_text.insert("1.0", f"Scanning: {folder_path}\nOptions: recursive={recursive}, skip_existing={skip_existing}\n\n")

            # Start scan in background thread
            import threading

            def scan_worker():
                try:
                    # Set up progress callback
                    def progress_callback(progress_data):
                        # Update UI from background thread
                        dialog.after(0, lambda: self._update_scan_progress(progress_data, dialog))

                    # Create scanner and set callback
                    from auralis.library.scanner import LibraryScanner
                    scanner = LibraryScanner(self.library_manager)
                    scanner.set_progress_callback(progress_callback)

                    # Run scan
                    result = scanner.scan_single_directory(
                        folder_path,
                        recursive=recursive,
                        skip_existing=skip_existing,
                        check_modifications=check_modifications
                    )

                    # Update UI with results
                    dialog.after(0, lambda: self._finish_scan(result, dialog))

                except Exception as e:
                    error_msg = f"Scan failed: {e}"
                    dialog.after(0, lambda: self._scan_error(error_msg, dialog))

            thread = threading.Thread(target=scan_worker, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("Scan Error", f"Failed to start scan: {e}")
            dialog.destroy()

    def _update_scan_progress(self, progress_data, dialog):
        """Update scan progress in UI"""
        try:
            stage = progress_data.get('stage', 'unknown')

            if stage == 'discovering':
                directory = progress_data.get('directory', '')
                files_found = progress_data.get('files_found', 0)
                total_found = progress_data.get('total_found', 0)

                self.scan_progress_label.configure(text=f"Discovering files... {total_found} found")
                self.scan_details_text.insert("end", f"Found {files_found} files in {Path(directory).name}\n")

            elif stage == 'processing':
                progress = progress_data.get('progress', 0)
                processed = progress_data.get('processed', 0)
                added = progress_data.get('added', 0)
                failed = progress_data.get('failed', 0)

                self.scan_progress_bar.set(progress)
                self.scan_progress_label.configure(text=f"Processing files... {processed} processed, {added} added")

                if processed % 10 == 0:  # Update every 10 files to avoid spam
                    self.scan_details_text.insert("end", f"Processed: {processed}, Added: {added}, Failed: {failed}\n")
                    self.scan_details_text.see("end")

            dialog.update()

        except Exception as e:
            print(f"Progress update error: {e}")

    def _finish_scan(self, result, dialog):
        """Handle scan completion"""
        try:
            self.scan_progress_bar.set(1.0)
            self.scan_progress_label.configure(text="Scan completed!")

            results_text = f"""
Scan Results:
• Files found: {result.files_found}
• Files processed: {result.files_processed}
• Files added: {result.files_added}
• Files updated: {result.files_updated}
• Files skipped: {result.files_skipped}
• Files failed: {result.files_failed}
• Scan time: {result.scan_time:.1f} seconds

Scan completed successfully!
"""

            self.scan_details_text.insert("end", results_text)
            self.scan_details_text.see("end")

            # Re-enable button and change text
            self.scan_btn.configure(state="normal", text="Close")
            self.scan_btn.configure(command=lambda: [self._refresh_library(), dialog.destroy()])

            # Show completion message
            if result.files_added > 0:
                messagebox.showinfo("Scan Complete",
                                  f"Successfully added {result.files_added} new tracks to library!")

        except Exception as e:
            print(f"Scan completion error: {e}")

    def _scan_error(self, error_msg, dialog):
        """Handle scan error"""
        self.scan_progress_label.configure(text="Scan failed!")
        self.scan_details_text.insert("end", f"\nERROR: {error_msg}\n")
        self.scan_details_text.see("end")

        self.scan_btn.configure(state="normal", text="Close")
        self.scan_btn.configure(command=dialog.destroy)

        messagebox.showerror("Scan Error", error_msg)

    def _show_playlist_manager(self):
        """Show playlist management dialog"""
        if not self.library_manager:
            messagebox.showerror("Error", "No library manager available")
            return

        # Create playlist manager dialog
        dialog = PlaylistManagerDialog(self, self.library_manager)
        dialog.show()

    def _refresh_library(self):
        """Refresh the library display"""
        if not self.library_manager:
            self.status_label.configure(text="No library manager available")
            return

        try:
            # Get all tracks
            stats = self.library_manager.get_library_stats()
            if stats['total_tracks'] == 0:
                self.status_label.configure(text="No tracks in library")
                return

            # For now, get recent tracks as example
            tracks = self.library_manager.get_recent_tracks(limit=50)
            self.tracks_data = tracks
            self._update_tracks_display(tracks)

            self.status_label.configure(text=f"{len(tracks)} tracks loaded")

        except Exception as e:
            self.status_label.configure(text=f"Error loading library: {e}")

    def _update_tracks_display(self, tracks):
        """Update the tracks display"""
        # Clear existing tracks
        for widget in self.tracks_frame.winfo_children():
            widget.destroy()

        # Add tracks
        for track in tracks:
            self._add_track_widget(track)

    def _add_track_widget(self, track):
        """Add a single track widget"""
        track_frame = ctk.CTkFrame(self.tracks_frame)
        track_frame.pack(fill="x", pady=2)

        # Track info
        info_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
        info_frame.pack(fill="x", side="left", expand=True, padx=10, pady=5)

        # Title and artist
        title_text = track.title or "Unknown Title"
        artist_text = track.artists[0].name if track.artists else "Unknown Artist"

        title_label = ctk.CTkLabel(info_frame, text=title_text,
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 anchor="w")
        title_label.pack(anchor="w")

        artist_label = ctk.CTkLabel(info_frame, text=artist_text,
                                  font=ctk.CTkFont(size=10),
                                  text_color="#888888", anchor="w")
        artist_label.pack(anchor="w")

        # Duration and quality
        duration = f"{track.duration:.0f}s" if track.duration else "Unknown"
        quality = f"Q: {track.mastering_quality:.1%}" if track.mastering_quality else "Q: --"

        details = ctk.CTkLabel(info_frame, text=f"{duration} • {quality}",
                             font=ctk.CTkFont(size=9),
                             text_color="#666666", anchor="w")
        details.pack(anchor="w")

        # Play button
        play_btn = ctk.CTkButton(track_frame, text="▶️", width=40, height=30,
                               command=lambda t=track: self._play_track(t))
        play_btn.pack(side="right", padx=10, pady=5)

    def _play_track(self, track):
        """Play a selected track"""
        if self.player_callback:
            self.player_callback(track.id)

    def _on_search(self, event):
        """Handle search input"""
        query = self.search_entry.get().strip()
        if not query:
            self._refresh_library()
            return

        if self.library_manager:
            try:
                results = self.library_manager.search_tracks(query, limit=50)
                self._update_tracks_display(results)
                self.status_label.configure(text=f"{len(results)} tracks found")
            except Exception as e:
                self.status_label.configure(text=f"Search error: {e}")

    def _on_filter_change(self, value):
        """Handle filter change"""
        if not self.library_manager:
            return

        try:
            if value == "All":
                tracks = self.library_manager.get_recent_tracks(limit=50)
            elif value == "Favorites":
                tracks = self.library_manager.get_favorite_tracks(limit=50)
            elif value == "Recent":
                tracks = self.library_manager.get_recent_tracks(limit=50)
            elif value == "High Quality":
                # This would filter by mastering quality
                tracks = self.library_manager.get_recent_tracks(limit=50)
            else:
                tracks = []

            self._update_tracks_display(tracks)
            self.status_label.configure(text=f"{len(tracks)} tracks ({value.lower()})")

        except Exception as e:
            self.status_label.configure(text=f"Filter error: {e}")

    def _show_stats(self):
        """Show library statistics"""
        if not self.library_manager:
            messagebox.showinfo("Stats", "No library manager available")
            return

        try:
            stats = self.library_manager.get_library_stats()

            stats_text = f"""📊 Library Statistics

🎵 Total Tracks: {stats['total_tracks']}
🎤 Total Artists: {stats['total_artists']}
💿 Total Albums: {stats['total_albums']}
🎼 Total Genres: {stats['total_genres']}
📋 Total Playlists: {stats['total_playlists']}

⏱️ Total Duration: {stats.get('total_duration_formatted', 'Unknown')}
💾 Total Size: {stats.get('total_filesize_gb', 0):.1f} GB

🎛️ Audio Quality:
   Average DR: {stats.get('avg_dr_rating', 0):.1f} dB
   Average LUFS: {stats.get('avg_lufs', 0):.1f}
   Average Quality: {stats.get('avg_mastering_quality', 0):.1%}
"""

            messagebox.showinfo("Library Statistics", stats_text)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get stats: {e}")


class PlayerControls(ctk.CTkFrame):
    """Main player controls and transport"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.player = None
        self.seeking = False

        self.setup_ui()

    def setup_ui(self):
        """Setup player controls UI"""
        # Current track info
        track_info_frame = ctk.CTkFrame(self)
        track_info_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.track_title = ctk.CTkLabel(track_info_frame, text="No track loaded",
                                      font=ctk.CTkFont(size=14, weight="bold"))
        self.track_title.pack(pady=5)

        self.track_artist = ctk.CTkLabel(track_info_frame, text="",
                                       font=ctk.CTkFont(size=11), text_color="#888888")
        self.track_artist.pack()

        # Transport controls
        transport_frame = ctk.CTkFrame(self, fg_color="transparent")
        transport_frame.pack(pady=10)

        self.prev_btn = ctk.CTkButton(transport_frame, text="⏮️", width=50, height=40,
                                    command=self._previous_track)
        self.prev_btn.pack(side="left", padx=5)

        self.play_btn = ctk.CTkButton(transport_frame, text="▶️", width=60, height=40,
                                    command=self._toggle_play,
                                    font=ctk.CTkFont(size=16))
        self.play_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(transport_frame, text="⏹️", width=50, height=40,
                                    command=self._stop)
        self.stop_btn.pack(side="left", padx=5)

        self.next_btn = ctk.CTkButton(transport_frame, text="⏭️", width=50, height=40,
                                    command=self._next_track)
        self.next_btn.pack(side="left", padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.position_label = ctk.CTkLabel(progress_frame, text="0:00", width=40)
        self.position_label.pack(side="left")

        self.progress_slider = ctk.CTkSlider(progress_frame, from_=0, to=100,
                                           command=self._on_seek)
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=10)

        self.duration_label = ctk.CTkLabel(progress_frame, text="0:00", width=40)
        self.duration_label.pack(side="right")

        # Volume and settings
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(controls_frame, text="🔊").pack(side="left")

        self.volume_slider = ctk.CTkSlider(controls_frame, from_=0, to=1,
                                         command=self._on_volume_change, width=100)
        self.volume_slider.set(0.8)
        self.volume_slider.pack(side="left", padx=(5, 10))

        self.volume_label = ctk.CTkLabel(controls_frame, text="80%", width=40)
        self.volume_label.pack(side="left")

        # Shuffle and repeat
        shuffle_btn = ctk.CTkButton(controls_frame, text="🔀", width=40, height=30,
                                  command=self._toggle_shuffle)
        shuffle_btn.pack(side="right", padx=5)

        repeat_btn = ctk.CTkButton(controls_frame, text="🔁", width=40, height=30,
                                 command=self._toggle_repeat)
        repeat_btn.pack(side="right", padx=5)

    def set_player(self, player):
        """Set the audio player"""
        self.player = player

    def update_info(self, info: Dict[str, Any]):
        """Update player info display"""
        # Track info
        library_info = info.get('library', {})
        track_data = library_info.get('current_track_data')

        if track_data:
            self.track_title.configure(text=track_data.get('title', 'Unknown'))
            artists = track_data.get('artists', [])
            artist_text = artists[0] if artists else 'Unknown Artist'
            self.track_artist.configure(text=artist_text)
        else:
            self.track_title.configure(text="No track loaded")
            self.track_artist.configure(text="")

        # Progress
        if not self.seeking:
            position = info.get('position_seconds', 0)
            duration = info.get('duration_seconds', 0)

            pos_min, pos_sec = divmod(int(position), 60)
            dur_min, dur_sec = divmod(int(duration), 60)

            self.position_label.configure(text=f"{pos_min}:{pos_sec:02d}")
            self.duration_label.configure(text=f"{dur_min}:{dur_sec:02d}")

            if duration > 0:
                progress = (position / duration) * 100
                self.progress_slider.set(progress)

        # Play button state
        state = info.get('state', 'stopped')
        if state == 'playing':
            self.play_btn.configure(text="⏸️")
        else:
            self.play_btn.configure(text="▶️")

    def _toggle_play(self):
        """Toggle play/pause"""
        if self.player:
            info = self.player.get_playback_info()
            if info.get('state') == 'playing':
                self.player.pause()
            else:
                self.player.play()

    def _stop(self):
        """Stop playback"""
        if self.player:
            self.player.stop()

    def _previous_track(self):
        """Previous track"""
        if self.player:
            self.player.previous_track()

    def _next_track(self):
        """Next track"""
        if self.player:
            self.player.next_track()

    def _on_seek(self, value):
        """Handle seek"""
        if not self.seeking and self.player:
            self.seeking = True
            info = self.player.get_playback_info()
            duration = info.get('duration_seconds', 0)
            position = (float(value) / 100.0) * duration
            self.player.seek(position)
            self.seeking = False

    def _on_volume_change(self, value):
        """Handle volume change"""
        self.volume_label.configure(text=f"{int(float(value) * 100)}%")
        # Volume control would be implemented here

    def _toggle_shuffle(self):
        """Toggle shuffle mode"""
        if self.player:
            # Shuffle toggle would be implemented here
            pass

    def _toggle_repeat(self):
        """Toggle repeat mode"""
        if self.player:
            # Repeat toggle would be implemented here
            pass


class MasteringControls(ctk.CTkFrame):
    """Mastering controls and DSP settings"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.player = None

        self.setup_ui()

    def setup_ui(self):
        """Setup mastering controls UI"""
        # Header
        header = ctk.CTkLabel(self, text="🎛️ Mastering Controls",
                            font=ctk.CTkFont(size=16, weight="bold"))
        header.pack(pady=(10, 5))

        # Level matching
        level_frame = ctk.CTkFrame(self)
        level_frame.pack(fill="x", padx=10, pady=5)

        self.level_matching_switch = ctk.CTkSwitch(level_frame, text="🎯 Real-time Level Matching")
        self.level_matching_switch.pack(pady=10)

        # Auto mastering
        auto_frame = ctk.CTkFrame(self)
        auto_frame.pack(fill="x", padx=10, pady=5)

        self.auto_mastering_switch = ctk.CTkSwitch(auto_frame, text="🤖 Auto Mastering")
        self.auto_mastering_switch.pack(pady=5)

        # Mastering profile
        profile_frame = ctk.CTkFrame(auto_frame, fg_color="transparent")
        profile_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(profile_frame, text="Profile:").pack(side="left")

        self.profile_var = ctk.StringVar(value="balanced")
        self.profile_menu = ctk.CTkOptionMenu(profile_frame, variable=self.profile_var,
                                            values=["balanced", "warm", "bright", "punchy"],
                                            command=self._on_profile_change)
        self.profile_menu.pack(side="left", padx=(10, 0))

        # Reference selection
        ref_frame = ctk.CTkFrame(self)
        ref_frame.pack(fill="x", padx=10, pady=5)

        ref_header = ctk.CTkLabel(ref_frame, text="🎯 Reference Track",
                                font=ctk.CTkFont(size=12, weight="bold"))
        ref_header.pack(pady=(5, 0))

        self.auto_ref_switch = ctk.CTkSwitch(ref_frame, text="Auto-select reference")
        self.auto_ref_switch.pack(pady=5)

        ref_btn = ctk.CTkButton(ref_frame, text="📁 Load Reference",
                              command=self._load_reference)
        ref_btn.pack(pady=5)

        self.ref_status = ctk.CTkLabel(ref_frame, text="No reference loaded",
                                     font=ctk.CTkFont(size=10), text_color="#888888")
        self.ref_status.pack()

        # Performance settings
        perf_frame = ctk.CTkFrame(self)
        perf_frame.pack(fill="x", padx=10, pady=5)

        perf_header = ctk.CTkLabel(perf_frame, text="⚡ Performance",
                                 font=ctk.CTkFont(size=12, weight="bold"))
        perf_header.pack(pady=(5, 0))

        self.performance_mode_switch = ctk.CTkSwitch(perf_frame, text="Performance mode")
        self.performance_mode_switch.pack(pady=5)

        # CPU usage display
        self.cpu_label = ctk.CTkLabel(perf_frame, text="CPU: 0%",
                                    font=ctk.CTkFont(size=10))
        self.cpu_label.pack()

    def set_player(self, player):
        """Set the audio player"""
        self.player = player

    def update_processing_info(self, processing_info: Dict[str, Any]):
        """Update processing information display"""
        # Performance info
        performance = processing_info.get('performance', {})
        cpu_usage = performance.get('cpu_usage', 0) * 100
        self.cpu_label.configure(text=f"CPU: {cpu_usage:.1f}%")

        # Effects status
        effects = processing_info.get('effects', {})

        level_matching = effects.get('level_matching', {})
        self.level_matching_switch.configure(state="normal" if level_matching.get('enabled') else "disabled")

        auto_mastering = effects.get('auto_mastering', {})
        self.auto_mastering_switch.configure(state="normal" if auto_mastering.get('enabled') else "disabled")

        # Reference status
        if level_matching.get('reference_loaded'):
            self.ref_status.configure(text="✅ Reference active", text_color="#00ff88")
        else:
            self.ref_status.configure(text="No reference loaded", text_color="#888888")

    def _on_profile_change(self, value):
        """Handle mastering profile change"""
        if self.player:
            self.player.set_auto_master_profile(value)

    def _load_reference(self):
        """Load reference track"""
        filename = filedialog.askopenfilename(
            title="Select Reference Track",
            filetypes=[
                ("Audio files", "*.wav *.flac *.mp3 *.m4a *.aac"),
                ("All files", "*.*")
            ]
        )

        if filename and self.player:
            success = self.player.load_reference(filename)
            if success:
                ref_name = os.path.basename(filename)
                self.ref_status.configure(text=f"✅ {ref_name}", text_color="#00ff88")
            else:
                self.ref_status.configure(text="❌ Failed to load", text_color="#ff4444")


class AuralisGUI(ctk.CTk):
    """Main Auralis GUI Application"""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("🎵 Auralis - Professional Audio Mastering Player")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        # Initialize components
        self.player = None
        self.library_manager = None
        self.update_running = False

        # Create interface
        self.create_interface()

        # Initialize audio system
        self.initialize_audio_system()

        # Start update loop
        self.start_update_loop()

    def create_interface(self):
        """Create the main interface"""
        # Main content area with sidebar
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left sidebar (library and controls)
        sidebar = ctk.CTkFrame(main_frame, width=400)
        sidebar.pack(side="left", fill="y", padx=(0, 5))
        sidebar.pack_propagate(False)

        # Library browser
        self.library_browser = LibraryBrowser(sidebar, player_callback=self._play_track_from_library)
        self.library_browser.pack(fill="both", expand=True, pady=(0, 5))

        # Mastering controls
        self.mastering_controls = MasteringControls(sidebar, height=300)
        self.mastering_controls.pack(fill="x")
        self.mastering_controls.pack_propagate(False)

        # Right main area (player and visualization)
        main_area = ctk.CTkFrame(main_frame)
        main_area.pack(side="right", fill="both", expand=True)

        # Player controls
        self.player_controls = PlayerControls(main_area)
        self.player_controls.pack(fill="x", padx=5, pady=(5, 0))

        # Visualization
        self.visualization = RealTimeVisualization(main_area)
        self.visualization.pack(fill="both", expand=True, padx=5, pady=5)

        # Status bar
        self.status_bar = ctk.CTkLabel(self, text="🎵 Auralis ready - Load a track to begin",
                                     font=ctk.CTkFont(size=11),
                                     fg_color="#2b2b2b", corner_radius=0)
        self.status_bar.pack(side="bottom", fill="x")

    def initialize_audio_system(self):
        """Initialize the audio system"""
        if not HAS_AURALIS:
            self.status_bar.configure(text="❌ Auralis library not available - Running in demo mode")
            return

        try:
            # Create library manager
            self.library_manager = LibraryManager()
            self.library_browser.set_library_manager(self.library_manager)

            # Create enhanced player
            config = PlayerConfig(
                sample_rate=44100,
                buffer_size=2048,
                enable_level_matching=True,
                enable_auto_mastering=True
            )

            self.player = EnhancedAudioPlayer(config, self.library_manager)
            self.player_controls.set_player(self.player)
            self.mastering_controls.set_player(self.player)

            self.status_bar.configure(text="✅ Auralis audio system initialized successfully")

        except Exception as e:
            self.status_bar.configure(text=f"❌ Failed to initialize audio system: {e}")

    def _play_track_from_library(self, track_id: int):
        """Play a track from the library"""
        if self.player:
            success = self.player.load_track_from_library(track_id)
            if success:
                self.player.play()
                self.status_bar.configure(text=f"🎵 Playing track from library (ID: {track_id})")
            else:
                self.status_bar.configure(text=f"❌ Failed to load track {track_id}")

    def start_update_loop(self):
        """Start the GUI update loop"""
        self.update_running = True
        self.update_gui()

    def update_gui(self):
        """Update GUI with current player state"""
        if self.update_running and self.player:
            try:
                # Get player info
                info = self.player.get_playback_info()

                # Update controls
                self.player_controls.update_info(info)

                # Update mastering controls
                processing_info = info.get('processing', {})
                self.mastering_controls.update_processing_info(processing_info)

                # Update visualization
                # For now, simulate some levels - real implementation would get from audio stream
                import random
                rms_db = -20 + random.random() * 15 if info.get('is_playing') else -60
                peak_db = rms_db + random.random() * 5
                mastering_active = processing_info.get('effects', {}).get('level_matching', {}).get('enabled', False)

                self.visualization.update_levels(rms_db, peak_db, mastering_active,
                                               dr_rating=12.5, quality_score=0.85)

            except Exception as e:
                print(f"GUI update error: {e}")

        # Schedule next update
        if self.update_running:
            self.after(100, self.update_gui)  # 10 FPS

    def on_closing(self):
        """Handle window closing"""
        self.update_running = False
        if self.player:
            self.player.cleanup()
        self.destroy()


class PlaylistManagerDialog:
    """Comprehensive playlist management dialog"""

    def __init__(self, parent, library_manager):
        self.parent = parent
        self.library_manager = library_manager
        self.dialog = None
        self.current_playlist = None
        self.all_tracks = []

    def show(self):
        """Show the playlist manager dialog"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Playlist Manager")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)

        # Center on parent
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.refresh_playlists()
        self.load_all_tracks()

    def setup_ui(self):
        """Setup the playlist management UI"""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Playlist list
        left_panel = ctk.CTkFrame(main_frame)
        left_panel.pack(side="left", fill="y", padx=(0, 5))

        # Playlist controls
        playlist_controls = ctk.CTkFrame(left_panel)
        playlist_controls.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(playlist_controls, text="Playlists",
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)

        # Playlist action buttons
        btn_frame = ctk.CTkFrame(playlist_controls, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)

        new_btn = ctk.CTkButton(btn_frame, text="➕ New", width=70,
                              command=self._create_new_playlist)
        new_btn.pack(side="left", padx=(0, 5))

        edit_btn = ctk.CTkButton(btn_frame, text="✏️ Edit", width=70,
                               command=self._edit_playlist)
        edit_btn.pack(side="left", padx=(0, 5))

        delete_btn = ctk.CTkButton(btn_frame, text="🗑️ Delete", width=70,
                                 command=self._delete_playlist)
        delete_btn.pack(side="left")

        # Playlist list
        self.playlist_listbox = ctk.CTkScrollableFrame(left_panel, width=250, height=400)
        self.playlist_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right panel - Playlist content
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Playlist details header
        details_header = ctk.CTkFrame(right_panel)
        details_header.pack(fill="x", padx=10, pady=10)

        self.playlist_title = ctk.CTkLabel(details_header, text="Select a playlist",
                                         font=ctk.CTkFont(size=16, weight="bold"))
        self.playlist_title.pack(side="left")

        # Track management controls
        track_controls = ctk.CTkFrame(right_panel)
        track_controls.pack(fill="x", padx=10, pady=(0, 10))

        add_tracks_btn = ctk.CTkButton(track_controls, text="➕ Add Tracks",
                                     command=self._show_add_tracks_dialog)
        add_tracks_btn.pack(side="left", padx=(0, 5))

        remove_track_btn = ctk.CTkButton(track_controls, text="➖ Remove",
                                       command=self._remove_selected_track)
        remove_track_btn.pack(side="left", padx=(0, 5))

        clear_btn = ctk.CTkButton(track_controls, text="🗑️ Clear All",
                                command=self._clear_playlist)
        clear_btn.pack(side="left")

        # Playlist tracks
        self.tracks_frame = ctk.CTkScrollableFrame(right_panel, label_text="Playlist Tracks")
        self.tracks_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        close_btn = ctk.CTkButton(bottom_frame, text="Close", command=self.dialog.destroy)
        close_btn.pack(side="right")

        play_playlist_btn = ctk.CTkButton(bottom_frame, text="▶️ Play Playlist",
                                        command=self._play_playlist)
        play_playlist_btn.pack(side="right", padx=(0, 10))

    def refresh_playlists(self):
        """Refresh the playlist list"""
        try:
            # Clear existing playlist items
            for widget in self.playlist_listbox.winfo_children():
                widget.destroy()

            # Get all playlists
            playlists = self.library_manager.get_all_playlists()

            if not playlists:
                no_playlists_label = ctk.CTkLabel(self.playlist_listbox,
                                                text="No playlists yet\nCreate one to get started!",
                                                text_color="#888888")
                no_playlists_label.pack(pady=20)
                return

            # Create playlist items
            for playlist in playlists:
                self._create_playlist_item(playlist)

        except Exception as e:
            print(f"Error refreshing playlists: {e}")

    def _create_playlist_item(self, playlist):
        """Create a playlist item widget"""
        playlist_frame = ctk.CTkFrame(self.playlist_listbox)
        playlist_frame.pack(fill="x", padx=5, pady=2)

        # Playlist info
        info_frame = ctk.CTkFrame(playlist_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=8)

        name_label = ctk.CTkLabel(info_frame, text=playlist.name,
                                font=ctk.CTkFont(size=14, weight="bold"))
        name_label.pack(anchor="w")

        # Track count and duration
        track_count = len(playlist.tracks) if playlist.tracks else 0
        total_duration = sum(track.duration for track in playlist.tracks if track.duration) if playlist.tracks else 0
        duration_min = int(total_duration // 60)

        details_text = f"{track_count} tracks • {duration_min} min"
        details_label = ctk.CTkLabel(info_frame, text=details_text,
                                   font=ctk.CTkFont(size=11), text_color="#888888")
        details_label.pack(anchor="w")

        # Description if available
        if playlist.description:
            desc_label = ctk.CTkLabel(info_frame, text=playlist.description[:50] + "..." if len(playlist.description) > 50 else playlist.description,
                                    font=ctk.CTkFont(size=10), text_color="#666666")
            desc_label.pack(anchor="w", pady=(2, 0))

        # Click handler
        def select_playlist():
            self._select_playlist(playlist)

        playlist_frame.bind("<Button-1>", lambda e: select_playlist())
        info_frame.bind("<Button-1>", lambda e: select_playlist())
        name_label.bind("<Button-1>", lambda e: select_playlist())
        details_label.bind("<Button-1>", lambda e: select_playlist())

    def _select_playlist(self, playlist):
        """Select and display a playlist"""
        self.current_playlist = playlist
        self.playlist_title.configure(text=playlist.name)
        self._refresh_playlist_tracks()

    def _refresh_playlist_tracks(self):
        """Refresh the tracks in the current playlist"""
        # Clear existing tracks
        for widget in self.tracks_frame.winfo_children():
            widget.destroy()

        if not self.current_playlist or not self.current_playlist.tracks:
            no_tracks_label = ctk.CTkLabel(self.tracks_frame,
                                         text="No tracks in this playlist\nAdd some tracks to get started!",
                                         text_color="#888888")
            no_tracks_label.pack(pady=20)
            return

        # Display tracks
        for i, track in enumerate(self.current_playlist.tracks):
            self._create_track_item(track, i + 1)

    def _create_track_item(self, track, track_number):
        """Create a track item widget for playlist"""
        track_frame = ctk.CTkFrame(self.tracks_frame)
        track_frame.pack(fill="x", padx=5, pady=2)

        info_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=5)

        # Track number and title
        title_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_frame.pack(fill="x")

        number_label = ctk.CTkLabel(title_frame, text=f"{track_number:02d}.",
                                  font=ctk.CTkFont(size=12), width=30)
        number_label.pack(side="left")

        title_label = ctk.CTkLabel(title_frame, text=track.title,
                                 font=ctk.CTkFont(size=12, weight="bold"))
        title_label.pack(side="left", padx=(5, 0))

        # Artist and duration
        details_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        details_frame.pack(fill="x", pady=(2, 0))

        artist_text = ", ".join([a.name for a in track.artists]) if track.artists else "Unknown Artist"
        duration_text = f"{int(track.duration // 60)}:{int(track.duration % 60):02d}" if track.duration else "0:00"

        artist_label = ctk.CTkLabel(details_frame, text=artist_text,
                                  font=ctk.CTkFont(size=10), text_color="#888888")
        artist_label.pack(side="left", padx=(35, 0))

        duration_label = ctk.CTkLabel(details_frame, text=duration_text,
                                    font=ctk.CTkFont(size=10), text_color="#888888")
        duration_label.pack(side="right")

    def load_all_tracks(self):
        """Load all tracks for adding to playlists"""
        try:
            self.all_tracks = self.library_manager.get_recent_tracks(limit=1000)  # Get many tracks
        except Exception as e:
            print(f"Error loading tracks: {e}")
            self.all_tracks = []

    def _create_new_playlist(self):
        """Create a new playlist"""
        self._show_playlist_dialog()

    def _edit_playlist(self):
        """Edit the selected playlist"""
        if not self.current_playlist:
            messagebox.showwarning("No Selection", "Please select a playlist to edit")
            return
        self._show_playlist_dialog(self.current_playlist)

    def _delete_playlist(self):
        """Delete the selected playlist"""
        if not self.current_playlist:
            messagebox.showwarning("No Selection", "Please select a playlist to delete")
            return

        result = messagebox.askyesno("Confirm Delete",
                                   f"Are you sure you want to delete the playlist '{self.current_playlist.name}'?")
        if result:
            try:
                self.library_manager.delete_playlist(self.current_playlist.id)
                self.current_playlist = None
                self.playlist_title.configure(text="Select a playlist")
                self.refresh_playlists()
                self._refresh_playlist_tracks()
                messagebox.showinfo("Success", "Playlist deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete playlist: {e}")

    def _show_playlist_dialog(self, playlist=None):
        """Show create/edit playlist dialog"""
        is_editing = playlist is not None

        # Create dialog
        dialog = ctk.CTkToplevel(self.dialog)
        dialog.title("Edit Playlist" if is_editing else "Create New Playlist")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.dialog)
        dialog.grab_set()

        # Name field
        name_frame = ctk.CTkFrame(dialog)
        name_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(name_frame, text="Playlist Name:").pack(anchor="w", pady=(5, 0))
        name_entry = ctk.CTkEntry(name_frame, width=300)
        name_entry.pack(fill="x", pady=(5, 5))

        if is_editing:
            name_entry.insert(0, playlist.name)

        # Description field
        desc_frame = ctk.CTkFrame(dialog)
        desc_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(desc_frame, text="Description (optional):").pack(anchor="w", pady=(5, 0))
        desc_text = ctk.CTkTextbox(desc_frame, height=100, width=300)
        desc_text.pack(fill="x", pady=(5, 5))

        if is_editing and playlist.description:
            desc_text.insert("1.0", playlist.description)

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=(5, 0))

        def save_playlist():
            name = name_entry.get().strip()
            description = desc_text.get("1.0", "end").strip()

            if not name:
                messagebox.showerror("Error", "Please enter a playlist name")
                return

            try:
                if is_editing:
                    # Update existing playlist
                    self.library_manager.update_playlist(playlist.id, {
                        'name': name,
                        'description': description
                    })
                    messagebox.showinfo("Success", "Playlist updated successfully")
                else:
                    # Create new playlist
                    new_playlist = self.library_manager.create_playlist(name, description)
                    if new_playlist:
                        messagebox.showinfo("Success", "Playlist created successfully")
                    else:
                        messagebox.showerror("Error", "Failed to create playlist")

                dialog.destroy()
                self.refresh_playlists()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save playlist: {e}")

        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_playlist)
        save_btn.pack(side="right")

    def _show_add_tracks_dialog(self):
        """Show dialog to add tracks to current playlist"""
        if not self.current_playlist:
            messagebox.showwarning("No Playlist", "Please select a playlist first")
            return

        # Create dialog
        dialog = ctk.CTkToplevel(self.dialog)
        dialog.title("Add Tracks to Playlist")
        dialog.geometry("600x500")
        dialog.resizable(True, True)
        dialog.transient(self.dialog)
        dialog.grab_set()

        # Search frame
        search_frame = ctk.CTkFrame(dialog)
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Search Tracks:").pack(side="left")
        search_entry = ctk.CTkEntry(search_frame, width=200)
        search_entry.pack(side="left", padx=(10, 5))

        def search_tracks():
            query = search_entry.get().strip()
            if query:
                tracks = self.library_manager.search_tracks(query, limit=100)
            else:
                tracks = self.all_tracks[:100]  # Show first 100 tracks
            display_tracks_for_selection(tracks)

        search_btn = ctk.CTkButton(search_frame, text="Search", command=search_tracks)
        search_btn.pack(side="left")

        # Tracks list
        tracks_scroll = ctk.CTkScrollableFrame(dialog, label_text="Available Tracks")
        tracks_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        selected_tracks = set()

        def display_tracks_for_selection(tracks):
            # Clear existing
            for widget in tracks_scroll.winfo_children():
                widget.destroy()

            for track in tracks:
                track_frame = ctk.CTkFrame(tracks_scroll)
                track_frame.pack(fill="x", padx=5, pady=2)

                # Checkbox
                var = ctk.BooleanVar()
                checkbox = ctk.CTkCheckBox(track_frame, text="", variable=var, width=20)
                checkbox.pack(side="left", padx=5)

                # Track info
                info_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
                info_frame.pack(fill="x", side="left", padx=(5, 5))

                title_label = ctk.CTkLabel(info_frame, text=track.title,
                                         font=ctk.CTkFont(weight="bold"))
                title_label.pack(anchor="w")

                artist_text = ", ".join([a.name for a in track.artists]) if track.artists else "Unknown Artist"
                artist_label = ctk.CTkLabel(info_frame, text=artist_text,
                                          font=ctk.CTkFont(size=10), text_color="#888888")
                artist_label.pack(anchor="w")

                # Track selection
                def track_selected(t=track, v=var):
                    if v.get():
                        selected_tracks.add(t)
                    else:
                        selected_tracks.discard(t)

                var.trace('w', lambda *args, t=track, v=var: track_selected(t, v))

        # Initialize with recent tracks
        display_tracks_for_selection(self.all_tracks[:50])

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=(5, 0))

        def add_selected_tracks():
            if not selected_tracks:
                messagebox.showwarning("No Selection", "Please select tracks to add")
                return

            try:
                for track in selected_tracks:
                    self.library_manager.add_track_to_playlist(self.current_playlist.id, track.id)

                messagebox.showinfo("Success", f"Added {len(selected_tracks)} tracks to playlist")
                dialog.destroy()

                # Refresh current playlist
                self.current_playlist = self.library_manager.get_playlist(self.current_playlist.id)
                self._refresh_playlist_tracks()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add tracks: {e}")

        add_btn = ctk.CTkButton(button_frame, text=f"Add Selected", command=add_selected_tracks)
        add_btn.pack(side="right")

    def _remove_selected_track(self):
        """Remove selected track from playlist"""
        # This would need track selection implementation
        messagebox.showinfo("Not Implemented", "Track removal will be implemented in the next version")

    def _clear_playlist(self):
        """Clear all tracks from playlist"""
        if not self.current_playlist:
            messagebox.showwarning("No Playlist", "Please select a playlist first")
            return

        result = messagebox.askyesno("Confirm Clear",
                                   f"Are you sure you want to remove all tracks from '{self.current_playlist.name}'?")
        if result:
            try:
                self.library_manager.clear_playlist(self.current_playlist.id)
                self.current_playlist = self.library_manager.get_playlist(self.current_playlist.id)
                self._refresh_playlist_tracks()
                messagebox.showinfo("Success", "Playlist cleared successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear playlist: {e}")

    def _play_playlist(self):
        """Play the current playlist"""
        if not self.current_playlist or not self.current_playlist.tracks:
            messagebox.showwarning("Empty Playlist", "Please select a playlist with tracks")
            return

        messagebox.showinfo("Play Playlist",
                          f"Playing playlist '{self.current_playlist.name}' with {len(self.current_playlist.tracks)} tracks.\n"
                          "Full playlist playback integration will be completed in the next version.")


def main():
    """Main application entry point"""
    print("🎵 Starting Auralis Modern GUI...")

    app = AuralisGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()