import { CacheEntry } from './types';
import { CACHE_CONFIG } from './config';

class Cache {
  private storage: Map<string, CacheEntry<any>>;
  private keyTimeMap: Map<string, number>;

  constructor() {
    this.storage = new Map();
    this.keyTimeMap = new Map();
    this.startCleanupInterval();
  }

  set<T>(key: string, data: T, type: keyof typeof CACHE_CONFIG.version): void {
    const timestamp = Date.now();
    const version = CACHE_CONFIG.version[type];
    
    this.storage.set(key, { data, timestamp, version });
    this.keyTimeMap.set(key, timestamp);
    
    // Enforce size limits
    this.enforceLimit(type);
  }

  get<T>(key: string, type: keyof typeof CACHE_CONFIG.version): T | null {
    const entry = this.storage.get(key) as CacheEntry<T>;
    
    if (!entry) {
      return null;
    }
    
    // Check version
    if (entry.version !== CACHE_CONFIG.version[type]) {
      this.delete(key);
      return null;
    }
    
    // Check expiration
    const age = Date.now() - entry.timestamp;
    if (age > CACHE_CONFIG[type]) {
      this.delete(key);
      return null;
    }
    
    return entry.data;
  }

  delete(key: string): void {
    this.storage.delete(key);
    this.keyTimeMap.delete(key);
  }

  clear(): void {
    this.storage.clear();
    this.keyTimeMap.clear();
  }

  private enforceLimit(type: string): void {
    const limit = type === 'track' ? CACHE_CONFIG.maxTracks : CACHE_CONFIG.maxPlaylists;
    
    if (this.storage.size > limit) {
      // Sort by timestamp and remove oldest entries
      const entries = Array.from(this.keyTimeMap.entries())
        .sort((a, b) => a[1] - b[1]);
      
      const toRemove = entries.slice(0, this.storage.size - limit);
      toRemove.forEach(([key]) => this.delete(key));
    }
  }

  private startCleanupInterval(): void {
    // Run cleanup every minute
    setInterval(() => {
      const now = Date.now();
      
      for (const [key, entry] of this.storage.entries()) {
        const type = key.startsWith('track') ? 'track' :
                    key.startsWith('playlist') ? 'playlist' : 'library';
                    
        const maxAge = CACHE_CONFIG[type];
        const age = now - entry.timestamp;
        
        if (age > maxAge || entry.version !== CACHE_CONFIG.version[type]) {
          this.delete(key);
        }
      }
    }, 60000);
  }
}

// Create singleton instance
export const cache = new Cache();

// Helper functions for specific types
export function cacheTrack<T>(key: string, data: T): void {
  cache.set(`track:${key}`, data, 'track');
}

export function getCachedTrack<T>(key: string): T | null {
  return cache.get(`track:${key}`, 'track');
}

export function cachePlaylist<T>(key: string, data: T): void {
  cache.set(`playlist:${key}`, data, 'playlist');
}

export function getCachedPlaylist<T>(key: string): T | null {
  return cache.get(`playlist:${key}`, 'playlist');
}

export function cacheLibrary<T>(key: string, data: T): void {
  cache.set(`library:${key}`, data, 'library');
}

export function getCachedLibrary<T>(key: string): T | null {
  return cache.get(`library:${key}`, 'library');
}

// Cache invalidation helpers
export function invalidateTrack(trackId: string): void {
  cache.delete(`track:${trackId}`);
}

export function invalidatePlaylist(playlistId: string): void {
  cache.delete(`playlist:${playlistId}`);
}

export function invalidateLibrary(): void {
  // Clear all library-related caches
  for (const [key] of cache['storage'].entries()) {
    if (key.startsWith('library:')) {
      cache.delete(key);
    }
  }
}

// Query cache helpers
interface QueryParams {
  [key: string]: string | number | boolean | undefined;
}

export function getCacheKey(base: string, params?: QueryParams): string {
  if (!params) return base;
  
  const sortedKeys = Object.keys(params).sort();
  const queryString = sortedKeys
    .map(key => `${key}=${params[key]}`)
    .join('&');
    
  return `${base}?${queryString}`;
}

// Cache wrapper for API calls
export async function withCache<T>(
  key: string,
  type: keyof typeof CACHE_CONFIG.version,
  fetchFn: () => Promise<T>
): Promise<T> {
  // Try to get from cache
  const cached = cache.get<T>(key, type);
  if (cached !== null) {
    return cached;
  }
  
  // Fetch fresh data
  const data = await fetchFn();
  cache.set(key, data, type);
  return data;
}