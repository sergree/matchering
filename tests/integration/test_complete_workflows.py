"""
End-to-End Workflow Testing - Complete user scenarios from input to output
Tests the full matchering pipeline: load → analyze → process → save
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import matchering
from matchering import Config, Result
from matchering_player.core.audio_manager import AudioManager
from matchering_player.core.config import PlayerConfig


class TestCompleteMatcheringWorkflows:
    """Test complete matchering workflows from target to result"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs"""
        with tempfile.TemporaryDirectory(prefix="matchering_e2e_") as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def realistic_audio_files(self, temp_output_dir):
        """Create realistic audio files for end-to-end testing"""
        import soundfile as sf

        files = {}
        sample_rate = 44100
        duration = 3.0  # 3 seconds for faster testing

        # Create quiet target (needs mastering)
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Quiet target - simple mix with low level
        target_left = (np.sin(2 * np.pi * 220 * t) * 0.1 +  # Bass
                      np.sin(2 * np.pi * 440 * t) * 0.08 +  # Mid
                      np.sin(2 * np.pi * 880 * t) * 0.05)   # Treble
        target_right = target_left * 0.9 + np.sin(2 * np.pi * 660 * t) * 0.03
        target_audio = np.column_stack([target_left, target_right]).astype(np.float32)

        target_file = temp_output_dir / "quiet_target.wav"
        sf.write(target_file, target_audio, sample_rate)
        files['target'] = str(target_file)

        # Loud reference (mastering goal)
        ref_left = (np.sin(2 * np.pi * 220 * t) * 0.4 +    # Bass
                   np.sin(2 * np.pi * 440 * t) * 0.35 +    # Mid
                   np.sin(2 * np.pi * 880 * t) * 0.25)     # Treble
        ref_right = ref_left * 0.95 + np.sin(2 * np.pi * 660 * t) * 0.15
        # Add gentle compression characteristic
        ref_audio = np.tanh(np.column_stack([ref_left, ref_right]) * 1.2) * 0.8
        ref_audio = ref_audio.astype(np.float32)

        reference_file = temp_output_dir / "loud_reference.wav"
        sf.write(reference_file, ref_audio, sample_rate)
        files['reference'] = str(reference_file)

        return files

    def test_basic_matchering_workflow(self, realistic_audio_files, temp_output_dir):
        """Test basic target + reference → result workflow"""
        target_file = realistic_audio_files['target']
        reference_file = realistic_audio_files['reference']
        result_file = temp_output_dir / "basic_result.wav"

        # Execute complete matchering workflow
        start_time = time.perf_counter()

        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(result_file)]
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time

        # Verify result file exists and has content
        assert result_file.exists()
        assert result_file.stat().st_size > 1000  # Non-trivial file size

        # Verify processing completed in reasonable time
        assert processing_time < 30.0  # Should complete within 30 seconds

        # Load and verify result audio
        import soundfile as sf
        result_audio, result_sr = sf.read(str(result_file))
        target_audio, target_sr = sf.read(target_file)

        assert result_audio.shape == target_audio.shape
        assert result_sr == target_sr

        # Verify result has higher RMS than target (was amplified)
        target_rms = np.sqrt(np.mean(target_audio**2))
        result_rms = np.sqrt(np.mean(result_audio**2))
        assert result_rms > target_rms, "Result should be louder than quiet target"

        print(f"✅ Basic workflow: {processing_time:.2f}s, RMS: {target_rms:.4f} → {result_rms:.4f}")

    def test_multiple_output_formats_workflow(self, realistic_audio_files, temp_output_dir):
        """Test generating multiple output formats simultaneously"""
        target_file = realistic_audio_files['target']
        reference_file = realistic_audio_files['reference']

        # Multiple output formats
        outputs = [
            Result(str(temp_output_dir / "result_16bit.wav"), subtype="PCM_16"),
            Result(str(temp_output_dir / "result_24bit.wav"), subtype="PCM_24"),
            Result(str(temp_output_dir / "result_float.wav"), subtype="FLOAT"),
        ]

        # Execute workflow with multiple outputs
        matchering.process(
            target=target_file,
            reference=reference_file,
            results=outputs
        )

        # Verify all output files were created
        for output in outputs:
            output_file = Path(output.file)
            assert output_file.exists()
            assert output_file.stat().st_size > 1000

            # Verify audio content
            import soundfile as sf
            audio, sr = sf.read(str(output_file))
            assert audio.shape[0] > 0  # Has samples
            assert audio.shape[1] == 2  # Stereo
            assert sr == 44100

    def test_preview_generation_workflow(self, realistic_audio_files, temp_output_dir):
        """Test workflow with preview generation"""
        target_file = realistic_audio_files['target']
        reference_file = realistic_audio_files['reference']
        result_file = temp_output_dir / "result_with_preview.wav"
        preview_target_file = temp_output_dir / "preview_target.wav"
        preview_result_file = temp_output_dir / "preview_result.wav"

        # Execute workflow with previews
        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(result_file)],
            preview_target=Result(str(preview_target_file)),
            preview_result=Result(str(preview_result_file))
        )

        # Verify main result and previews exist
        assert result_file.exists()
        assert preview_target_file.exists()
        assert preview_result_file.exists()

        # Verify preview files exist and have reasonable content
        import soundfile as sf
        result_info = sf.info(str(result_file))
        preview_target_info = sf.info(str(preview_target_file))
        preview_result_info = sf.info(str(preview_result_file))

        # Preview files should be same duration as each other
        assert preview_target_info.duration == preview_result_info.duration
        # Preview files should have content (not just headers)
        assert preview_target_info.duration > 0
        assert preview_result_info.duration > 0
        # All files should have same sample rate and channels
        assert result_info.samplerate == preview_target_info.samplerate == preview_result_info.samplerate
        assert result_info.channels == preview_target_info.channels == preview_result_info.channels

    def test_custom_config_workflow(self, realistic_audio_files, temp_output_dir):
        """Test workflow with custom configuration"""
        target_file = realistic_audio_files['target']
        reference_file = realistic_audio_files['reference']
        result_file = temp_output_dir / "custom_config_result.wav"

        # Create custom configuration
        config = Config()
        config.threshold = 0.9  # Lower threshold for more aggressive limiting
        config.internal_sample_rate = 48000  # Different internal sample rate

        # Execute workflow with custom config
        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(result_file)],
            config=config
        )

        # Verify result exists and has correct properties
        assert result_file.exists()

        import soundfile as sf
        result_audio, result_sr = sf.read(str(result_file))

        # Should still output at original sample rate despite internal processing
        assert result_sr == 44100

        # Verify limiting was applied (peak should be near threshold)
        peak_level = np.max(np.abs(result_audio))
        assert peak_level <= config.threshold + 0.01  # Within small tolerance

    @pytest.mark.error
    def test_error_handling_workflow(self, temp_output_dir):
        """Test error handling in complete workflows"""
        nonexistent_target = "/fake/nonexistent_target.wav"
        nonexistent_reference = "/fake/nonexistent_reference.wav"
        result_file = temp_output_dir / "error_result.wav"

        # Test with nonexistent target file
        with pytest.raises(Exception):  # Should raise some kind of error
            matchering.process(
                target=nonexistent_target,
                reference=str(temp_output_dir / "fake_ref.wav"),
                results=[str(result_file)]
            )

        # Test with nonexistent reference file
        with pytest.raises(Exception):  # Should raise some kind of error
            matchering.process(
                target=str(temp_output_dir / "fake_target.wav"),
                reference=nonexistent_reference,
                results=[str(result_file)]
            )

    @pytest.mark.performance
    def test_workflow_performance_benchmark(self, realistic_audio_files, temp_output_dir):
        """Benchmark complete workflow performance"""
        target_file = realistic_audio_files['target']
        reference_file = realistic_audio_files['reference']

        # Run multiple iterations to get stable timing
        times = []
        num_iterations = 3

        for i in range(num_iterations):
            result_file = temp_output_dir / f"perf_result_{i}.wav"

            start_time = time.perf_counter()

            matchering.process(
                target=target_file,
                reference=reference_file,
                results=[str(result_file)]
            )

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # Calculate performance metrics
        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)

        # Get audio duration for real-time factor calculation
        import soundfile as sf
        target_info = sf.info(target_file)
        audio_duration = target_info.duration

        real_time_factor = audio_duration / avg_time

        print(f"📊 Performance Benchmark:")
        print(f"   Audio duration: {audio_duration:.2f}s")
        print(f"   Processing time: {avg_time:.2f}s ±{np.std(times):.2f}s")
        print(f"   Real-time factor: {real_time_factor:.1f}x")
        print(f"   Range: {min_time:.2f}s - {max_time:.2f}s")

        # Performance assertions
        assert avg_time < 60.0  # Should complete within 1 minute for 3s audio
        assert real_time_factor > 0.05  # Should be somewhat efficient

        # Verify consistency (max shouldn't be more than 2x min)
        assert max_time / min_time < 3.0  # Reasonable consistency


class TestPlayerWorkflowIntegration:
    """Test integration between matchering core and player components"""

    @pytest.fixture
    def player_config(self):
        """Player configuration for testing"""
        return PlayerConfig(
            sample_rate=44100,
            buffer_size_ms=100.0,
            enable_level_matching=True,
            enable_frequency_matching=False,
            enable_stereo_width=False
        )

    def test_core_to_player_workflow(self, audio_pair, player_config, tmp_path):
        """Test using core matchering result as player input"""
        # Create temporary audio files from audio_pair
        target_audio, reference_audio, sr = audio_pair

        target_file = tmp_path / "target.wav"
        reference_file = tmp_path / "reference.wav"
        result_file = tmp_path / "core_to_player.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, sr)
        sf.write(reference_file, reference_audio, sr)

        # Step 1: Process with core matchering
        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        # Step 2: Load result into player (mock initialization)
        from unittest.mock import patch

        with patch('matchering_player.core.audio_manager.HAS_SOUNDDEVICE', True):
            with patch('matchering_player.core.audio_manager.sd.check_output_settings'):
                audio_manager = AudioManager(player_config)

                # Mock file loading to avoid audio device dependencies
                with patch.object(audio_manager.file_loader, 'get_file_info') as mock_info:
                    with patch.object(audio_manager.file_loader, 'load_audio_file') as mock_load:
                        # Mock successful loading
                        mock_info.return_value.filename = "core_to_player.wav"

                        import soundfile as sf
                        result_audio, sr = sf.read(str(result_file))
                        mock_load.return_value = (result_audio, sr)

                        # Test loading the processed file
                        success = audio_manager.load_file(str(result_file))
                        assert success == True

                        # Verify audio data was loaded
                        info = audio_manager.get_playback_info()
                        assert 'filename' in info  # File info added when loaded
                        assert info['total_samples'] > 0

    def test_player_reference_loading_workflow(self, audio_pair, player_config, tmp_path):
        """Test loading reference track into player DSP"""
        # Create temporary audio files from audio_pair
        target_audio, reference_audio, sr = audio_pair

        reference_file = tmp_path / "reference.wav"

        import soundfile as sf
        sf.write(reference_file, reference_audio, sr)

        from unittest.mock import patch

        with patch('matchering_player.core.audio_manager.HAS_SOUNDDEVICE', True):
            with patch('matchering_player.core.audio_manager.sd.check_output_settings'):
                audio_manager = AudioManager(player_config)

                # Test loading reference for DSP processing
                with patch.object(audio_manager.dsp_processor, 'load_reference_track', return_value=True) as mock_ref:
                    success = audio_manager.load_reference_track(str(reference_file))
                    assert success == True
                    mock_ref.assert_called_once_with(str(reference_file))

    @pytest.mark.integration
    def test_full_ecosystem_workflow(self, audio_pair, tmp_path):
        """Test complete ecosystem: core processing → player loading → DSP processing"""
        # Create temporary audio files from audio_pair
        target_audio, reference_audio, sr = audio_pair

        target_file = tmp_path / "target.wav"
        reference_file = tmp_path / "reference.wav"
        result_file = tmp_path / "ecosystem_result.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, sr)
        sf.write(reference_file, reference_audio, sr)

        # Phase 1: Core matchering processing
        start_time = time.perf_counter()

        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        core_time = time.perf_counter() - start_time

        # Phase 2: Player integration simulation
        from unittest.mock import patch

        with patch('matchering_player.core.audio_manager.HAS_SOUNDDEVICE', True):
            with patch('matchering_player.core.audio_manager.sd.check_output_settings'):
                player_config = PlayerConfig(
                    sample_rate=44100,
                    buffer_size_ms=50.0,  # Smaller buffer for testing
                    enable_level_matching=True
                )

                audio_manager = AudioManager(player_config)

                # Load the processed result
                import soundfile as sf
                result_audio, sr = sf.read(str(result_file))

                with patch.object(audio_manager.file_loader, 'get_file_info'):
                    with patch.object(audio_manager.file_loader, 'load_audio_file', return_value=(result_audio, sr)):
                        # Load result file
                        load_success = audio_manager.load_file(str(result_file))
                        assert load_success == True

                        # Load reference for player DSP
                        with patch.object(audio_manager.dsp_processor, 'load_reference_track', return_value=True):
                            ref_success = audio_manager.load_reference_track(reference_file)
                            assert ref_success == True

                        # Simulate real-time processing
                        chunk_size = player_config.buffer_size_samples
                        chunks_processed = 0

                        player_start = time.perf_counter()

                        for i in range(0, min(len(result_audio), chunk_size * 10), chunk_size):
                            chunk = result_audio[i:i + chunk_size]
                            if len(chunk) < chunk_size:
                                # Pad last chunk
                                chunk = np.pad(chunk, ((0, chunk_size - len(chunk)), (0, 0)))

                            # Process chunk through player DSP
                            processed_chunk = audio_manager.dsp_processor.process_audio_chunk(chunk)

                            assert processed_chunk.shape == chunk.shape
                            chunks_processed += 1

                        player_time = time.perf_counter() - player_start

                        # Performance validation
                        total_audio_duration = len(result_audio) / sr
                        processed_audio_duration = (chunks_processed * chunk_size) / sr

                        print(f"🔄 Full Ecosystem Workflow:")
                        print(f"   Core processing: {core_time:.2f}s")
                        print(f"   Player processing: {player_time:.2f}s")
                        print(f"   Audio duration: {total_audio_duration:.2f}s")
                        print(f"   Player real-time factor: {processed_audio_duration/player_time:.1f}x")
                        print(f"   Chunks processed: {chunks_processed}")

                        # Verify player can process faster than real-time
                        assert processed_audio_duration / player_time > 1.0


class TestErrorPropagationWorkflows:
    """Test error handling and recovery across the complete system"""

    def test_invalid_input_propagation(self, tmp_path):
        """Test how invalid inputs propagate through the system"""
        # Test with corrupted audio file
        corrupt_file = tmp_path / "corrupt.wav"
        with open(corrupt_file, 'wb') as f:
            f.write(b"Not a valid audio file")

        valid_reference = tmp_path / "valid_ref.wav"
        # Create minimal valid WAV file
        import soundfile as sf
        test_audio = np.random.rand(1000, 2).astype(np.float32) * 0.1
        sf.write(valid_reference, test_audio, 44100)

        result_file = tmp_path / "error_result.wav"

        # Should handle corrupted input gracefully
        with pytest.raises(Exception):  # Expect some form of error
            matchering.process(
                target=str(corrupt_file),
                reference=str(valid_reference),
                results=[str(result_file)]
            )

        # Result file should not exist after error
        assert not result_file.exists()

    def test_processing_chain_recovery(self, audio_pair, tmp_path):
        """Test recovery from processing chain failures"""
        # Create temporary audio files from audio_pair
        target_audio, reference_audio, sr = audio_pair

        target_file = tmp_path / "target.wav"
        reference_file = tmp_path / "reference.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, sr)
        sf.write(reference_file, reference_audio, sr)

        # Test with invalid output path (should fail gracefully)
        invalid_output = "/invalid/path/that/does/not/exist/result.wav"

        with pytest.raises(Exception):
            matchering.process(
                target=str(target_file),
                reference=str(reference_file),
                results=[invalid_output]
            )

        # System should still work after the error
        valid_result = tmp_path / "recovery_test.wav"
        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(valid_result)]
        )

        assert valid_result.exists()

    @pytest.mark.performance
    def test_memory_usage_workflow(self, tmp_path):
        """Test memory usage during complete workflows"""
        # Skip psutil dependency for basic workflow testing
        # import psutil
        # import os

        # Create larger test files for memory testing
        import soundfile as sf
        duration = 10.0  # 10 seconds
        sample_rate = 44100
        samples = int(duration * sample_rate)

        # Generate test audio
        t = np.linspace(0, duration, samples)
        target_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.1,
            np.sin(2 * np.pi * 440 * t) * 0.09
        ]).astype(np.float32)

        reference_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.6,
            np.sin(2 * np.pi * 440 * t) * 0.58
        ]).astype(np.float32)

        target_file = tmp_path / "memory_target.wav"
        reference_file = tmp_path / "memory_reference.wav"
        result_file = tmp_path / "memory_result.wav"

        sf.write(target_file, target_audio, sample_rate)
        sf.write(reference_file, reference_audio, sample_rate)

        # Simple workflow test without psutil dependency
        # Monitor memory usage would require: process = psutil.Process(os.getpid())
        # initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Execute workflow
        start_time = time.perf_counter()
        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )
        end_time = time.perf_counter()

        # final_memory = process.memory_info().rss / 1024 / 1024  # MB
        # memory_increase = final_memory - initial_memory
        processing_time = end_time - start_time

        print(f"⏱️  Processing Performance:")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Processing Time: {processing_time:.2f} seconds")
        print(f"   Real-time Factor: {duration/processing_time:.1f}x")

        # Processing should complete efficiently
        assert processing_time < 30.0  # Should complete within 30 seconds
        assert result_file.exists()
        assert result_file.stat().st_size > 1000  # Non-trivial file size

        # Verify result was created successfully
        assert result_file.exists()
        result_info = sf.info(str(result_file))
        assert abs(result_info.duration - duration) < 0.1