export interface Track {
  id: string;
  title: string;
  artist: string;
  album?: string;
  duration: number;
  format: string;
  path: string;
  isFavorite: boolean;
  lastPlayed: string;
  metadata: Record<string, any>;
}

export interface Playlist {
  id: string;
  name: string;
  trackCount: number;
  tracks: string[];  // Track IDs
  isSmartPlaylist: boolean;
  smartRules?: Record<string, any>;
}

export interface LibraryState {
  tracks: Track[];
  playlists: Playlist[];
  currentTrack: Track | null;
  setCurrentTrack: (track: Track) => void;
  toggleFavorite: (trackId: string) => void;
  addTrack: (track: Track) => void;
  removeTrack: (trackId: string) => void;
  addPlaylist: (playlist: Playlist) => void;
  removePlaylist: (playlistId: string) => void;
  addTrackToPlaylist: (trackId: string, playlistId: string) => void;
  removeTrackFromPlaylist: (trackId: string, playlistId: string) => void;
}