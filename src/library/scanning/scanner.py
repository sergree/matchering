"""
Music library scanner module.
"""

import os
from pathlib import Path
from typing import List, Set, Generator, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio
from ..metadata.reader import MetadataReader
from ..models.database import LibraryManager

class LibraryScanner:
    """Music library scanner."""
    
    SUPPORTED_EXTENSIONS = {'.mp3', '.flac', '.wav', '.aiff'}
    
    def __init__(self, library_manager: LibraryManager):
        """Initialize scanner.
        
        Args:
            library_manager: Library manager instance
        """
        self.library = library_manager
        self.reader = MetadataReader()
        self._scanning = False
        self._total_files = 0
        self._processed_files = 0
        self._current_file: Optional[str] = None
        
    @property
    def is_scanning(self) -> bool:
        """Whether scanner is currently running."""
        return self._scanning
        
    @property
    def progress(self) -> float:
        """Scan progress as percentage."""
        if self._total_files == 0:
            return 0.0
        return (self._processed_files / self._total_files) * 100
        
    @property
    def current_file(self) -> Optional[str]:
        """Currently processing file."""
        return self._current_file
        
    def _find_audio_files(self, path: str) -> Generator[str, None, None]:
        """Find all supported audio files in directory.
        
        Args:
            path: Directory path to scan
            
        Yields:
            Paths to audio files
        """
        for root, _, files in os.walk(path):
            for file in files:
                if Path(file).suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    yield os.path.join(root, file)
                    
    def _count_audio_files(self, path: str) -> int:
        """Count number of supported audio files in directory.
        
        Args:
            path: Directory path to scan
            
        Returns:
            Number of audio files found
        """
        return sum(1 for _ in self._find_audio_files(path))
        
    async def _process_file(self, filepath: str) -> None:
        """Process a single audio file.
        
        Args:
            filepath: Path to audio file
        """
        try:
            self._current_file = filepath
            metadata = await asyncio.get_event_loop().run_in_executor(
                None,
                self.reader.read_metadata,
                filepath
            )
            self.library.add_track(filepath, metadata)
            self._processed_files += 1
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
        finally:
            self._current_file = None
            
    async def scan_directory(self, path: str, max_workers: int = 4) -> None:
        """Scan directory for audio files.
        
        Args:
            path: Directory path to scan
            max_workers: Maximum number of concurrent workers
        """
        if self._scanning:
            raise RuntimeError("Scanner is already running")
            
        self._scanning = True
        self._processed_files = 0
        self._total_files = self._count_audio_files(path)
        
        try:
            # Process files concurrently
            tasks = []
            for filepath in self._find_audio_files(path):
                if not self._scanning:
                    break
                    
                # Limit concurrent tasks
                while len(tasks) >= max_workers:
                    done, tasks = await asyncio.wait(
                        tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in done:
                        try:
                            await task
                        except Exception as e:
                            print(f"Task failed: {e}")
                            
                tasks.append(asyncio.create_task(self._process_file(filepath)))
                
            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
            # Update library statistics
            self.library.update_statistics()
            
        finally:
            self._scanning = False
            self._current_file = None
            
    def stop(self):
        """Stop scanning process."""
        self._scanning = False