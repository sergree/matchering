# -*- coding: utf-8 -*-

"""
Auralis Library Scanner
~~~~~~~~~~~~~~~~~~~~~~

Automated folder scanning and music discovery system
Handles recursive directory scanning with intelligent file detection

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.
"""

import os
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Callable, Generator, Set
from dataclasses import dataclass
from datetime import datetime
import soundfile as sf

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    MutagenFile = None

from ..utils.logging import info, warning, error, debug


@dataclass
class ScanResult:
    """Result of a library scan operation"""
    files_found: int = 0
    files_processed: int = 0
    files_added: int = 0
    files_updated: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    scan_time: float = 0.0
    directories_scanned: int = 0

    def __str__(self):
        return (f"Scan Results: {self.files_found} found, {self.files_added} added, "
                f"{self.files_updated} updated, {self.files_failed} failed "
                f"({self.scan_time:.1f}s)")


@dataclass
class AudioFileInfo:
    """Information about discovered audio file"""
    filepath: str
    filename: str
    filesize: int
    modified_time: datetime
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None
    metadata: Optional[Dict] = None
    file_hash: Optional[str] = None


class LibraryScanner:
    """
    Comprehensive library scanning system

    Features:
    - Recursive directory scanning
    - Audio format detection and analysis
    - Metadata extraction
    - Duplicate detection
    - Progress tracking
    - Intelligent file filtering
    """

    # Supported audio formats
    AUDIO_EXTENSIONS = {
        '.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma',
        '.aiff', '.au', '.mp4', '.m4p', '.opus', '.webm'
    }

    # Common non-music directories to skip
    SKIP_DIRECTORIES = {
        '.git', '.svn', 'node_modules', '__pycache__', '.vscode',
        'System Volume Information', '$RECYCLE.BIN', 'Thumbs.db',
        '.DS_Store', '.AppleDouble', '.LSOverride'
    }

    def __init__(self, library_manager):
        """Initialize scanner with library manager"""
        self.library_manager = library_manager
        self.progress_callback: Optional[Callable] = None
        self.should_stop = False

    def set_progress_callback(self, callback: Callable[[Dict], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback

    def stop_scan(self):
        """Signal scanner to stop"""
        self.should_stop = True

    def scan_directories(self, directories: List[str],
                        recursive: bool = True,
                        skip_existing: bool = True,
                        check_modifications: bool = True) -> ScanResult:
        """
        Scan multiple directories for audio files

        Args:
            directories: List of directory paths to scan
            recursive: Whether to scan subdirectories
            skip_existing: Skip files already in library
            check_modifications: Check for file modifications

        Returns:
            ScanResult with scan statistics
        """
        start_time = time.time()
        result = ScanResult()

        info(f"Starting library scan of {len(directories)} directories")

        try:
            # Discover all audio files
            all_files = []
            for directory in directories:
                if self.should_stop:
                    break

                files = list(self._discover_audio_files(directory, recursive))
                all_files.extend(files)
                result.directories_scanned += 1

                self._report_progress({
                    'stage': 'discovering',
                    'directory': directory,
                    'files_found': len(files),
                    'total_found': len(all_files)
                })

            result.files_found = len(all_files)
            info(f"Discovered {result.files_found} audio files")

            if self.should_stop:
                return result

            # Process files in batches for better performance
            batch_size = 50
            for i in range(0, len(all_files), batch_size):
                if self.should_stop:
                    break

                batch = all_files[i:i + batch_size]
                batch_result = self._process_file_batch(
                    batch, skip_existing, check_modifications
                )

                result.files_processed += batch_result.files_processed
                result.files_added += batch_result.files_added
                result.files_updated += batch_result.files_updated
                result.files_skipped += batch_result.files_skipped
                result.files_failed += batch_result.files_failed

                # Report progress
                progress = (i + len(batch)) / len(all_files)
                self._report_progress({
                    'stage': 'processing',
                    'progress': progress,
                    'processed': result.files_processed,
                    'added': result.files_added,
                    'failed': result.files_failed
                })

            result.scan_time = time.time() - start_time

            # Update library statistics
            self._update_library_stats(result)

            info(f"Library scan completed: {result}")
            return result

        except Exception as e:
            error(f"Library scan failed: {e}")
            result.scan_time = time.time() - start_time
            return result

    def scan_single_directory(self, directory: str, **kwargs) -> ScanResult:
        """Scan a single directory"""
        return self.scan_directories([directory], **kwargs)

    def _discover_audio_files(self, directory: str, recursive: bool) -> Generator[str, None, None]:
        """Discover audio files in directory"""
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                warning(f"Directory does not exist: {directory}")
                return

            if not directory_path.is_dir():
                warning(f"Path is not a directory: {directory}")
                return

            debug(f"Scanning directory: {directory}")

            # Use appropriate scanning method
            if recursive:
                pattern_method = directory_path.rglob
            else:
                pattern_method = directory_path.glob

            # Find all audio files
            for ext in self.AUDIO_EXTENSIONS:
                for file_path in pattern_method(f"*{ext}"):
                    if self.should_stop:
                        break

                    # Skip if in excluded directory
                    if self._should_skip_path(file_path):
                        continue

                    # Verify it's actually a file
                    if file_path.is_file():
                        yield str(file_path)

        except PermissionError:
            warning(f"Permission denied accessing directory: {directory}")
        except Exception as e:
            error(f"Error scanning directory {directory}: {e}")

    def _should_skip_path(self, file_path: Path) -> bool:
        """Check if path should be skipped"""
        # Check if any parent directory should be skipped
        for parent in file_path.parents:
            if parent.name in self.SKIP_DIRECTORIES:
                return True

        # Check for hidden files/directories (starting with .)
        for part in file_path.parts:
            if part.startswith('.') and len(part) > 1:
                return True

        return False

    def _process_file_batch(self, file_paths: List[str],
                           skip_existing: bool,
                           check_modifications: bool) -> ScanResult:
        """Process a batch of audio files"""
        result = ScanResult()

        for file_path in file_paths:
            if self.should_stop:
                break

            try:
                file_result = self._process_single_file(
                    file_path, skip_existing, check_modifications
                )

                result.files_processed += 1
                if file_result == 'added':
                    result.files_added += 1
                elif file_result == 'updated':
                    result.files_updated += 1
                elif file_result == 'skipped':
                    result.files_skipped += 1
                else:  # failed
                    result.files_failed += 1

            except Exception as e:
                error(f"Failed to process {file_path}: {e}")
                result.files_failed += 1

        return result

    def _process_single_file(self, file_path: str,
                           skip_existing: bool,
                           check_modifications: bool) -> str:
        """
        Process a single audio file

        Returns:
            'added', 'updated', 'skipped', or 'failed'
        """
        try:
            # Check if file already exists in library
            if skip_existing:
                existing_track = self.library_manager.get_track_by_filepath(file_path)
                if existing_track:
                    if check_modifications:
                        # Check if file was modified since last scan
                        file_stat = Path(file_path).stat()
                        file_mtime = datetime.fromtimestamp(file_stat.st_mtime)

                        if existing_track.updated_at and existing_track.updated_at >= file_mtime:
                            return 'skipped'  # File hasn't been modified
                    else:
                        return 'skipped'  # Skip existing files

            # Extract file information
            audio_info = self._extract_audio_info(file_path)
            if not audio_info:
                return 'failed'

            # Convert to track info format
            track_info = self._audio_info_to_track_info(audio_info)

            # Add or update track in library
            if skip_existing and self.library_manager.get_track_by_filepath(file_path):
                # Update existing track
                track = self.library_manager.update_track_by_filepath(file_path, track_info)
                return 'updated' if track else 'failed'
            else:
                # Add new track
                track = self.library_manager.add_track(track_info)
                return 'added' if track else 'failed'

        except Exception as e:
            debug(f"Error processing {file_path}: {e}")
            return 'failed'

    def _extract_audio_info(self, file_path: str) -> Optional[AudioFileInfo]:
        """Extract comprehensive audio file information"""
        try:
            path = Path(file_path)
            file_stat = path.stat()

            info_obj = AudioFileInfo(
                filepath=file_path,
                filename=path.name,
                filesize=file_stat.st_size,
                modified_time=datetime.fromtimestamp(file_stat.st_mtime)
            )

            # Extract audio properties using soundfile
            try:
                sf_info = sf.info(file_path)
                info_obj.duration = sf_info.duration
                info_obj.sample_rate = sf_info.samplerate
                info_obj.channels = sf_info.channels
                info_obj.format = sf_info.format
            except Exception as e:
                debug(f"SoundFile analysis failed for {file_path}: {e}")

            # Extract metadata using mutagen if available
            if MUTAGEN_AVAILABLE:
                try:
                    audio_file = MutagenFile(file_path)
                    if audio_file:
                        info_obj.metadata = self._extract_metadata(audio_file)
                except Exception as e:
                    debug(f"Metadata extraction failed for {file_path}: {e}")

            # Generate file hash for duplicate detection
            try:
                info_obj.file_hash = self._calculate_file_hash(file_path)
            except Exception as e:
                debug(f"Hash calculation failed for {file_path}: {e}")

            return info_obj

        except Exception as e:
            debug(f"Failed to extract info from {file_path}: {e}")
            return None

    def _extract_metadata(self, audio_file) -> Dict:
        """Extract metadata from mutagen audio file object"""
        metadata = {}

        # Common tag mappings
        tag_mappings = {
            'title': ['TIT2', 'TITLE', '\xa9nam'],
            'artist': ['TPE1', 'ARTIST', '\xa9ART'],
            'album': ['TALB', 'ALBUM', '\xa9alb'],
            'albumartist': ['TPE2', 'ALBUMARTIST', 'aART'],
            'date': ['TDRC', 'DATE', '\xa9day'],
            'year': ['TDRC', 'DATE', '\xa9day', 'YEAR'],
            'genre': ['TCON', 'GENRE', '\xa9gen'],
            'track': ['TRCK', 'TRACKNUMBER', 'trkn'],
            'disc': ['TPOS', 'DISCNUMBER', 'disk'],
            'comment': ['COMM::eng', 'COMMENT', '\xa9cmt']
        }

        for field, keys in tag_mappings.items():
            for key in keys:
                if key in audio_file:
                    value = audio_file[key]
                    if isinstance(value, list) and value:
                        value = value[0]

                    if value:
                        if field in ['track', 'disc']:
                            # Handle track/disc numbers
                            try:
                                if '/' in str(value):
                                    value = int(str(value).split('/')[0])
                                else:
                                    value = int(value)
                            except (ValueError, TypeError):
                                continue
                        elif field in ['year', 'date']:
                            # Handle year/date
                            try:
                                year_str = str(value)[:4]
                                value = int(year_str)
                            except (ValueError, TypeError):
                                continue
                        else:
                            value = str(value)

                        metadata[field] = value
                        break

        return metadata

    def _calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """Calculate SHA-256 hash of file for duplicate detection"""
        hash_obj = hashlib.sha256()

        with open(file_path, 'rb') as f:
            # Hash first and last chunks for speed on large files
            chunk = f.read(chunk_size)
            if chunk:
                hash_obj.update(chunk)

            # Seek to end and read last chunk
            f.seek(-min(chunk_size, f.tell()), 2)
            last_chunk = f.read(chunk_size)
            if last_chunk and last_chunk != chunk:
                hash_obj.update(last_chunk)

        return hash_obj.hexdigest()[:16]  # Use first 16 chars

    def _audio_info_to_track_info(self, audio_info: AudioFileInfo) -> Dict:
        """Convert AudioFileInfo to track_info dict for library manager"""
        track_info = {
            'filepath': audio_info.filepath,
            'title': audio_info.filename,  # Default to filename
            'duration': audio_info.duration,
            'sample_rate': audio_info.sample_rate,
            'channels': audio_info.channels,
            'format': audio_info.format,
            'filesize': audio_info.filesize,
        }

        # Add metadata if available
        if audio_info.metadata:
            metadata = audio_info.metadata

            # Map metadata to track_info
            if 'title' in metadata:
                track_info['title'] = metadata['title']
            else:
                # Use filename without extension as title
                track_info['title'] = Path(audio_info.filepath).stem

            if 'artist' in metadata:
                # Handle multiple artists
                artists = metadata['artist']
                if isinstance(artists, str):
                    track_info['artists'] = [artists]
                else:
                    track_info['artists'] = [str(a) for a in artists]

            if 'album' in metadata:
                track_info['album'] = metadata['album']

            if 'genre' in metadata:
                genres = metadata['genre']
                if isinstance(genres, str):
                    track_info['genres'] = [genres]
                else:
                    track_info['genres'] = [str(g) for g in genres]

            if 'track' in metadata:
                track_info['track_number'] = metadata['track']

            if 'disc' in metadata:
                track_info['disc_number'] = metadata['disc']

            if 'year' in metadata:
                track_info['year'] = metadata['year']

        return track_info

    def _update_library_stats(self, scan_result: ScanResult):
        """Update library statistics after scan"""
        try:
            # This would update the LibraryStats table
            # For now, just log the results
            info(f"Scan completed: {scan_result}")
        except Exception as e:
            warning(f"Failed to update library stats: {e}")

    def _report_progress(self, progress_data: Dict):
        """Report progress to callback if set"""
        if self.progress_callback:
            try:
                self.progress_callback(progress_data)
            except Exception as e:
                warning(f"Progress callback failed: {e}")

    def find_duplicates(self, directories: List[str] = None) -> List[List[str]]:
        """
        Find duplicate audio files based on content hash

        Args:
            directories: Specific directories to check, or None for entire library

        Returns:
            List of lists, where each inner list contains paths of duplicate files
        """
        try:
            duplicates = []
            hash_to_files = {}

            if directories:
                # Scan specific directories
                for directory in directories:
                    for file_path in self._discover_audio_files(directory, True):
                        file_hash = self._calculate_file_hash(file_path)
                        if file_hash:
                            if file_hash in hash_to_files:
                                hash_to_files[file_hash].append(file_path)
                            else:
                                hash_to_files[file_hash] = [file_path]
            else:
                # Check entire library
                # This would query the database for all tracks with file hashes
                # For now, return empty list
                pass

            # Find duplicates
            for file_hash, files in hash_to_files.items():
                if len(files) > 1:
                    duplicates.append(files)

            return duplicates

        except Exception as e:
            error(f"Duplicate detection failed: {e}")
            return []