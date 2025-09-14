// API Response Types
export interface ApiResponse<T> {
  data: T;
  error?: string;
  meta?: Record<string, any>;
}

// Library Types
export interface Track {
  id: string;
  title: string;
  artist: string;
  album?: string;
  duration: number;
  format: string;
  path: string;
  sample_rate: number;
  bit_depth: number;
  channels: number;
  filesize: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface Playlist {
  id: string;
  name: string;
  description?: string;
  track_count: number;
  duration: number;
  is_smart: boolean;
  smart_rules?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PlaylistTrack {
  playlist_id: string;
  track_id: string;
  position: number;
}

// Processing Types
export interface ProcessingParams {
  eq: {
    bands: Array<{
      frequency: number;
      gain: number;
      q: number;
    }>;
  };
  compressor: {
    threshold: number;
    ratio: number;
    attack: number;
    release: number;
    knee: number;
    makeup_gain: number;
  };
  stereo: {
    width: number;
    rotation: number;
    balance: number;
  };
  limiter: {
    threshold: number;
    release: number;
    lookahead: number;
  };
}

export interface ProcessingPreset {
  id: string;
  name: string;
  description?: string;
  params: ProcessingParams;
  created_at: string;
  updated_at: string;
}

// WebSocket Message Types
export interface WsMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
}

export interface TrackAnalysis {
  id: string;
  peak_level: number;
  rms_level: number;
  loudness: number;
  dynamic_range: number;
  spectrum: number[];
  stereo_width: number;
}

export interface ProcessingStatus {
  track_id: string;
  state: 'idle' | 'processing' | 'complete' | 'error';
  progress: number;
  stats?: {
    cpu_usage: number;
    memory_usage: number;
    latency: number;
  };
  error?: string;
}

export interface PlaybackStatus {
  track_id: string;
  state: 'playing' | 'paused' | 'stopped';
  position: number;
  duration: number;
  volume: number;
}

// API Error Types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// Pagination Types
export interface PaginationParams {
  page: number;
  per_page: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  filter?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Upload Types
export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}

export interface UploadResult {
  track_id: string;
  status: 'success' | 'error';
  error?: string;
}

// Cache Types
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  version: string;
}