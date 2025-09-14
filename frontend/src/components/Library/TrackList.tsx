import {
  Stack,
  Group,
  Text,
  ActionIcon,
  UnstyledButton,
  Box,
} from '@mantine/core';
import {
  IconPlayCircle,
  IconStar,
  IconStarFilled,
  IconDotsVertical,
} from '@tabler/icons-react';
import { Track } from './types';
import { useLibraryStore } from './store';
import { formatDuration } from '../../utils/format';

interface TrackListProps {
  tracks: Track[];
}

export function TrackList({ tracks }: TrackListProps) {
  const toggleFavorite = useLibraryStore(state => state.toggleFavorite);
  const setCurrentTrack = useLibraryStore(state => state.setCurrentTrack);

  return (
    <Stack gap="xs">
      {tracks.map(track => (
        <UnstyledButton
          key={track.id}
          onClick={() => setCurrentTrack(track)}
          p="xs"
          style={(theme) => ({
            borderRadius: theme.radius.sm,
            '&:hover': {
              backgroundColor: theme.colorScheme === 'dark'
                ? theme.colors.dark[6]
                : theme.colors.gray[0],
            },
          })}
        >
          <Group justify="space-between" wrap="nowrap">
            <Group gap="sm" wrap="nowrap">
              <ActionIcon
                variant="subtle"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setCurrentTrack(track);
                }}
              >
                <IconPlayCircle size={18} />
              </ActionIcon>

              <Box>
                <Text size="sm" truncate>
                  {track.title}
                </Text>
                <Text size="xs" c="dimmed" truncate>
                  {track.artist}
                </Text>
              </Box>
            </Group>

            <Group gap="xs" wrap="nowrap">
              <Text size="xs" c="dimmed">
                {formatDuration(track.duration)}
              </Text>

              <ActionIcon
                variant="subtle"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavorite(track.id);
                }}
              >
                {track.isFavorite ? (
                  <IconStarFilled size={16} color="yellow" />
                ) : (
                  <IconStar size={16} />
                )}
              </ActionIcon>

              <ActionIcon
                variant="subtle"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  // TODO: Show track menu
                }}
              >
                <IconDotsVertical size={16} />
              </ActionIcon>
            </Group>
          </Group>
        </UnstyledButton>
      ))}
    </Stack>
  );
}