import {
  Paper,
  Stack,
  Title,
  Tabs,
  Slider,
  Switch,
  Group,
  Text,
  Select,
  Button,
} from '@mantine/core';
import {
  IconWaveform,
  IconWaveSine,
  IconStereo,
  IconAdjustments,
} from '@tabler/icons-react';
import { useProcessingStore } from './store';

export function ProcessingPanel() {
  const {
    isEnabled,
    toggleEnabled,
    updateEqGains,
    updateCompressorParams,
    updateStereoParams,
    updateLimiterParams,
    eqGains,
    compressorParams,
    stereoParams,
    limiterParams,
  } = useProcessingStore();

  return (
    <Paper shadow="sm" p="md" h="100vh">
      <Stack>
        <Group justify="space-between" align="center">
          <Title order={4}>Processing</Title>
          <Switch
            checked={isEnabled}
            onChange={(event) => toggleEnabled(event.currentTarget.checked)}
          />
        </Group>

        <Tabs defaultValue="eq">
          <Tabs.List>
            <Tabs.Tab value="eq" leftSection={<IconWaveform size={16} />}>
              EQ
            </Tabs.Tab>
            <Tabs.Tab value="dynamics" leftSection={<IconWaveSine size={16} />}>
              Dynamics
            </Tabs.Tab>
            <Tabs.Tab value="stereo" leftSection={<IconStereo size={16} />}>
              Stereo
            </Tabs.Tab>
            <Tabs.Tab value="limiter" leftSection={<IconAdjustments size={16} />}>
              Limiter
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="eq" pt="sm">
            <Stack gap="xs">
              {eqGains.map((gain, index) => (
                <Slider
                  key={index}
                  label={`${index + 1}. ${[31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000][index]} Hz`}
                  value={gain}
                  onChange={(value) => updateEqGains(index, value)}
                  min={-12}
                  max={12}
                  step={0.1}
                  size="xs"
                />
              ))}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="dynamics" pt="sm">
            <Stack gap="xs">
              <Slider
                label="Threshold"
                value={compressorParams.threshold}
                onChange={(value) => updateCompressorParams({ threshold: value })}
                min={-60}
                max={0}
                step={0.1}
                size="xs"
              />
              <Slider
                label="Ratio"
                value={compressorParams.ratio}
                onChange={(value) => updateCompressorParams({ ratio: value })}
                min={1}
                max={20}
                step={0.1}
                size="xs"
              />
              <Slider
                label="Attack"
                value={compressorParams.attack}
                onChange={(value) => updateCompressorParams({ attack: value })}
                min={0}
                max={100}
                step={1}
                size="xs"
              />
              <Slider
                label="Release"
                value={compressorParams.release}
                onChange={(value) => updateCompressorParams({ release: value })}
                min={0}
                max={1000}
                step={10}
                size="xs"
              />
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="stereo" pt="sm">
            <Stack gap="xs">
              <Slider
                label="Width"
                value={stereoParams.width}
                onChange={(value) => updateStereoParams({ width: value })}
                min={0}
                max={2}
                step={0.01}
                size="xs"
              />
              <Slider
                label="Rotation"
                value={stereoParams.rotation}
                onChange={(value) => updateStereoParams({ rotation: value })}
                min={-180}
                max={180}
                step={1}
                size="xs"
              />
              <Slider
                label="Balance"
                value={stereoParams.balance}
                onChange={(value) => updateStereoParams({ balance: value })}
                min={-1}
                max={1}
                step={0.01}
                size="xs"
              />
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="limiter" pt="sm">
            <Stack gap="xs">
              <Slider
                label="Threshold"
                value={limiterParams.threshold}
                onChange={(value) => updateLimiterParams({ threshold: value })}
                min={-12}
                max={0}
                step={0.1}
                size="xs"
              />
              <Slider
                label="Release"
                value={limiterParams.release}
                onChange={(value) => updateLimiterParams({ release: value })}
                min={1}
                max={500}
                step={1}
                size="xs"
              />
            </Stack>
          </Tabs.Panel>
        </Tabs>

        <Stack mt="auto">
          <Select
            label="Preset"
            placeholder="Select preset"
            data={[
              { value: 'flat', label: 'Flat' },
              { value: 'warm', label: 'Warm' },
              { value: 'bright', label: 'Bright' },
              { value: 'wide', label: 'Wide Stereo' },
            ]}
          />

          <Button variant="light" size="xs">
            Save Preset
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}