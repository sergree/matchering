# -*- coding: utf-8 -*-

"""
Auralis Library Management
~~~~~~~~~~~~~~~~~~~~~~~~~

Music library database integration for Auralis

:copyright: (C) 2024 Auralis Team
:license: GPLv3, see LICENSE for more details.
"""

from .manager import LibraryManager
from .models import Track, Album, Artist, Genre, Playlist
from .scanner import LibraryScanner, ScanResult, AudioFileInfo

__all__ = [
    "LibraryManager",
    "Track", "Album", "Artist", "Genre", "Playlist",
    "LibraryScanner", "ScanResult", "AudioFileInfo"
]