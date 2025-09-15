"""
Performance Benchmarking Suite - Phase 4.2: Performance and scalability benchmarking
Tests processing performance across various audio durations, formats, and configurations
"""

import pytest
import numpy as np
import time
import tempfile
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import matchering


class TestProcessingPerformanceBenchmarks:
    """Test processing performance across various conditions"""

    @pytest.fixture
    def benchmark_workspace(self):
        """Create temporary workspace for benchmarking"""
        with tempfile.TemporaryDirectory(prefix="benchmark_") as tmpdir:
            yield Path(tmpdir)

    def create_test_audio(self, duration_seconds: float, sample_rate: int = 44100, complexity: str = "simple"):
        """Create test audio of specified duration and complexity"""
        samples = int(duration_seconds * sample_rate)
        t = np.linspace(0, duration_seconds, samples)

        if complexity == "simple":
            # Simple sine wave
            audio = np.column_stack([
                np.sin(2 * np.pi * 440 * t) * 0.1,
                np.sin(2 * np.pi * 440 * t) * 0.09
            ]).astype(np.float32)
        elif complexity == "complex":
            # Complex harmonic content
            audio = np.column_stack([
                (np.sin(2 * np.pi * 220 * t) * 0.3 +
                 np.sin(2 * np.pi * 440 * t) * 0.25 +
                 np.sin(2 * np.pi * 880 * t) * 0.2 +
                 np.sin(2 * np.pi * 1760 * t) * 0.15 +
                 np.random.normal(0, 0.05, samples)),
                (np.sin(2 * np.pi * 220 * t) * 0.28 +
                 np.sin(2 * np.pi * 440 * t) * 0.24 +
                 np.sin(2 * np.pi * 880 * t) * 0.19 +
                 np.sin(2 * np.pi * 1760 * t) * 0.14 +
                 np.random.normal(0, 0.05, samples))
            ]).astype(np.float32)
        else:  # realistic
            # Realistic music-like content with dynamics
            harmonics = [220, 440, 660, 880, 1100, 1320, 1540, 1760]
            left = np.zeros(samples)
            right = np.zeros(samples)

            for i, freq in enumerate(harmonics):
                amplitude = 0.3 / (i + 1)  # Decreasing harmonics
                left += np.sin(2 * np.pi * freq * t) * amplitude
                right += np.sin(2 * np.pi * freq * t * 1.002) * amplitude  # Slight detuning

            # Add envelope and dynamics
            envelope = np.exp(-t / (duration_seconds * 0.3)) * (1 + 0.5 * np.sin(2 * np.pi * t / 3))
            left *= envelope
            right *= envelope

            # Add some noise for realism
            left += np.random.normal(0, 0.02, samples)
            right += np.random.normal(0, 0.02, samples)

            audio = np.column_stack([left, right]).astype(np.float32)

        return audio

    @pytest.mark.performance
    @pytest.mark.parametrize("duration", [1.0, 3.0, 10.0, 30.0, 60.0])
    def test_duration_scaling_performance(self, benchmark_workspace, duration):
        """Test how processing time scales with audio duration"""
        print(f"\n🎵 Testing {duration}s audio processing performance")

        # Create test files
        target_audio = self.create_test_audio(duration, complexity="simple")
        reference_audio = self.create_test_audio(duration, complexity="complex")

        target_file = benchmark_workspace / f"target_{duration}s.wav"
        reference_file = benchmark_workspace / f"reference_{duration}s.wav"
        result_file = benchmark_workspace / f"result_{duration}s.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, 44100)
        sf.write(reference_file, reference_audio, 44100)

        # Benchmark processing
        start_time = time.perf_counter()

        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time
        real_time_factor = duration / processing_time

        print(f"   ⏱️  Processing time: {processing_time:.3f}s")
        print(f"   🚀 Real-time factor: {real_time_factor:.1f}x")
        print(f"   💾 File size: {result_file.stat().st_size / 1024:.1f} KB")

        # Performance assertions
        assert processing_time < duration * 2  # Should be faster than 0.5x real-time
        assert real_time_factor > 1.0  # Should be faster than real-time
        assert result_file.exists()
        assert result_file.stat().st_size > 1000

        # Log performance data for analysis
        performance_data = {
            'duration': duration,
            'processing_time': processing_time,
            'real_time_factor': real_time_factor,
            'file_size': result_file.stat().st_size
        }
        print(f"   📊 Performance data: {performance_data}")

    @pytest.mark.performance
    @pytest.mark.parametrize("sample_rate", [22050, 44100, 48000, 96000])
    def test_sample_rate_performance(self, benchmark_workspace, sample_rate):
        """Test performance across different sample rates"""
        print(f"\n🔊 Testing {sample_rate} Hz sample rate performance")

        duration = 5.0  # Fixed duration for comparison

        # Create test files at specified sample rate
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)

        target_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.1,
            np.sin(2 * np.pi * 440 * t) * 0.09
        ]).astype(np.float32)

        reference_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.3,
            np.sin(2 * np.pi * 440 * t) * 0.28
        ]).astype(np.float32)

        target_file = benchmark_workspace / f"target_{sample_rate}Hz.wav"
        reference_file = benchmark_workspace / f"reference_{sample_rate}Hz.wav"
        result_file = benchmark_workspace / f"result_{sample_rate}Hz.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, sample_rate)
        sf.write(reference_file, reference_audio, sample_rate)

        # Benchmark processing
        start_time = time.perf_counter()

        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time
        real_time_factor = duration / processing_time

        print(f"   ⏱️  Processing time: {processing_time:.3f}s")
        print(f"   🚀 Real-time factor: {real_time_factor:.1f}x")
        print(f"   🔢 Samples processed: {samples:,}")

        # Performance assertions
        assert processing_time < 30.0  # Should complete within 30 seconds
        assert real_time_factor > 0.1  # Should be reasonable even for high sample rates
        assert result_file.exists()

    @pytest.mark.performance
    def test_multiple_format_generation_performance(self, benchmark_workspace):
        """Test performance when generating multiple output formats"""
        print(f"\n📁 Testing multiple format generation performance")

        duration = 10.0
        target_audio = self.create_test_audio(duration, complexity="realistic")
        reference_audio = self.create_test_audio(duration, complexity="complex")

        target_file = benchmark_workspace / "target_multi.wav"
        reference_file = benchmark_workspace / "reference_multi.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, 44100)
        sf.write(reference_file, reference_audio, 44100)

        # Generate multiple formats
        result_files = [
            str(benchmark_workspace / "result_16bit.wav"),
            str(benchmark_workspace / "result_24bit.wav"),
            str(benchmark_workspace / "result_preview.wav")
        ]

        # Benchmark multi-format processing
        start_time = time.perf_counter()

        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=result_files
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time
        real_time_factor = duration / processing_time

        print(f"   ⏱️  Processing time: {processing_time:.3f}s")
        print(f"   🚀 Real-time factor: {real_time_factor:.1f}x")
        print(f"   📄 Formats generated: {len(result_files)}")

        # Verify all files were created
        for result_file in result_files:
            result_path = Path(result_file)
            assert result_path.exists()
            print(f"   ✅ {result_path.name}: {result_path.stat().st_size / 1024:.1f} KB")

        # Performance should still be reasonable
        assert processing_time < 60.0
        assert real_time_factor > 0.2

    @pytest.mark.performance
    def test_concurrent_processing_simulation(self, benchmark_workspace):
        """Test system stability under simulated concurrent processing loads"""
        print(f"\n🔄 Testing system stability under load")

        # Create multiple small jobs to simulate concurrent processing
        num_jobs = 5
        duration_per_job = 2.0

        jobs = []
        for i in range(num_jobs):
            target_audio = self.create_test_audio(duration_per_job, complexity="simple")
            reference_audio = self.create_test_audio(duration_per_job, complexity="complex")

            target_file = benchmark_workspace / f"target_job_{i}.wav"
            reference_file = benchmark_workspace / f"reference_job_{i}.wav"
            result_file = benchmark_workspace / f"result_job_{i}.wav"

            import soundfile as sf
            sf.write(target_file, target_audio, 44100)
            sf.write(reference_file, reference_audio, 44100)

            jobs.append({
                'target': str(target_file),
                'reference': str(reference_file),
                'result': str(result_file),
                'id': i
            })

        # Process jobs sequentially (simulating queue processing)
        total_start_time = time.perf_counter()
        job_times = []

        for job in jobs:
            job_start = time.perf_counter()

            matchering.process(
                target=job['target'],
                reference=job['reference'],
                results=[job['result']]
            )

            job_end = time.perf_counter()
            job_time = job_end - job_start
            job_times.append(job_time)

            print(f"   📋 Job {job['id']}: {job_time:.3f}s")

        total_end_time = time.perf_counter()
        total_time = total_end_time - total_start_time

        # Calculate statistics
        avg_job_time = np.mean(job_times)
        std_job_time = np.std(job_times)
        total_audio_duration = num_jobs * duration_per_job
        overall_real_time_factor = total_audio_duration / total_time

        print(f"   ⏱️  Total processing time: {total_time:.3f}s")
        print(f"   📊 Average job time: {avg_job_time:.3f}s ±{std_job_time:.3f}s")
        print(f"   🎵 Total audio processed: {total_audio_duration:.1f}s")
        print(f"   🚀 Overall real-time factor: {overall_real_time_factor:.1f}x")

        # Stability assertions
        assert all(Path(job['result']).exists() for job in jobs)
        assert std_job_time < avg_job_time * 0.5  # Consistent performance
        assert overall_real_time_factor > 1.0  # Still faster than real-time overall


class TestScalabilityBenchmarks:
    """Test system scalability and resource usage"""

    @pytest.mark.performance
    def test_large_file_processing(self, tmp_path):
        """Test processing performance with large audio files"""
        print(f"\n🗂️  Testing large file processing")

        # Create a larger file (2 minutes)
        duration = 120.0  # 2 minutes
        sample_rate = 44100
        samples = int(duration * sample_rate)

        print(f"   📏 Creating {duration/60:.1f} minute audio files...")

        # Create realistic but efficient test audio
        t = np.linspace(0, duration, samples)

        # Target: Quiet, simple content
        target_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.1 * np.exp(-t/60),  # Decaying
            np.sin(2 * np.pi * 440 * t) * 0.09 * np.exp(-t/60)
        ]).astype(np.float32)

        # Reference: Louder, more complex
        reference_audio = np.column_stack([
            (np.sin(2 * np.pi * 220 * t) * 0.3 +
             np.sin(2 * np.pi * 440 * t) * 0.25),
            (np.sin(2 * np.pi * 220 * t) * 0.28 +
             np.sin(2 * np.pi * 440 * t) * 0.24)
        ]).astype(np.float32)

        target_file = tmp_path / "large_target.wav"
        reference_file = tmp_path / "large_reference.wav"
        result_file = tmp_path / "large_result.wav"

        import soundfile as sf

        print(f"   💾 Writing test files...")
        sf.write(target_file, target_audio, sample_rate)
        sf.write(reference_file, reference_audio, sample_rate)

        file_size_mb = target_file.stat().st_size / 1024 / 1024
        print(f"   📊 Input file size: {file_size_mb:.1f} MB")

        # Benchmark large file processing
        print(f"   🏃 Processing large files...")
        start_time = time.perf_counter()

        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time
        real_time_factor = duration / processing_time

        result_size_mb = result_file.stat().st_size / 1024 / 1024

        print(f"   ⏱️  Processing time: {processing_time:.1f}s")
        print(f"   🚀 Real-time factor: {real_time_factor:.1f}x")
        print(f"   📈 Processing rate: {file_size_mb/processing_time:.1f} MB/s")
        print(f"   📊 Result file size: {result_size_mb:.1f} MB")

        # Large file performance assertions
        assert processing_time < 300  # Should complete within 5 minutes
        assert real_time_factor > 0.5  # Should be at least 0.5x real-time
        assert result_file.exists()
        assert result_size_mb > 0.1  # Should produce meaningful output

    @pytest.mark.performance
    def test_processing_consistency(self, tmp_path):
        """Test processing consistency across multiple identical runs"""
        print(f"\n🔄 Testing processing consistency")

        # Create test files
        duration = 5.0
        target_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(duration * 44100))) * 0.1,
            np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(duration * 44100))) * 0.09
        ]).astype(np.float32)

        reference_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(duration * 44100))) * 0.3,
            np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(duration * 44100))) * 0.28
        ]).astype(np.float32)

        target_file = tmp_path / "consistency_target.wav"
        reference_file = tmp_path / "consistency_reference.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, 44100)
        sf.write(reference_file, reference_audio, 44100)

        # Run multiple processing iterations
        num_runs = 5
        processing_times = []

        for run in range(num_runs):
            result_file = tmp_path / f"consistency_result_{run}.wav"

            start_time = time.perf_counter()

            matchering.process(
                target=str(target_file),
                reference=str(reference_file),
                results=[str(result_file)]
            )

            end_time = time.perf_counter()
            processing_time = end_time - start_time
            processing_times.append(processing_time)

            print(f"   🏃 Run {run + 1}: {processing_time:.3f}s")

        # Calculate consistency metrics
        avg_time = np.mean(processing_times)
        std_time = np.std(processing_times)
        coefficient_of_variation = std_time / avg_time
        min_time = np.min(processing_times)
        max_time = np.max(processing_times)

        print(f"   📊 Average time: {avg_time:.3f}s ±{std_time:.3f}s")
        print(f"   📈 Range: {min_time:.3f}s - {max_time:.3f}s")
        print(f"   🎯 Coefficient of variation: {coefficient_of_variation:.3f}")

        # Consistency assertions (relaxed for small files where overhead dominates)
        assert coefficient_of_variation < 0.3  # Less than 30% variation is acceptable
        assert max_time - min_time < avg_time * 1.0  # Range should be reasonable
        assert all(processing_time < 30.0 for processing_time in processing_times)