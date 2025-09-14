import { Grid, Container } from '@mantine/core';
import { Library } from '../components/Library';
import { Player } from '../components/Player';
import { ProcessingPanel } from '../components/ProcessingPanel';

export function MainLayout() {
  return (
    <Container fluid>
      <Grid>
        {/* Library Panel */}
        <Grid.Col span={3}>
          <Library />
        </Grid.Col>

        {/* Main Player Area */}
        <Grid.Col span={7}>
          <Player />
        </Grid.Col>

        {/* Processing Panel */}
        <Grid.Col span={2}>
          <ProcessingPanel />
        </Grid.Col>
      </Grid>
    </Container>
  );
}