"""
Unit tests for core matchering processing pipeline
Tests the main process() function and core workflow
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from tests.conftest import HAS_SOUNDFILE, HAS_MATCHERING, assert_audio_equal, assert_rms_similar


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.files
class TestCoreProcessing:
    """Test the main matchering processing pipeline"""

    def test_process_basic_workflow(self, test_audio_files, temp_dir):
        """Test basic process() function workflow"""
        matchering = pytest.importorskip("matchering")

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]
        output_file = temp_dir / "output.wav"

        # Test basic processing with string path
        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(output_file)]
        )

        # Verify output file exists and is valid
        assert output_file.exists(), "Output file should be created"

        # Load and verify the output
        sf = pytest.importorskip("soundfile")
        output_audio, output_sr = sf.read(output_file)
        target_audio, target_sr = sf.read(target_file)
        reference_audio, reference_sr = sf.read(reference_file)

        # Basic validation
        assert output_audio.shape[1] == 2, "Output should be stereo"
        assert output_sr == target_sr, "Output sample rate should match target"
        assert len(output_audio) == len(target_audio), "Output length should match target"

    def test_process_with_result_objects(self, test_audio_files, temp_dir):
        """Test process() with Result objects"""
        matchering = pytest.importorskip("matchering")
        from matchering import Result

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]

        # Test different Result configurations
        results = [
            Result(str(temp_dir / "output_pcm16.wav"), subtype="PCM_16", use_limiter=True),
            Result(str(temp_dir / "output_pcm24.wav"), subtype="PCM_24", use_limiter=False),
            Result(str(temp_dir / "output_normalized.wav"), subtype="PCM_16", use_limiter=False, normalize=True),
        ]

        matchering.process(
            target=target_file,
            reference=reference_file,
            results=results
        )

        # Verify all outputs were created
        for result in results:
            output_path = Path(result.file)
            assert output_path.exists(), f"Output file {result.file} should be created"

        # Load and compare outputs
        sf = pytest.importorskip("soundfile")

        # All outputs should have same length but potentially different amplitudes
        outputs = []
        for result in results:
            audio, sr = sf.read(result.file)
            outputs.append((audio, sr, result))
            assert audio.shape[1] == 2, f"Output {result.file} should be stereo"

        # Compare characteristics
        for i, (audio, sr, result) in enumerate(outputs):
            for j, (other_audio, other_sr, other_result) in enumerate(outputs):
                if i != j:
                    assert len(audio) == len(other_audio), "All outputs should have same length"
                    assert sr == other_sr, "All outputs should have same sample rate"

    def test_process_level_matching_effectiveness(self, test_audio_files, temp_dir):
        """Test that level matching actually works"""
        matchering = pytest.importorskip("matchering")
        sf = pytest.importorskip("soundfile")

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]
        output_file = temp_dir / "level_matched.wav"

        # Process
        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(output_file)]
        )

        # Load all files
        target_audio, target_sr = sf.read(target_file)
        reference_audio, reference_sr = sf.read(reference_file)
        output_audio, output_sr = sf.read(output_file)

        # Calculate RMS levels
        target_rms = np.sqrt(np.mean(target_audio**2))
        reference_rms = np.sqrt(np.mean(reference_audio**2))
        output_rms = np.sqrt(np.mean(output_audio**2))

        print(f"Target RMS: {target_rms:.6f}")
        print(f"Reference RMS: {reference_rms:.6f}")
        print(f"Output RMS: {output_rms:.6f}")

        # Output should be closer to reference than target was
        target_ref_diff = abs(target_rms - reference_rms)
        output_ref_diff = abs(output_rms - reference_rms)

        print(f"Target-Reference RMS difference: {target_ref_diff:.6f}")
        print(f"Output-Reference RMS difference: {output_ref_diff:.6f}")

        # Level matching should improve RMS similarity
        assert output_ref_diff <= target_ref_diff, "Output should be closer to reference RMS than target"

    def test_process_different_sample_rates(self, temp_dir):
        """Test processing files with different sample rates (should fail validation)"""
        matchering = pytest.importorskip("matchering")
        sf = pytest.importorskip("soundfile")

        # Create test files with different sample rates
        def create_test_audio(duration, sr, amplitude):
            samples = int(duration * sr)
            t = np.linspace(0, duration, samples)
            left = np.sin(2 * np.pi * 440 * t) * amplitude
            right = np.sin(2 * np.pi * 440 * t * 1.01) * amplitude * 0.9
            return np.column_stack([left, right]).astype(np.float32)

        # Create files with different rates
        target_sr, reference_sr = 44100, 48000

        target_audio = create_test_audio(3.0, target_sr, 0.2)
        reference_audio = create_test_audio(3.0, reference_sr, 0.7)

        target_file = temp_dir / "target_44k.wav"
        reference_file = temp_dir / "reference_48k.wav"
        output_file = temp_dir / "output_mixed.wav"

        sf.write(target_file, target_audio, target_sr)
        sf.write(reference_file, reference_audio, reference_sr)

        # Files with different sample rates should fail validation
        with pytest.raises(Exception):  # Should raise validation error
            matchering.process(
                target=str(target_file),
                reference=str(reference_file),
                results=[str(output_file)]
            )

    def test_process_custom_config(self, test_audio_files, temp_dir):
        """Test process() with custom Config"""
        matchering = pytest.importorskip("matchering")
        from matchering import Config

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]
        output_file = temp_dir / "custom_config.wav"

        # Create custom config
        config = Config(
            internal_sample_rate=44100,
            fft_size=2048,  # Smaller FFT for testing
            max_length=5 * 60,  # 5 minutes max
            allow_equality=True  # Allow identical files
        )

        # Process with custom config
        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(output_file)],
            config=config
        )

        # Verify output
        assert output_file.exists(), "Output should be created with custom config"

        sf = pytest.importorskip("soundfile")
        output_audio, output_sr = sf.read(output_file)
        assert output_audio.shape[1] == 2, "Output should be stereo"

    def test_process_multiple_outputs(self, test_audio_files, temp_dir):
        """Test process() with multiple output formats"""
        matchering = pytest.importorskip("matchering")
        from matchering import Result

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]

        # Multiple output formats
        results = [
            Result(str(temp_dir / "output1.wav"), subtype="PCM_16"),
            Result(str(temp_dir / "output2.wav"), subtype="PCM_24"),
            str(temp_dir / "output3.wav"),  # String path (should default to PCM_16)
        ]

        matchering.process(
            target=target_file,
            reference=reference_file,
            results=results
        )

        # Verify all outputs
        sf = pytest.importorskip("soundfile")
        for i, result in enumerate(results):
            if isinstance(result, str):
                output_path = Path(result)
            else:
                output_path = Path(result.file)

            assert output_path.exists(), f"Output {i+1} should exist"

            audio, sr = sf.read(output_path)
            assert audio.shape[1] == 2, f"Output {i+1} should be stereo"
            assert len(audio) > 0, f"Output {i+1} should have content"


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.error
class TestCoreProcessingErrors:
    """Test error handling in core processing"""

    def test_process_invalid_target_file(self, test_audio_files, temp_dir):
        """Test process() with invalid target file"""
        matchering = pytest.importorskip("matchering")

        reference_file = test_audio_files["loud_reference.wav"]
        output_file = temp_dir / "output.wav"

        with pytest.raises(Exception):  # ModuleError for target loading
            matchering.process(
                target="nonexistent_target.wav",
                reference=reference_file,
                results=[str(output_file)]
            )

    def test_process_invalid_reference_file(self, test_audio_files, temp_dir):
        """Test process() with invalid reference file"""
        matchering = pytest.importorskip("matchering")

        target_file = test_audio_files["quiet_target.wav"]
        output_file = temp_dir / "output.wav"

        with pytest.raises(Exception):  # ModuleError for reference loading
            matchering.process(
                target=target_file,
                reference="nonexistent_reference.wav",
                results=[str(output_file)]
            )

    def test_process_empty_results_list(self, test_audio_files):
        """Test process() with empty results list"""
        matchering = pytest.importorskip("matchering")

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]

        with pytest.raises(RuntimeError, match="result list is empty"):
            matchering.process(
                target=target_file,
                reference=reference_file,
                results=[]
            )

    def test_process_invalid_output_format(self, test_audio_files, temp_dir):
        """Test process() with invalid output format"""
        matchering = pytest.importorskip("matchering")
        from matchering import Result

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]

        # Test invalid file extension
        with pytest.raises((TypeError, ValueError)):
            Result(str(temp_dir / "output.xyz"), subtype="PCM_16")

        # Test invalid subtype
        with pytest.raises((TypeError, ValueError)):
            Result(str(temp_dir / "output.wav"), subtype="INVALID_SUBTYPE")

    def test_process_mono_files(self, temp_dir):
        """Test process() with mono files (should fail)"""
        matchering = pytest.importorskip("matchering")
        sf = pytest.importorskip("soundfile")

        # Create mono test files
        duration = 2.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)

        mono_audio = np.sin(2 * np.pi * 440 * t) * 0.5  # Mono signal

        target_file = temp_dir / "mono_target.wav"
        reference_file = temp_dir / "mono_reference.wav"
        output_file = temp_dir / "output.wav"

        sf.write(target_file, mono_audio, sample_rate)
        sf.write(reference_file, mono_audio * 2, sample_rate)  # Different amplitude

        # Mono files actually work (get converted to stereo), so this should succeed
        # Let's test that mono files are processed correctly
        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(output_file)]
        )

        # Verify output was created
        assert output_file.exists(), "Output should be created for mono files"

        # Verify output is stereo
        sf = pytest.importorskip("soundfile")
        output_audio, output_sr = sf.read(output_file)
        assert output_audio.shape[1] == 2, "Output should be converted to stereo"

    def test_process_identical_files(self, test_audio_files, temp_dir):
        """Test process() with identical target and reference files"""
        matchering = pytest.importorskip("matchering")

        target_file = test_audio_files["quiet_target.wav"]
        output_file = temp_dir / "identical_output.wav"

        # Using same file as target and reference should fail by default
        with pytest.raises(Exception):  # Should raise equality check error
            matchering.process(
                target=target_file,
                reference=target_file,  # Same file
                results=[str(output_file)]
            )

    def test_process_identical_files_allowed(self, test_audio_files, temp_dir):
        """Test process() with identical files when equality is allowed"""
        matchering = pytest.importorskip("matchering")
        from matchering import Config

        target_file = test_audio_files["quiet_target.wav"]
        output_file = temp_dir / "identical_allowed.wav"

        config = Config(allow_equality=True)

        # Should work when allow_equality=True
        matchering.process(
            target=target_file,
            reference=target_file,
            results=[str(output_file)],
            config=config
        )

        assert output_file.exists(), "Should process identical files when allow_equality=True"


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.performance
@pytest.mark.slow
class TestCoreProcessingPerformance:
    """Test performance characteristics of core processing"""

    def test_process_performance_benchmark(self, test_audio_files, temp_dir):
        """Benchmark core processing performance"""
        matchering = pytest.importorskip("matchering")
        import time

        target_file = test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]
        output_file = temp_dir / "benchmark.wav"

        # Benchmark processing time
        start_time = time.perf_counter()

        matchering.process(
            target=target_file,
            reference=reference_file,
            results=[str(output_file)]
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time

        print(f"Processing time: {processing_time:.2f}s")

        # Performance should be reasonable (less than 30 seconds for test files)
        assert processing_time < 30.0, f"Processing took too long: {processing_time:.2f}s"

        # Verify output quality wasn't compromised
        sf = pytest.importorskip("soundfile")
        output_audio, output_sr = sf.read(output_file)
        assert len(output_audio) > 0, "Output should have content"
        assert not np.isnan(output_audio).any(), "Output should not contain NaN"
        assert not np.isinf(output_audio).any(), "Output should not contain Inf"

    def test_process_memory_usage(self, test_audio_files, temp_dir):
        """Test memory usage during processing"""
        matchering = pytest.importorskip("matchering")

        target_file = test_audio_files["long_audio.wav"] if "long_audio.wav" in test_audio_files else test_audio_files["quiet_target.wav"]
        reference_file = test_audio_files["loud_reference.wav"]
        output_file = temp_dir / "memory_test.wav"

        try:
            # Process and monitor for memory issues
            matchering.process(
                target=target_file,
                reference=reference_file,
                results=[str(output_file)]
            )

            # If we get here without MemoryError, processing completed successfully
            assert output_file.exists(), "Processing should complete successfully"

        except MemoryError:
            pytest.skip("Insufficient memory for memory usage test")