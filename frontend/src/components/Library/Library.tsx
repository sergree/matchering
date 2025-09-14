import { useState } from 'react';
import {
  Box,
  Paper,
  Title,
  Tabs,
  Text,
  ScrollArea,
  Stack,
  ActionIcon,
  Group,
} from '@mantine/core';
import { IconMusic, IconPlaylist, IconStar, IconHistory } from '@tabler/icons-react';
import { TrackList } from './TrackList';
import { useLibraryStore } from './store';

export function Library() {
  const [activeTab, setActiveTab] = useState('tracks');
  const tracks = useLibraryStore(state => state.tracks);
  const playlists = useLibraryStore(state => state.playlists);

  return (
    <Paper shadow="sm" p="md" h="100vh">
      <Box mb="md">
        <Title order={4}>Library</Title>
      </Box>

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value as string)}>
        <Tabs.List>
          <Tabs.Tab value="tracks" leftSection={<IconMusic size={16} />}>
            Tracks
          </Tabs.Tab>
          <Tabs.Tab value="playlists" leftSection={<IconPlaylist size={16} />}>
            Playlists
          </Tabs.Tab>
          <Tabs.Tab value="favorites" leftSection={<IconStar size={16} />}>
            Favorites
          </Tabs.Tab>
          <Tabs.Tab value="recent" leftSection={<IconHistory size={16} />}>
            Recent
          </Tabs.Tab>
        </Tabs.List>

        <ScrollArea h="calc(100vh - 150px)" mt="md">
          <Tabs.Panel value="tracks">
            <TrackList tracks={tracks} />
          </Tabs.Panel>

          <Tabs.Panel value="playlists">
            <Stack gap="xs">
              {playlists.map(playlist => (
                <Group key={playlist.id} justify="space-between">
                  <Text size="sm">{playlist.name}</Text>
                  <Text size="xs" c="dimmed">
                    {playlist.trackCount} tracks
                  </Text>
                </Group>
              ))}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="favorites">
            <TrackList tracks={tracks.filter(track => track.isFavorite)} />
          </Tabs.Panel>

          <Tabs.Panel value="recent">
            <TrackList tracks={tracks.slice().sort((a, b) => 
              new Date(b.lastPlayed).getTime() - new Date(a.lastPlayed).getTime()
            )} />
          </Tabs.Panel>
        </ScrollArea>
      </Tabs>
    </Paper>
  );
}