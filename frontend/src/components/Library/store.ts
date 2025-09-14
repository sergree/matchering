import { create } from 'zustand';
import { LibraryState, Track, Playlist } from './types';

export const useLibraryStore = create<LibraryState>((set) => ({
  tracks: [],
  playlists: [],
  currentTrack: null,

  setCurrentTrack: (track: Track) => set({ currentTrack: track }),

  toggleFavorite: (trackId: string) =>
    set((state) => ({
      tracks: state.tracks.map((track) =>
        track.id === trackId
          ? { ...track, isFavorite: !track.isFavorite }
          : track
      ),
    })),

  addTrack: (track: Track) =>
    set((state) => ({
      tracks: [...state.tracks, track],
    })),

  removeTrack: (trackId: string) =>
    set((state) => ({
      tracks: state.tracks.filter((track) => track.id !== trackId),
      playlists: state.playlists.map((playlist) => ({
        ...playlist,
        tracks: playlist.tracks.filter((id) => id !== trackId),
        trackCount: playlist.tracks.filter((id) => id !== trackId).length,
      })),
    })),

  addPlaylist: (playlist: Playlist) =>
    set((state) => ({
      playlists: [...state.playlists, playlist],
    })),

  removePlaylist: (playlistId: string) =>
    set((state) => ({
      playlists: state.playlists.filter((playlist) => playlist.id !== playlistId),
    })),

  addTrackToPlaylist: (trackId: string, playlistId: string) =>
    set((state) => ({
      playlists: state.playlists.map((playlist) =>
        playlist.id === playlistId
          ? {
              ...playlist,
              tracks: [...playlist.tracks, trackId],
              trackCount: playlist.trackCount + 1,
            }
          : playlist
      ),
    })),

  removeTrackFromPlaylist: (trackId: string, playlistId: string) =>
    set((state) => ({
      playlists: state.playlists.map((playlist) =>
        playlist.id === playlistId
          ? {
              ...playlist,
              tracks: playlist.tracks.filter((id) => id !== trackId),
              trackCount: playlist.trackCount - 1,
            }
          : playlist
      ),
    })),
}));