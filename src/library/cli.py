"""
Command-line interface for library management.
"""

import asyncio
import argparse
from pathlib import Path
from typing import Optional
from .models.database import LibraryManager
from .scanning.scanner import LibraryScanner

class LibraryCLI:
    """Command-line interface for library management."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize CLI.
        
        Args:
            db_path: Optional path to database file
        """
        if db_path is None:
            db_path = str(Path.home() / '.matchering' / 'library.db')
            
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.library = LibraryManager(db_path)
        self.scanner = LibraryScanner(self.library)
        
    async def scan(self, path: str, max_workers: int = 4):
        """Scan directory for audio files.
        
        Args:
            path: Directory path to scan
            max_workers: Maximum number of concurrent workers
        """
        print(f"Scanning directory: {path}")
        
        # Start scanner
        try:
            await self.scanner.scan_directory(path, max_workers)
        except KeyboardInterrupt:
            print("\nScan interrupted by user")
            self.scanner.stop()
            return
            
        # Print statistics
        session = self.library.db.get_session()
        try:
            stats = session.query(LibraryStatistics).first()
            if stats:
                print("\nLibrary Statistics:")
                print(f"Total tracks: {stats.total_tracks}")
                print(f"Total albums: {stats.total_albums}")
                print(f"Total artists: {stats.total_artists}")
                print(f"Total duration: {stats.total_duration/3600:.1f} hours")
                print(f"Total size: {stats.total_size/1024/1024/1024:.1f} GB")
        finally:
            session.close()
            
    def show_statistics(self):
        """Show library statistics."""
        session = self.library.db.get_session()
        try:
            stats = session.query(LibraryStatistics).first()
            if stats:
                print("Library Statistics:")
                print(f"Total tracks: {stats.total_tracks}")
                print(f"Total albums: {stats.total_albums}")
                print(f"Total artists: {stats.total_artists}")
                print(f"Total playlists: {stats.total_playlists}")
                print(f"Total duration: {stats.total_duration/3600:.1f} hours")
                print(f"Total size: {stats.total_size/1024/1024/1024:.1f} GB")
                if stats.last_scan:
                    print(f"Last scan: {stats.last_scan}")
            else:
                print("No statistics available")
        finally:
            session.close()
            
    def search(self, query: str):
        """Search library.
        
        Args:
            query: Search query
        """
        session = self.library.db.get_session()
        try:
            # Search tracks
            tracks = session.query(Track).filter(
                or_(
                    Track.title.ilike(f"%{query}%"),
                    Track.filepath.ilike(f"%{query}%")
                )
            ).all()
            
            if tracks:
                print("\nTracks:")
                for track in tracks:
                    artists = ", ".join(a.name for a in track.artists)
                    print(f"- {track.title} by {artists} ({track.format})")
                    
            # Search albums
            albums = session.query(Album).filter(
                Album.title.ilike(f"%{query}%")
            ).all()
            
            if albums:
                print("\nAlbums:")
                for album in albums:
                    print(f"- {album.title} by {album.artist.name if album.artist else 'Unknown'}")
                    
            # Search artists
            artists = session.query(Artist).filter(
                Artist.name.ilike(f"%{query}%")
            ).all()
            
            if artists:
                print("\nArtists:")
                for artist in artists:
                    print(f"- {artist.name} ({len(artist.tracks)} tracks)")
                    
            if not (tracks or albums or artists):
                print("No results found")
                
        finally:
            session.close()
            
def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Matchering Library Management")
    
    # Common arguments
    parser.add_argument(
        "--db-path",
        help="Path to database file",
        default=None
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directory for audio files")
    scan_parser.add_argument("path", help="Directory path to scan")
    scan_parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Maximum number of concurrent workers"
    )
    
    # Stats command
    subparsers.add_parser("stats", help="Show library statistics")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search library")
    search_parser.add_argument("query", help="Search query")
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = LibraryCLI(args.db_path)
    
    # Execute command
    if args.command == "scan":
        asyncio.run(cli.scan(args.path, args.workers))
    elif args.command == "stats":
        cli.show_statistics()
    elif args.command == "search":
        cli.search(args.query)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()