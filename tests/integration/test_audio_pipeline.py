"""
Integration tests for complete audio pipeline
"""

import pytest
import numpy as np
import time
from pathlib import Path
from tests.conftest import HAS_SOUNDFILE, HAS_PLAYER, assert_rms_similar


@pytest.mark.integration
@pytest.mark.player
@pytest.mark.audio
@pytest.mark.files
class TestAudioPipeline:
    """Test complete audio processing pipeline"""

    def test_pipeline_initialization(self, test_config):
        """Test pipeline initialization"""
        MatcheringPlayer = pytest.importorskip("matchering_player.core.player").MatcheringPlayer

        try:
            player = MatcheringPlayer(test_config)

            # Test basic properties
            assert player.config.buffer_size_ms == test_config.buffer_size_ms
            assert player.config.enable_level_matching == test_config.enable_level_matching

            # Test device enumeration
            devices = player.get_audio_devices()
            assert 'output' in devices

            # Test supported formats
            formats = player.get_supported_formats()
            assert len(formats) > 0

        except Exception as e:
            if "PyAudio" in str(e) or "audio device" in str(e):
                pytest.skip("Audio system not available")
            raise

    def test_file_loading_pipeline(self, test_config, test_audio_files):
        """Test file loading and info retrieval"""
        MatcheringPlayer = pytest.importorskip("matchering_player.core.player").MatcheringPlayer

        try:
            player = MatcheringPlayer(test_config)

            # Test file loading
            target_file = test_audio_files["quiet_target.wav"]
            success = player.load_file(target_file)
            assert success, "Failed to load test file"

            # Check playback info
            info = player.get_playback_info()
            assert info['duration_seconds'] > 0
            assert info['state'] == 'stopped'

            # Test reference loading
            reference_file = test_audio_files["loud_reference.wav"]
            ref_success = player.load_reference_track(reference_file)
            assert ref_success, "Failed to load reference"

        except Exception as e:
            if "PyAudio" in str(e):
                pytest.skip("Audio system not available")
            raise

    def test_dsp_pipeline_processing(self, test_config, test_audio_files):
        """Test DSP processing without actual playback"""
        MatcheringPlayer = pytest.importorskip("matchering_player.core.player").MatcheringPlayer

        try:
            player = MatcheringPlayer(test_config)

            # Load files
            player.load_file(test_audio_files["quiet_target.wav"])
            player.load_reference_track(test_audio_files["loud_reference.wav"])

            # Test DSP status
            info = player.get_playback_info()
            dsp_stats = info.get('dsp', {})

            # Test effect control
            player.set_effect_enabled('level_matching', False)
            player.set_effect_enabled('level_matching', True)

            # Test parameter setting
            player.set_effect_parameter('level_matching', 'smoothing_speed', 0.5)

        except Exception as e:
            if "PyAudio" in str(e):
                pytest.skip("Audio system not available")
            raise

    @pytest.mark.slow
    def test_playback_simulation(self, test_config, test_audio_files):
        """Test playback functionality (may skip if no audio device)"""
        MatcheringPlayer = pytest.importorskip("matchering_player.core.player").MatcheringPlayer

        try:
            player = MatcheringPlayer(test_config)
            player.load_file(test_audio_files["short_audio.wav"])

            # Set up callbacks to track playback
            position_updates = []
            state_changes = []

            def position_callback(pos):
                position_updates.append(pos)

            def state_callback(state):
                state_changes.append(state)

            player.set_position_callback(position_callback)
            player.set_state_callback(state_callback)

            # Test play (might fail if no audio device)
            play_success = player.play()

            if play_success:
                # Let it run briefly
                time.sleep(0.2)

                # Test pause
                player.pause()
                time.sleep(0.1)

                # Test resume
                player.play()
                time.sleep(0.1)

                # Test stop
                player.stop()

                assert len(state_changes) > 0, "Should have received state changes"
            else:
                pytest.skip("Playback failed (likely no audio device)")

        except Exception as e:
            if "PyAudio" in str(e) or "audio device" in str(e):
                pytest.skip("Audio system not available")
            raise


@pytest.mark.integration
@pytest.mark.core
@pytest.mark.audio
@pytest.mark.files
@pytest.mark.slow
class TestMatcheringPipeline:
    """Test complete Matchering processing pipeline"""

    def test_full_matchering_process(self, test_audio_files, temp_dir):
        """Test end-to-end matchering processing"""
        matchering = pytest.importorskip("matchering")
        sf = pytest.importorskip("soundfile")

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]
        output_file = temp_dir / "matched_output.wav"

        # Run matchering
        start_time = time.perf_counter()
        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(output_file)]
        )
        end_time = time.perf_counter()

        processing_time = end_time - start_time

        # Verify output file
        assert output_file.exists(), "Output file was not created"

        # Load and verify output
        output_audio, output_sr = sf.read(output_file)
        target_audio, target_sr = sf.read(target_file)
        reference_audio, reference_sr = sf.read(reference_file)

        assert output_audio.shape == target_audio.shape, "Output shape mismatch"

        # Check that level was adjusted
        target_rms = np.sqrt(np.mean(target_audio**2))
        output_rms = np.sqrt(np.mean(output_audio**2))
        reference_rms = np.sqrt(np.mean(reference_audio**2))

        # Output should be closer to reference level
        target_ref_diff = abs(target_rms - reference_rms)
        output_ref_diff = abs(output_rms - reference_rms)

        assert output_ref_diff < target_ref_diff, "Matchering should improve level matching"
        assert processing_time < 30.0, "Processing should complete in reasonable time"

    def test_matchering_different_formats(self, temp_dir):
        """Test matchering with different audio formats"""
        matchering = pytest.importorskip("matchering")
        sf = pytest.importorskip("soundfile")

        # Create test files with different characteristics
        def create_test_audio(duration, sr, amplitude, freq=440):
            samples = int(duration * sr)
            t = np.linspace(0, duration, samples)
            left = np.sin(2 * np.pi * freq * t) * amplitude
            right = np.sin(2 * np.pi * freq * t * 1.01) * amplitude * 0.9
            return np.column_stack([left, right]).astype(np.float32)

        # Test different sample rates
        for sample_rate in [44100, 48000]:
            target_audio = create_test_audio(2.0, sample_rate, 0.1)
            reference_audio = create_test_audio(2.0, sample_rate, 0.8)

            target_file = temp_dir / f"target_{sample_rate}.wav"
            reference_file = temp_dir / f"reference_{sample_rate}.wav"
            output_file = temp_dir / f"output_{sample_rate}.wav"

            sf.write(target_file, target_audio, sample_rate)
            sf.write(reference_file, reference_audio, sample_rate)

            # Process
            matchering.process(
                target=str(target_file),
                reference=str(reference_file),
                results=[str(output_file)]
            )

            assert output_file.exists(), f"Failed to process {sample_rate}Hz files"

            # Verify output
            output_audio, output_sr = sf.read(output_file)
            assert output_sr == sample_rate, f"Sample rate mismatch for {sample_rate}Hz"


@pytest.mark.integration
@pytest.mark.player
@pytest.mark.performance
class TestPerformanceIntegration:
    """Test performance across integrated components"""

    def test_realtime_processing_performance(self, test_config, sine_wave):
        """Test real-time processing performance"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(test_config)
        test_chunk, _ = sine_wave(test_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = test_config.buffer_size_samples
        if len(test_chunk) != expected_samples:
            test_chunk = test_chunk[:expected_samples] if len(test_chunk) > expected_samples else np.pad(test_chunk, ((0, expected_samples - len(test_chunk)), (0, 0)), 'constant')

        # Measure processing performance
        processor.start_processing()

        # Warmup
        for _ in range(10):
            processor.process_audio_chunk(test_chunk)

        # Measure
        num_chunks = 100
        start_time = time.perf_counter()

        for _ in range(num_chunks):
            processor.process_audio_chunk(test_chunk)

        end_time = time.perf_counter()

        processing_time = end_time - start_time
        real_time = (num_chunks * test_config.buffer_size_samples) / test_config.sample_rate
        cpu_usage = processing_time / real_time

        processor.stop_processing()

        # Performance should be reasonable for real-time use
        assert cpu_usage < 2.0, f"CPU usage too high: {cpu_usage:.1%}"

    def test_memory_usage_stability(self, test_config, sine_wave):
        """Test memory usage stability over time"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(test_config)
        test_chunk, _ = sine_wave(test_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = test_config.buffer_size_samples
        if len(test_chunk) != expected_samples:
            test_chunk = test_chunk[:expected_samples] if len(test_chunk) > expected_samples else np.pad(test_chunk, ((0, expected_samples - len(test_chunk)), (0, 0)), 'constant')

        processor.start_processing()

        # Process many chunks to test for memory leaks
        for i in range(1000):
            result = processor.process_audio_chunk(test_chunk)

            # Periodically check that processing is still working
            if i % 100 == 0:
                assert result.shape == test_chunk.shape, f"Processing failed at iteration {i}"

        processor.stop_processing()

        # If we get here without crashing, memory usage is probably stable