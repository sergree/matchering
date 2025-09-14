"""
Tests for library management functionality.
"""

import pytest
import os
from pathlib import Path
import tempfile
import shutil
from src.library.models.database import LibraryManager, Track, Album, Artist
from src.library.scanning.scanner import LibraryScanner
from src.library.metadata.reader import MetadataReader

@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture
def temp_db():
    """Create temporary database."""
    _, path = tempfile.mkstemp(suffix='.db')
    yield path
    os.unlink(path)

@pytest.fixture
def library(temp_db):
    """Create library manager."""
    return LibraryManager(temp_db)

@pytest.fixture
def scanner(library):
    """Create library scanner."""
    return LibraryScanner(library)

def create_test_audio_file(path: str, ext: str = '.mp3') -> str:
    """Create test audio file.
    
    Args:
        path: Directory path
        ext: File extension
        
    Returns:
        Path to created file
    """
    filepath = os.path.join(path, f'test{ext}')
    with open(filepath, 'wb') as f:
        f.write(b'dummy audio data')
    return filepath

def test_metadata_reader():
    """Test metadata reader."""
    reader = MetadataReader()
    
    with tempfile.NamedTemporaryFile(suffix='.mp3') as f:
        # Write dummy MP3 file
        f.write(b'dummy audio data')
        f.flush()
        
        # Read metadata
        metadata = reader.read_metadata(f.name)
        
        # Check basic file info
        assert metadata['format'] == 'mp3'
        assert metadata['filesize'] > 0
        assert 'filepath' in metadata
        assert 'filename' in metadata

def test_library_manager(library, temp_dir):
    """Test library manager."""
    # Create test file
    filepath = create_test_audio_file(temp_dir)
    
    # Add track
    track = library.add_track(filepath, {
        'title': 'Test Track',
        'artists': ['Test Artist'],
        'album': 'Test Album',
        'year': 2025,
        'genres': ['Test Genre']
    })
    
    # Check track
    assert track.title == 'Test Track'
    assert track.filepath == str(Path(filepath).absolute())
    assert track.year == 2025
    
    # Check relationships
    assert len(track.artists) == 1
    assert track.artists[0].name == 'Test Artist'
    assert track.album.title == 'Test Album'
    assert len(track.genres) == 1
    assert track.genres[0].name == 'Test Genre'
    
    # Update statistics
    library.update_statistics()
    
    # Check statistics
    session = library.db.get_session()
    try:
        stats = session.query(LibraryStatistics).first()
        assert stats.total_tracks == 1
        assert stats.total_albums == 1
        assert stats.total_artists == 1
    finally:
        session.close()

@pytest.mark.asyncio
async def test_library_scanner(scanner, temp_dir):
    """Test library scanner."""
    # Create test files
    files = [
        create_test_audio_file(temp_dir, '.mp3'),
        create_test_audio_file(temp_dir, '.flac'),
        create_test_audio_file(temp_dir, '.wav')
    ]
    
    # Create unsupported file
    unsupported = os.path.join(temp_dir, 'test.txt')
    with open(unsupported, 'w') as f:
        f.write('dummy text file')
    
    # Scan directory
    await scanner.scan_directory(temp_dir)
    
    # Check statistics
    session = scanner.library.db.get_session()
    try:
        stats = session.query(LibraryStatistics).first()
        assert stats.total_tracks == len(files)
    finally:
        session.close()

def test_library_search(library, temp_dir):
    """Test library search."""
    # Add test tracks
    track1 = library.add_track(create_test_audio_file(temp_dir), {
        'title': 'Test Track 1',
        'artists': ['Artist 1'],
        'album': 'Album 1',
        'genres': ['Genre 1']
    })
    
    track2 = library.add_track(create_test_audio_file(temp_dir), {
        'title': 'Test Track 2',
        'artists': ['Artist 2'],
        'album': 'Album 2',
        'genres': ['Genre 2']
    })
    
    # Test search
    session = library.db.get_session()
    try:
        # Search by title
        results = session.query(Track).filter(
            Track.title.ilike('%Track 1%')
        ).all()
        assert len(results) == 1
        assert results[0].id == track1.id
        
        # Search by artist
        results = session.query(Artist).filter(
            Artist.name.ilike('%Artist 2%')
        ).all()
        assert len(results) == 1
        assert results[0].tracks[0].id == track2.id
        
        # Search by album
        results = session.query(Album).filter(
            Album.title.ilike('%Album%')
        ).all()
        assert len(results) == 2
        
    finally:
        session.close()