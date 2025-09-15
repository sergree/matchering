#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance and Scalability Benchmarks for Matchering Core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comprehensive performance testing to validate production readiness

:copyright: (C) 2024 Matchering Team
:license: GPLv3, see LICENSE for more details.
"""

import pytest
import time
import psutil
import numpy as np
import threading
from pathlib import Path
from unittest.mock import patch
import tempfile
import soundfile as sf
import matchering
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc


@pytest.fixture
def performance_audio_files():
    """Generate audio files of various sizes for performance testing"""
    files = {}
    sample_rate = 44100

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Small file (10 seconds)
        duration = 10.0
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        audio_10s = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.3,
            np.sin(2 * np.pi * 440 * t) * 0.28
        ]).astype(np.float32)

        files['small_target'] = tmpdir / "small_target.wav"
        files['small_reference'] = tmpdir / "small_reference.wav"
        sf.write(files['small_target'], audio_10s, sample_rate)
        sf.write(files['small_reference'], audio_10s * 1.5, sample_rate)

        # Medium file (60 seconds)
        duration = 60.0
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        audio_60s = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.3,
            np.sin(2 * np.pi * 440 * t) * 0.28
        ]).astype(np.float32)

        files['medium_target'] = tmpdir / "medium_target.wav"
        files['medium_reference'] = tmpdir / "medium_reference.wav"
        sf.write(files['medium_target'], audio_60s, sample_rate)
        sf.write(files['medium_reference'], audio_60s * 1.5, sample_rate)

        # Large file (300 seconds / 5 minutes)
        duration = 300.0
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        audio_300s = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.3,
            np.sin(2 * np.pi * 440 * t) * 0.28
        ]).astype(np.float32)

        files['large_target'] = tmpdir / "large_target.wav"
        files['large_reference'] = tmpdir / "large_reference.wav"
        sf.write(files['large_target'], audio_300s, sample_rate)
        sf.write(files['large_reference'], audio_300s * 1.5, sample_rate)

        yield files


class TestPerformanceBenchmarks:
    """Core performance benchmarking tests"""

    def test_processing_time_scalability(self, performance_audio_files):
        """Test how processing time scales with audio duration"""
        results = {}

        for size in ['small', 'medium', 'large']:
            target = performance_audio_files[f'{size}_target']
            reference = performance_audio_files[f'{size}_reference']

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                result_file = tmp.name

            # Measure processing time
            start_time = time.perf_counter()
            matchering.process(
                target=str(target),
                reference=str(reference),
                results=[result_file]
            )
            end_time = time.perf_counter()

            processing_time = end_time - start_time

            # Get audio duration
            with sf.SoundFile(str(target)) as f:
                duration = len(f) / f.samplerate

            real_time_factor = duration / processing_time
            results[size] = {
                'duration': duration,
                'processing_time': processing_time,
                'real_time_factor': real_time_factor
            }

            print(f"{size.capitalize()} file ({duration}s): {processing_time:.2f}s processing, {real_time_factor:.1f}x real-time")

            # Clean up
            Path(result_file).unlink(missing_ok=True)

        # Validate performance scaling
        assert results['small']['real_time_factor'] > 5.0, "Small files should process at least 5x real-time"
        assert results['medium']['real_time_factor'] > 3.0, "Medium files should process at least 3x real-time"
        assert results['large']['real_time_factor'] > 1.0, "Large files should process faster than real-time"

        # Processing time should scale roughly linearly with duration
        time_efficiency_ratio = (results['large']['processing_time'] / results['small']['processing_time']) / (results['large']['duration'] / results['small']['duration'])
        assert time_efficiency_ratio < 2.0, f"Processing time scaling should be reasonable (got {time_efficiency_ratio:.2f})"

    def test_memory_usage_scaling(self, performance_audio_files):
        """Test memory usage with different file sizes"""
        memory_results = {}

        for size in ['small', 'medium', 'large']:
            target = performance_audio_files[f'{size}_target']
            reference = performance_audio_files[f'{size}_reference']

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                result_file = tmp.name

            # Force garbage collection before measurement
            gc.collect()

            # Measure memory before processing
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # Process audio
            matchering.process(
                target=str(target),
                reference=str(reference),
                results=[result_file]
            )

            # Measure memory after processing
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before

            # Get file size for comparison
            file_size_mb = Path(target).stat().st_size / 1024 / 1024

            memory_results[size] = {
                'file_size_mb': file_size_mb,
                'memory_used_mb': memory_used,
                'memory_efficiency': memory_used / file_size_mb if file_size_mb > 0 else 0
            }

            print(f"{size.capitalize()} file ({file_size_mb:.1f}MB): {memory_used:.1f}MB used ({memory_used/file_size_mb:.1f}x file size)")

            # Clean up
            Path(result_file).unlink(missing_ok=True)
            gc.collect()

        # Memory usage should be reasonable considering fixed overhead
        # Small files have higher overhead ratio, larger files should be more efficient
        assert memory_results['small']['memory_efficiency'] < 30.0, f"Small file memory usage too high: {memory_results['small']['memory_efficiency']:.1f}x file size"
        assert memory_results['medium']['memory_efficiency'] < 20.0, f"Medium file memory usage too high: {memory_results['medium']['memory_efficiency']:.1f}x file size"
        assert memory_results['large']['memory_efficiency'] < 10.0, f"Large file memory usage too high: {memory_results['large']['memory_efficiency']:.1f}x file size"

        # Validate memory efficiency improves with larger files
        assert memory_results['large']['memory_efficiency'] < memory_results['medium']['memory_efficiency'], "Larger files should be more memory efficient"

    def test_concurrent_processing_performance(self, performance_audio_files):
        """Test performance with concurrent processing tasks"""

        def process_file(target_path, reference_path):
            """Process a single file and return timing"""
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                result_file = tmp.name

            start_time = time.perf_counter()
            matchering.process(
                target=str(target_path),
                reference=str(reference_path),
                results=[result_file]
            )
            end_time = time.perf_counter()

            processing_time = end_time - start_time
            Path(result_file).unlink(missing_ok=True)
            return processing_time

        # Test serial processing
        serial_times = []
        for i in range(3):
            processing_time = process_file(
                performance_audio_files['small_target'],
                performance_audio_files['small_reference']
            )
            serial_times.append(processing_time)

        serial_total = sum(serial_times)

        # Test concurrent processing
        concurrent_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for i in range(3):
                future = executor.submit(
                    process_file,
                    performance_audio_files['small_target'],
                    performance_audio_files['small_reference']
                )
                futures.append(future)

            concurrent_times = []
            for future in as_completed(futures):
                concurrent_times.append(future.result())

        concurrent_total = time.perf_counter() - concurrent_start

        print(f"Serial processing: {serial_total:.2f}s")
        print(f"Concurrent processing: {concurrent_total:.2f}s")
        print(f"Speedup: {serial_total/concurrent_total:.2f}x")

        # Concurrent processing should provide some speedup (even modest improvement is good)
        assert concurrent_total < serial_total * 0.95, "Concurrent processing should be faster than serial"

    def test_cpu_utilization_efficiency(self, performance_audio_files):
        """Test CPU utilization during processing"""
        target = performance_audio_files['medium_target']
        reference = performance_audio_files['medium_reference']

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            result_file = tmp.name

        # Monitor CPU usage during processing
        cpu_samples = []
        monitoring = True

        def monitor_cpu():
            while monitoring:
                cpu_samples.append(psutil.cpu_percent(interval=0.1))

        # Start CPU monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()

        # Process audio
        start_time = time.perf_counter()
        matchering.process(
            target=str(target),
            reference=str(reference),
            results=[result_file]
        )
        end_time = time.perf_counter()

        # Stop monitoring
        monitoring = False
        monitor_thread.join()

        processing_time = end_time - start_time
        avg_cpu = np.mean(cpu_samples) if cpu_samples else 0
        max_cpu = np.max(cpu_samples) if cpu_samples else 0

        print(f"Processing time: {processing_time:.2f}s")
        print(f"Average CPU usage: {avg_cpu:.1f}%")
        print(f"Peak CPU usage: {max_cpu:.1f}%")

        # CPU should be utilized effectively
        assert avg_cpu > 20.0, f"CPU utilization too low: {avg_cpu:.1f}%"
        assert max_cpu < 100.0, f"CPU utilization sustainable: {max_cpu:.1f}%"

        # Clean up
        Path(result_file).unlink(missing_ok=True)


class TestScalabilityLimits:
    """Test system limits and edge cases"""

    def test_maximum_supported_duration(self, performance_audio_files):
        """Test processing very long audio files"""
        # Use the largest file we have
        target = performance_audio_files['large_target']
        reference = performance_audio_files['large_reference']

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            result_file = tmp.name

        # This should succeed without memory issues
        start_time = time.perf_counter()
        matchering.process(
            target=str(target),
            reference=str(reference),
            results=[result_file]
        )
        end_time = time.perf_counter()

        processing_time = end_time - start_time

        # Get duration
        with sf.SoundFile(str(target)) as f:
            duration = len(f) / f.samplerate

        real_time_factor = duration / processing_time

        print(f"Long file processing: {duration}s audio in {processing_time:.2f}s ({real_time_factor:.1f}x real-time)")

        # Should still process faster than real-time
        assert real_time_factor > 0.5, "Even long files should process reasonably fast"

        # Result should exist and be valid
        assert Path(result_file).exists()
        with sf.SoundFile(result_file) as f:
            assert len(f) > 0, "Result file should have content"

        # Clean up
        Path(result_file).unlink(missing_ok=True)

    def test_resource_cleanup_after_processing(self, performance_audio_files):
        """Test that resources are properly cleaned up after processing"""
        target = performance_audio_files['medium_target']
        reference = performance_audio_files['medium_reference']

        # Get initial resource usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_open_files = len(process.open_files())

        # Process multiple files
        for i in range(5):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                result_file = tmp.name

            matchering.process(
                target=str(target),
                reference=str(reference),
                results=[result_file]
            )

            Path(result_file).unlink(missing_ok=True)

        # Force garbage collection
        gc.collect()

        # Check final resource usage
        final_memory = process.memory_info().rss
        final_open_files = len(process.open_files())

        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        file_handle_increase = final_open_files - initial_open_files

        print(f"Memory increase after 5 processes: {memory_increase:.1f}MB")
        print(f"File handle increase: {file_handle_increase}")

        # Memory shouldn't grow significantly
        assert memory_increase < 100.0, f"Memory leak detected: {memory_increase:.1f}MB increase"
        assert file_handle_increase <= 2, f"File handle leak detected: {file_handle_increase} handles"


class TestRealTimePlayerPerformance:
    """Performance tests for real-time player components"""

    def test_real_time_processing_latency(self, performance_audio_files):
        """Test real-time processing latency for player"""
        from auralis import AudioPlayer, PlayerConfig

        # Create player with small buffer for low latency
        config = PlayerConfig(
            sample_rate=44100,
            buffer_size=1024,  # ~23ms at 44.1kHz
            enable_level_matching=True
        )
        player = AudioPlayer(config)

        # Load audio files
        target_loaded = player.load_file(str(performance_audio_files['small_target']))
        reference_loaded = player.load_reference(str(performance_audio_files['small_reference']))

        assert target_loaded, "Target file should load successfully"
        assert reference_loaded, "Reference file should load successfully"

        # Start playback
        player.play()

        # Measure chunk processing time
        chunk_times = []
        for i in range(100):  # Process 100 chunks
            start_time = time.perf_counter()
            chunk = player.get_audio_chunk()
            end_time = time.perf_counter()

            chunk_time = end_time - start_time
            chunk_times.append(chunk_time)

            if not player.is_playing:
                break

        avg_chunk_time = np.mean(chunk_times)
        max_chunk_time = np.max(chunk_times)
        buffer_duration = config.buffer_size / config.sample_rate

        print(f"Average chunk processing time: {avg_chunk_time*1000:.2f}ms")
        print(f"Maximum chunk processing time: {max_chunk_time*1000:.2f}ms")
        print(f"Buffer duration: {buffer_duration*1000:.2f}ms")
        print(f"Real-time safety margin: {(buffer_duration/max_chunk_time):.1f}x")

        # Processing should be much faster than buffer duration for real-time safety
        assert avg_chunk_time < buffer_duration * 0.1, "Average processing should be <10% of buffer duration"
        assert max_chunk_time < buffer_duration * 0.5, "Peak processing should be <50% of buffer duration"

    def test_player_memory_efficiency(self, performance_audio_files):
        """Test memory efficiency of player during long playback"""
        from auralis import AudioPlayer, PlayerConfig

        config = PlayerConfig(
            sample_rate=44100,
            buffer_size=4410,  # Larger buffer
            enable_level_matching=True
        )
        player = AudioPlayer(config)

        # Load large file
        player.load_file(str(performance_audio_files['large_target']))
        player.load_reference(str(performance_audio_files['large_reference']))

        # Start playback
        player.play()

        # Monitor memory during simulated playback
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate 30 seconds of playback
        chunks_per_second = config.sample_rate // config.buffer_size
        total_chunks = chunks_per_second * 30

        for i in range(total_chunks):
            chunk = player.get_audio_chunk()

            # Check memory every 5 seconds
            if i % (chunks_per_second * 5) == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"Memory at {i//chunks_per_second}s: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")

                # Memory shouldn't grow significantly during playback
                assert memory_increase < 50.0, f"Excessive memory growth: {memory_increase:.1f}MB"

            if not player.is_playing:
                break

        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory

        print(f"Total memory increase during playback: {total_memory_increase:.1f}MB")
        assert total_memory_increase < 100.0, "Player memory usage should remain stable"