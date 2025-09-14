import { useEffect, useRef, useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { WebSocketManager } from './config';
import {
  Track,
  Playlist,
  ProcessingStatus,
  TrackAnalysis,
  PlaybackStatus,
  WsMessage,
} from './types';
import { api } from './client';

// WebSocket connection hook
export function useWebSocket() {
  const ws = useRef(WebSocketManager.getInstance());
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const connect = async () => {
      try {
        await ws.current.connect();
        setIsConnected(true);
        setError(null);
      } catch (e) {
        setError(e as Error);
      }
    };

    connect();

    return () => {
      ws.current.disconnect();
    };
  }, []);

  return { isConnected, error, ws: ws.current };
}

// Real-time processing status hook
export function useProcessingStatus(trackId: string) {
  const ws = useRef(WebSocketManager.getInstance());
  const [status, setStatus] = useState<ProcessingStatus | null>(null);

  useEffect(() => {
    const unsubscribe = ws.current.subscribe('processing_status', (data: WsMessage<ProcessingStatus>) => {
      if (data.data.track_id === trackId) {
        setStatus(data.data);
      }
    });

    // Get initial status
    api.processing.getProcessingStatus(trackId).then(response => {
      setStatus(response.data);
    });

    return () => {
      unsubscribe();
    };
  }, [trackId]);

  const startProcessing = useCallback(async () => {
    await api.processing.startProcessing(trackId, {
      // Add default processing params
    });
  }, [trackId]);

  const stopProcessing = useCallback(async () => {
    await api.processing.stopProcessing(trackId);
  }, [trackId]);

  return {
    status,
    startProcessing,
    stopProcessing,
    isProcessing: status?.state === 'processing',
  };
}

// Real-time analysis hook
export function useTrackAnalysis(trackId: string) {
  const ws = useRef(WebSocketManager.getInstance());
  const [analysis, setAnalysis] = useState<TrackAnalysis | null>(null);

  useEffect(() => {
    const unsubscribe = ws.current.subscribe('track_analysis', (data: WsMessage<TrackAnalysis>) => {
      if (data.data.id === trackId) {
        setAnalysis(data.data);
      }
    });

    // Get initial analysis
    api.analysis.getTrackAnalysis(trackId).then(response => {
      setAnalysis(response.data);
    });

    return () => {
      unsubscribe();
    };
  }, [trackId]);

  const startAnalysis = useCallback(async () => {
    await api.analysis.analyzeTrack(trackId);
  }, [trackId]);

  return {
    analysis,
    startAnalysis,
    hasAnalysis: analysis !== null,
  };
}

// Real-time playback status hook
export function usePlaybackStatus(trackId: string) {
  const ws = useRef(WebSocketManager.getInstance());
  const [status, setStatus] = useState<PlaybackStatus | null>(null);

  useEffect(() => {
    const unsubscribe = ws.current.subscribe('playback_status', (data: WsMessage<PlaybackStatus>) => {
      if (data.data.track_id === trackId) {
        setStatus(data.data);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [trackId]);

  return status;
}

// Library query hooks
export function useTracks(params?: any) {
  return useQuery(['tracks', params], () => api.library.getTracks(params), {
    staleTime: 1000 * 60, // 1 minute
  });
}

export function useTrack(id: string) {
  return useQuery(['track', id], () => api.library.getTrack(id), {
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function usePlaylists(params?: any) {
  return useQuery(['playlists', params], () => api.library.getPlaylists(params), {
    staleTime: 1000 * 60, // 1 minute
  });
}

export function usePlaylist(id: string) {
  return useQuery(['playlist', id], () => api.library.getPlaylist(id), {
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// Processing preset hooks
export function useProcessingPresets() {
  return useQuery(['processing:presets'], () => api.processing.getPresets(), {
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// Library update hook
export function useLibraryUpdates() {
  const ws = useRef(WebSocketManager.getInstance());
  const queryClient = useQueryClient();

  useEffect(() => {
    const handleTrackUpdate = (data: WsMessage<Track>) => {
      queryClient.setQueryData(['track', data.data.id], data.data);
      queryClient.invalidateQueries(['tracks']);
    };

    const handlePlaylistUpdate = (data: WsMessage<Playlist>) => {
      queryClient.setQueryData(['playlist', data.data.id], data.data);
      queryClient.invalidateQueries(['playlists']);
    };

    const unsubscribeTrack = ws.current.subscribe('track_update', handleTrackUpdate);
    const unsubscribePlaylist = ws.current.subscribe('playlist_update', handlePlaylistUpdate);

    return () => {
      unsubscribeTrack();
      unsubscribePlaylist();
    };
  }, [queryClient]);
}

// Upload hook with progress
export function useTrackUpload() {
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<Error | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const upload = useCallback(async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      const result = await api.library.uploadTrack(file, (progress) => {
        setProgress(progress.percent);
      });
      return result;
    } catch (e) {
      setError(e as Error);
      throw e;
    } finally {
      setIsUploading(false);
    }
  }, []);

  return {
    upload,
    progress,
    error,
    isUploading,
  };
}