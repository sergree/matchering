/**
 * Format duration in seconds to MM:SS format.
 */
export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * Format file size in bytes to human readable format.
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Format sample rate in Hz to human readable format.
 */
export function formatSampleRate(sampleRate: number): string {
  return sampleRate >= 1000
    ? `${(sampleRate / 1000).toFixed(1)}kHz`
    : `${sampleRate}Hz`;
}

/**
 * Format bit depth to human readable format.
 */
export function formatBitDepth(bitDepth: number): string {
  return `${bitDepth}-bit`;
}

/**
 * Format channel count to human readable format.
 */
export function formatChannels(channels: number): string {
  switch (channels) {
    case 1:
      return 'Mono';
    case 2:
      return 'Stereo';
    default:
      return `${channels} channels`;
  }
}

/**
 * Format decibels to human readable format.
 */
export function formatDecibels(db: number): string {
  return `${db.toFixed(1)} dB`;
}

/**
 * Format frequency to human readable format.
 */
export function formatFrequency(hz: number): string {
  if (hz >= 1000) {
    return `${(hz / 1000).toFixed(1)}kHz`;
  }
  return `${Math.round(hz)}Hz`;
}

/**
 * Format milliseconds to human readable format.
 */
export function formatMilliseconds(ms: number): string {
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  return `${Math.round(ms)}ms`;
}

/**
 * Format ratio to human readable format.
 */
export function formatRatio(ratio: number): string {
  return `${ratio.toFixed(1)}:1`;
}