import { apiClient } from './config';
import {
  Track,
  Playlist,
  ProcessingParams,
  ProcessingPreset,
  PaginationParams,
  PaginatedResponse,
  ApiResponse,
  UploadProgress,
  UploadResult,
} from './types';
import {
  cache,
  withCache,
  getCacheKey,
  invalidateTrack,
  invalidatePlaylist,
  invalidateLibrary,
} from './cache';

// Library API
export const libraryApi = {
  // Tracks
  async getTracks(params?: PaginationParams): Promise<PaginatedResponse<Track>> {
    const key = getCacheKey('tracks', params);
    return withCache(key, 'library', () =>
      apiClient.get('/api/tracks', { params }).then(res => res.data)
    );
  },

  async getTrack(id: string): Promise<Track> {
    return withCache(`track:${id}`, 'track', () =>
      apiClient.get(`/api/tracks/${id}`).then(res => res.data)
    );
  },

  async uploadTrack(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<UploadResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/api/tracks/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percent: (progressEvent.loaded / progressEvent.total) * 100,
          });
        }
      },
    });

    invalidateLibrary();
    return response.data;
  },

  async deleteTrack(id: string): Promise<void> {
    await apiClient.delete(`/api/tracks/${id}`);
    invalidateTrack(id);
    invalidateLibrary();
  },

  // Playlists
  async getPlaylists(params?: PaginationParams): Promise<PaginatedResponse<Playlist>> {
    const key = getCacheKey('playlists', params);
    return withCache(key, 'library', () =>
      apiClient.get('/api/playlists', { params }).then(res => res.data)
    );
  },

  async getPlaylist(id: string): Promise<Playlist> {
    return withCache(`playlist:${id}`, 'playlist', () =>
      apiClient.get(`/api/playlists/${id}`).then(res => res.data)
    );
  },

  async createPlaylist(data: Partial<Playlist>): Promise<Playlist> {
    const response = await apiClient.post('/api/playlists', data);
    invalidateLibrary();
    return response.data;
  },

  async updatePlaylist(id: string, data: Partial<Playlist>): Promise<Playlist> {
    const response = await apiClient.put(`/api/playlists/${id}`, data);
    invalidatePlaylist(id);
    invalidateLibrary();
    return response.data;
  },

  async deletePlaylist(id: string): Promise<void> {
    await apiClient.delete(`/api/playlists/${id}`);
    invalidatePlaylist(id);
    invalidateLibrary();
  },

  async addTrackToPlaylist(playlistId: string, trackId: string, position?: number): Promise<void> {
    await apiClient.post(`/api/playlists/${playlistId}/tracks`, {
      track_id: trackId,
      position,
    });
    invalidatePlaylist(playlistId);
  },

  async removeTrackFromPlaylist(playlistId: string, trackId: string): Promise<void> {
    await apiClient.delete(`/api/playlists/${playlistId}/tracks/${trackId}`);
    invalidatePlaylist(playlistId);
  },

  async reorderPlaylistTracks(playlistId: string, trackIds: string[]): Promise<void> {
    await apiClient.put(`/api/playlists/${playlistId}/tracks/reorder`, {
      track_ids: trackIds,
    });
    invalidatePlaylist(playlistId);
  },
};

// Processing API
export const processingApi = {
  async getProcessingStatus(trackId: string): Promise<ApiResponse<ProcessingStatus>> {
    return apiClient.get(`/api/processing/${trackId}/status`).then(res => res.data);
  },

  async startProcessing(
    trackId: string,
    params: ProcessingParams
  ): Promise<ApiResponse<void>> {
    return apiClient
      .post(`/api/processing/${trackId}/start`, params)
      .then(res => res.data);
  },

  async stopProcessing(trackId: string): Promise<ApiResponse<void>> {
    return apiClient
      .post(`/api/processing/${trackId}/stop`)
      .then(res => res.data);
  },

  async getPresets(): Promise<ProcessingPreset[]> {
    return withCache('processing:presets', 'library', () =>
      apiClient.get('/api/processing/presets').then(res => res.data)
    );
  },

  async createPreset(data: Partial<ProcessingPreset>): Promise<ProcessingPreset> {
    const response = await apiClient.post('/api/processing/presets', data);
    invalidateLibrary();
    return response.data;
  },

  async updatePreset(
    id: string,
    data: Partial<ProcessingPreset>
  ): Promise<ProcessingPreset> {
    const response = await apiClient.put(`/api/processing/presets/${id}`, data);
    invalidateLibrary();
    return response.data;
  },

  async deletePreset(id: string): Promise<void> {
    await apiClient.delete(`/api/processing/presets/${id}`);
    invalidateLibrary();
  },
};

// Analysis API
export const analysisApi = {
  async getTrackAnalysis(trackId: string): Promise<ApiResponse<TrackAnalysis>> {
    return withCache(`analysis:${trackId}`, 'track', () =>
      apiClient.get(`/api/analysis/${trackId}`).then(res => res.data)
    );
  },

  async analyzeTrack(trackId: string): Promise<ApiResponse<void>> {
    return apiClient
      .post(`/api/analysis/${trackId}/start`)
      .then(res => res.data);
  },
};

// Export a default API client combining all endpoints
export const api = {
  library: libraryApi,
  processing: processingApi,
  analysis: analysisApi,
};