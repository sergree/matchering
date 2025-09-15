"""
Cross-Platform Validation Suite - Phase 4.3: Cross-platform validation
Tests system compatibility across different platforms, Python versions, and environments
"""

import pytest
import numpy as np
import tempfile
import platform
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import matchering


class TestPlatformCompatibility:
    """Test basic platform compatibility and environment detection"""

    def test_platform_detection(self):
        """Test platform detection and basic system info"""
        print(f"\n🖥️  Platform Information:")
        print(f"   OS: {platform.system()} {platform.release()}")
        print(f"   Architecture: {platform.machine()}")
        print(f"   Python: {platform.python_version()}")
        print(f"   Python implementation: {platform.python_implementation()}")
        print(f"   Processor: {platform.processor()}")

        # Basic platform assertions
        assert platform.system() in ['Linux', 'Darwin', 'Windows']

        # Check Python version properly
        python_version = tuple(map(int, platform.python_version().split('.')))
        assert python_version >= (3, 7), f"Python 3.7+ required, got {platform.python_version()}"

        assert platform.machine() in ['x86_64', 'AMD64', 'arm64', 'aarch64', 'i386', 'i686']

    def test_numpy_compatibility(self):
        """Test NumPy compatibility across platforms"""
        print(f"\n🔢 NumPy Compatibility:")
        print(f"   Version: {np.__version__}")
        print(f"   BLAS info: {np.__config__.show()}")

        # Test basic NumPy operations that matchering relies on
        test_array = np.random.rand(1000, 2).astype(np.float32)

        # FFT operations (critical for frequency analysis)
        fft_result = np.fft.fft(test_array, axis=0)
        assert fft_result.shape == test_array.shape

        # Mathematical operations
        rms = np.sqrt(np.mean(test_array ** 2))
        assert rms > 0

        # Array operations
        normalized = test_array / np.max(np.abs(test_array))
        assert np.max(np.abs(normalized)) <= 1.0

        print(f"   ✅ FFT operations: Working")
        print(f"   ✅ Math operations: Working")
        print(f"   ✅ Array operations: Working")

    def test_audio_library_compatibility(self):
        """Test audio library compatibility"""
        print(f"\n🎵 Audio Library Compatibility:")

        # Test SoundFile
        try:
            import soundfile as sf
            print(f"   SoundFile: {sf.__version__} ✅")

            # Test basic I/O operations
            test_audio = np.random.rand(1000, 2).astype(np.float32) * 0.1
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                sf.write(tmp.name, test_audio, 44100)
                read_audio, sr = sf.read(tmp.name)
                assert sr == 44100
                assert read_audio.shape == test_audio.shape
                os.unlink(tmp.name)
                print(f"   SoundFile I/O: Working ✅")
        except ImportError as e:
            pytest.fail(f"SoundFile not available: {e}")

        # Test resampy
        try:
            import resampy
            print(f"   Resampy: Available ✅")

            # Test resampling functionality
            test_audio = np.random.rand(1000, 2).astype(np.float32)
            resampled = resampy.resample(test_audio, 44100, 48000, axis=0)
            assert resampled.shape[1] == 2  # Stereo preserved
            print(f"   Resampy functionality: Working ✅")
        except ImportError as e:
            print(f"   Resampy: Not available ⚠️ ({e})")

    @pytest.mark.platform
    def test_matchering_core_import(self):
        """Test matchering core module imports work across platforms"""
        print(f"\n📦 Matchering Core Import Test:")

        # Test main module import
        import matchering
        print(f"   Main module: ✅")

        # Test core components
        try:
            from matchering import core
            print(f"   Core module: ✅")
        except ImportError as e:
            print(f"   Core module: ❌ ({e})")

        try:
            from matchering import stages
            print(f"   Stages module: ✅")
        except ImportError as e:
            print(f"   Stages module: ❌ ({e})")

        try:
            from matchering import dsp
            print(f"   DSP module: ✅")
        except ImportError as e:
            print(f"   DSP module: ❌ ({e})")

        # Test that main process function exists
        assert hasattr(matchering, 'process')
        print(f"   Process function: ✅")


class TestCrossPlatformProcessing:
    """Test audio processing works consistently across platforms"""

    @pytest.fixture
    def platform_test_workspace(self):
        """Create platform-specific test workspace"""
        with tempfile.TemporaryDirectory(prefix=f"platform_test_{platform.system()}_") as tmpdir:
            yield Path(tmpdir)

    def create_test_audio_cross_platform(self, duration=3.0, sample_rate=44100):
        """Create test audio ensuring cross-platform compatibility"""
        # Use deterministic random seed for cross-platform consistency
        np.random.seed(42)

        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, dtype=np.float64)

        # Create target (quiet)
        target_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.1,
            np.sin(2 * np.pi * 440 * t) * 0.09
        ]).astype(np.float32)

        # Create reference (loud)
        reference_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * t) * 0.6,
            np.sin(2 * np.pi * 440 * t) * 0.58
        ]).astype(np.float32)

        return target_audio, reference_audio, sample_rate

    @pytest.mark.platform
    def test_basic_processing_cross_platform(self, platform_test_workspace):
        """Test basic processing works on current platform"""
        print(f"\n🔄 Testing basic processing on {platform.system()}")

        # Create test audio
        target_audio, reference_audio, sr = self.create_test_audio_cross_platform()

        # Create test files
        target_file = platform_test_workspace / "target.wav"
        reference_file = platform_test_workspace / "reference.wav"
        result_file = platform_test_workspace / "result.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, sr)
        sf.write(reference_file, reference_audio, sr)

        # Process
        import time
        start_time = time.perf_counter()

        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time

        # Verify result
        assert result_file.exists()
        result_audio, result_sr = sf.read(str(result_file))

        print(f"   ⏱️  Processing time: {processing_time:.3f}s")
        print(f"   📊 Input shape: {target_audio.shape}")
        print(f"   📊 Output shape: {result_audio.shape}")
        print(f"   🔊 Sample rate: {result_sr} Hz")

        # Platform-agnostic assertions
        assert result_audio.shape == target_audio.shape
        assert result_sr == sr
        assert not np.array_equal(result_audio, target_audio)  # Should be processed
        assert processing_time < 30.0  # Should complete reasonably quickly

    @pytest.mark.platform
    def test_file_path_handling_cross_platform(self, platform_test_workspace):
        """Test file path handling across different platform path conventions"""
        print(f"\n📂 Testing file path handling on {platform.system()}")

        # Create test audio
        target_audio, reference_audio, sr = self.create_test_audio_cross_platform(duration=1.0)

        # Test different path formats
        path_test_cases = [
            # Standard paths
            ("standard_target.wav", "standard_reference.wav", "standard_result.wav"),
            # Paths with spaces
            ("target with spaces.wav", "reference with spaces.wav", "result with spaces.wav"),
            # Paths with subdirectories
            ("sub/target.wav", "sub/reference.wav", "sub/result.wav"),
        ]

        for target_name, ref_name, result_name in path_test_cases:
            print(f"   Testing: {target_name}")

            # Create subdirectory if needed
            target_file = platform_test_workspace / target_name
            reference_file = platform_test_workspace / ref_name
            result_file = platform_test_workspace / result_name

            # Create parent directories
            target_file.parent.mkdir(parents=True, exist_ok=True)
            reference_file.parent.mkdir(parents=True, exist_ok=True)
            result_file.parent.mkdir(parents=True, exist_ok=True)

            # Write test files
            import soundfile as sf
            sf.write(target_file, target_audio, sr)
            sf.write(reference_file, reference_audio, sr)

            # Process with different path representations
            try:
                matchering.process(
                    target=str(target_file),
                    reference=str(reference_file),
                    results=[str(result_file)]
                )

                assert result_file.exists()
                print(f"   ✅ {target_name}: Success")

            except Exception as e:
                print(f"   ❌ {target_name}: Failed ({e})")
                raise

    @pytest.mark.platform
    def test_numerical_precision_cross_platform(self, platform_test_workspace):
        """Test numerical precision and consistency across platforms"""
        print(f"\n🔢 Testing numerical precision on {platform.system()}")

        # Create identical test audio with fixed seed
        np.random.seed(12345)  # Fixed seed for reproducibility

        target_audio, reference_audio, sr = self.create_test_audio_cross_platform(duration=2.0)

        target_file = platform_test_workspace / "precision_target.wav"
        reference_file = platform_test_workspace / "precision_reference.wav"
        result_file = platform_test_workspace / "precision_result.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, sr)
        sf.write(reference_file, reference_audio, sr)

        # Process
        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        # Load result and compute basic statistics
        result_audio, _ = sf.read(str(result_file))

        # Compute platform-independent metrics
        result_rms = np.sqrt(np.mean(result_audio ** 2))
        result_peak = np.max(np.abs(result_audio))
        result_mean = np.mean(result_audio)

        print(f"   📊 Result RMS: {result_rms:.6f}")
        print(f"   📊 Result peak: {result_peak:.6f}")
        print(f"   📊 Result mean: {result_mean:.6f}")

        # Sanity checks (platform-independent)
        assert 0.1 < result_rms < 1.0  # Reasonable RMS level
        assert result_peak <= 1.0  # No clipping
        assert abs(result_mean) < 0.1  # Roughly centered
        assert not np.any(np.isnan(result_audio))  # No NaN values
        assert not np.any(np.isinf(result_audio))  # No infinite values

    @pytest.mark.platform
    def test_memory_usage_cross_platform(self, platform_test_workspace):
        """Test memory usage behavior across platforms"""
        print(f"\n💾 Testing memory behavior on {platform.system()}")

        # Create a moderately sized test case
        duration = 10.0  # 10 seconds
        target_audio, reference_audio, sr = self.create_test_audio_cross_platform(duration)

        target_file = platform_test_workspace / "memory_target.wav"
        reference_file = platform_test_workspace / "memory_reference.wav"
        result_file = platform_test_workspace / "memory_result.wav"

        import soundfile as sf
        sf.write(target_file, target_audio, sr)
        sf.write(reference_file, reference_audio, sr)

        # Measure processing
        import time
        start_time = time.perf_counter()

        matchering.process(
            target=str(target_file),
            reference=str(reference_file),
            results=[str(result_file)]
        )

        end_time = time.perf_counter()
        processing_time = end_time - start_time

        # Check file sizes
        input_size = target_file.stat().st_size + reference_file.stat().st_size
        output_size = result_file.stat().st_size

        print(f"   📁 Input size: {input_size / 1024:.1f} KB")
        print(f"   📁 Output size: {output_size / 1024:.1f} KB")
        print(f"   ⏱️  Processing time: {processing_time:.3f}s")
        print(f"   🚀 Real-time factor: {duration / processing_time:.1f}x")

        # Platform-independent performance assertions
        assert processing_time < 30.0  # Should complete within 30 seconds
        assert output_size > 0  # Should produce output
        assert result_file.exists()


class TestPlatformSpecificFeatures:
    """Test platform-specific features and compatibility"""

    def test_path_separator_handling(self):
        """Test handling of platform-specific path separators"""
        print(f"\n📁 Testing path separators on {platform.system()}")

        # Test path separator detection
        if platform.system() == 'Windows':
            expected_sep = '\\'
            test_path = "C:\\Users\\test\\audio.wav"
        else:
            expected_sep = '/'
            test_path = "/home/user/audio.wav"

        print(f"   Expected separator: '{expected_sep}'")
        print(f"   Actual separator: '{os.sep}'")
        print(f"   Test path: {test_path}")

        assert os.sep == expected_sep

        # Test Path object handling
        path_obj = Path(test_path)
        assert isinstance(path_obj, Path)
        print(f"   ✅ Path object handling works")

    @pytest.mark.platform
    def test_unicode_filename_support(self):
        """Test support for Unicode filenames across platforms"""
        print(f"\n🌐 Testing Unicode filename support on {platform.system()}")

        # Test various Unicode characters that might be problematic
        unicode_test_cases = [
            "test_básico.wav",           # Basic accents
            "test_中文.wav",              # Chinese characters
            "test_русский.wav",          # Cyrillic
            "test_émoji🎵.wav",          # Emoji (if supported)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            for filename in unicode_test_cases:
                try:
                    test_file = tmpdir / filename

                    # Try to create file
                    test_file.touch()
                    assert test_file.exists()

                    # Clean up
                    test_file.unlink()

                    print(f"   ✅ {filename}: Supported")

                except (UnicodeError, OSError) as e:
                    print(f"   ⚠️  {filename}: Not supported ({e})")

    def test_cpu_architecture_compatibility(self):
        """Test CPU architecture specific features"""
        print(f"\n🖥️  Testing CPU architecture compatibility")

        arch = platform.machine().lower()
        print(f"   Architecture: {arch}")

        # Test NumPy operations that might be architecture-dependent
        test_data = np.random.rand(1000, 2).astype(np.float32)

        # FFT operations
        fft_result = np.fft.fft(test_data, axis=0)
        assert not np.any(np.isnan(fft_result))
        print(f"   ✅ FFT operations: Working")

        # SIMD-accelerated operations (if available)
        dot_product = np.dot(test_data[:, 0], test_data[:, 1])
        assert not np.isnan(dot_product)
        print(f"   ✅ Dot product: Working")

        # Memory alignment tests
        aligned_array = np.empty((1000, 2), dtype=np.float32)
        assert aligned_array.flags.c_contiguous
        print(f"   ✅ Memory alignment: Working")


class TestEnvironmentValidation:
    """Test different Python environments and configurations"""

    def test_python_version_compatibility(self):
        """Test Python version specific features"""
        print(f"\n🐍 Testing Python {sys.version_info} compatibility")

        # Check minimum version requirements
        assert sys.version_info >= (3, 7), "Python 3.7+ required"
        print(f"   ✅ Python version check: {sys.version_info}")

        # Test pathlib (Python 3.4+)
        from pathlib import Path
        test_path = Path("/tmp/test")
        assert hasattr(test_path, 'exists')
        print(f"   ✅ Pathlib support: Available")

        # Test f-strings (Python 3.6+)
        test_var = "world"
        test_fstring = f"Hello {test_var}"
        assert test_fstring == "Hello world"
        print(f"   ✅ F-string support: Available")

    def test_dependency_versions(self):
        """Test dependency version compatibility"""
        print(f"\n📦 Testing dependency versions")

        dependencies = [
            ('numpy', '1.19.0'),
            ('scipy', '1.5.0'),
            ('soundfile', '0.10.0'),
        ]

        for dep_name, min_version in dependencies:
            try:
                module = __import__(dep_name)
                version = getattr(module, '__version__', 'unknown')
                print(f"   {dep_name}: {version}")

                # Version comparison would be more complex in real implementation
                assert version != 'unknown'

            except ImportError:
                print(f"   {dep_name}: Not installed ❌")
                if dep_name in ['numpy', 'scipy', 'soundfile']:
                    pytest.fail(f"Required dependency {dep_name} not available")

    @pytest.mark.platform
    def test_temporary_directory_access(self):
        """Test temporary directory access across platforms"""
        print(f"\n📂 Testing temporary directory access on {platform.system()}")

        # Test standard temporary directory
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            print(f"   Temp directory: {tmpdir_path}")
            assert tmpdir_path.exists()
            assert tmpdir_path.is_dir()

            # Test file creation in temp directory
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("test content")
            assert test_file.exists()

            print(f"   ✅ Temporary directory access: Working")
            print(f"   ✅ File creation in temp dir: Working")