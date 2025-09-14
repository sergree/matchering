import { useEffect, useRef, useState } from 'react';
import {
  Paper,
  Stack,
  Group,
  ActionIcon,
  Slider,
  Text,
  Box,
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerSkipBack,
  IconPlayerSkipForward,
  IconVolume,
  IconVolume3,
} from '@tabler/icons-react';
import WaveSurfer from 'wavesurfer.js';
import { useLibraryStore } from '../Library/store';
import { formatDuration } from '../../utils/format';

export function Player() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(1);
  
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const currentTrack = useLibraryStore(state => state.currentTrack);

  useEffect(() => {
    if (waveformRef.current) {
      wavesurferRef.current = WaveSurfer.create({
        container: waveformRef.current,
        waveColor: '#A8A8A8',
        progressColor: '#2D9CDB',
        cursorColor: '#FFFFFF',
        barWidth: 2,
        barGap: 1,
        height: 60,
        normalize: true,
      });

      wavesurferRef.current.on('ready', () => {
        setDuration(wavesurferRef.current?.getDuration() || 0);
      });

      wavesurferRef.current.on('audioprocess', () => {
        setCurrentTime(wavesurferRef.current?.getCurrentTime() || 0);
      });

      wavesurferRef.current.on('finish', () => {
        setIsPlaying(false);
      });

      return () => {
        wavesurferRef.current?.destroy();
      };
    }
  }, []);

  useEffect(() => {
    if (currentTrack && wavesurferRef.current) {
      wavesurferRef.current.load(currentTrack.path);
    }
  }, [currentTrack]);

  const togglePlayback = () => {
    if (wavesurferRef.current) {
      if (isPlaying) {
        wavesurferRef.current.pause();
      } else {
        wavesurferRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (value: number) => {
    if (wavesurferRef.current) {
      wavesurferRef.current.seekTo(value / duration);
    }
  };

  const handleVolumeChange = (value: number) => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(value);
      setVolume(value);
    }
  };

  return (
    <Paper shadow="sm" p="md">
      <Stack>
        {/* Track Info */}
        <Group justify="center">
          <Text size="sm" fw={500}>
            {currentTrack?.title || 'No track selected'}
          </Text>
          <Text size="sm" c="dimmed">
            {currentTrack?.artist}
          </Text>
        </Group>

        {/* Waveform */}
        <Box ref={waveformRef} h={60} />

        {/* Controls */}
        <Group justify="center">
          <ActionIcon
            variant="subtle"
            size="lg"
            onClick={() => {/* Previous track */}}
          >
            <IconPlayerSkipBack />
          </ActionIcon>

          <ActionIcon
            variant="filled"
            size="xl"
            radius="xl"
            onClick={togglePlayback}
          >
            {isPlaying ? <IconPlayerPause /> : <IconPlayerPlay />}
          </ActionIcon>

          <ActionIcon
            variant="subtle"
            size="lg"
            onClick={() => {/* Next track */}}
          >
            <IconPlayerSkipForward />
          </ActionIcon>
        </Group>

        {/* Progress */}
        <Group gap="xs">
          <Text size="xs" w={40}>
            {formatDuration(currentTime)}
          </Text>

          <Slider
            flex={1}
            value={currentTime}
            onChange={handleSeek}
            max={duration}
            label={formatDuration}
            size="xs"
          />

          <Text size="xs" w={40}>
            {formatDuration(duration)}
          </Text>
        </Group>

        {/* Volume */}
        <Group>
          <ActionIcon
            variant="subtle"
            size="sm"
            onClick={() => handleVolumeChange(volume === 0 ? 1 : 0)}
          >
            {volume === 0 ? <IconVolume3 /> : <IconVolume />}
          </ActionIcon>

          <Slider
            w={100}
            value={volume}
            onChange={handleVolumeChange}
            min={0}
            max={1}
            step={0.01}
            size="xs"
          />
        </Group>
      </Stack>
    </Paper>
  );
}