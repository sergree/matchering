"""
Unit tests for preview creator and utilities
Tests preview generation functionality and utility functions
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.files
class TestPreviewCreator:
    """Test preview creation functionality"""

    def test_create_preview_import(self):
        """Test preview creator can be imported"""
        from matchering.preview_creator import create_preview
        assert callable(create_preview)

    def test_create_preview_basic_functionality(self, temp_dir):
        """Test basic preview creation"""
        from matchering.preview_creator import create_preview
        import matchering
        import soundfile as sf

        # Create synthetic target and result audio
        duration = 10.0  # 10 seconds
        sample_rate = 44100
        samples = int(duration * sample_rate)

        # Target: quieter audio
        target = np.random.random((samples, 2)).astype(np.float32) * 0.3

        # Result: processed audio (louder)
        result = np.random.random((samples, 2)).astype(np.float32) * 0.7

        # Create config with shorter preview settings for testing
        config = matchering.Config(
            internal_sample_rate=sample_rate,
            preview_size=int(sample_rate * 2),  # 2 seconds
            preview_analysis_step=int(sample_rate * 1),  # 1 second step
            preview_fade_size=int(sample_rate * 0.1),  # 0.1 second fade
        )

        # Create result objects for preview files
        preview_target = matchering.Result(str(temp_dir / "preview_target.wav"))
        preview_result = matchering.Result(str(temp_dir / "preview_result.wav"))

        # Create preview
        create_preview(target, result, config, preview_target, preview_result)

        # Verify preview files were created
        assert Path(preview_target.file).exists()
        assert Path(preview_result.file).exists()

        # Verify preview file properties
        target_audio, target_sr = sf.read(preview_target.file)
        result_audio, result_sr = sf.read(preview_result.file)

        assert target_sr == sample_rate
        assert result_sr == sample_rate
        assert target_audio.shape[1] == 2  # Stereo
        assert result_audio.shape[1] == 2  # Stereo
        assert len(target_audio) > 0
        assert len(result_audio) > 0

    def test_create_preview_target_only(self, temp_dir):
        """Test creating preview with only target output"""
        from matchering.preview_creator import create_preview
        import matchering

        # Create test audio
        samples = 44100 * 5  # 5 seconds
        target = np.random.random((samples, 2)).astype(np.float32) * 0.4
        result = np.random.random((samples, 2)).astype(np.float32) * 0.8

        config = matchering.Config()
        preview_target = matchering.Result(str(temp_dir / "preview_target_only.wav"))

        # Create preview with only target
        create_preview(target, result, config, preview_target, None)

        # Only target preview should exist
        assert Path(preview_target.file).exists()

    def test_create_preview_result_only(self, temp_dir):
        """Test creating preview with only result output"""
        from matchering.preview_creator import create_preview
        import matchering

        # Create test audio
        samples = 44100 * 5  # 5 seconds
        target = np.random.random((samples, 2)).astype(np.float32) * 0.4
        result = np.random.random((samples, 2)).astype(np.float32) * 0.8

        config = matchering.Config()
        preview_result = matchering.Result(str(temp_dir / "preview_result_only.wav"))

        # Create preview with only result
        create_preview(target, result, config, None, preview_result)

        # Only result preview should exist
        assert Path(preview_result.file).exists()

    def test_create_preview_no_outputs(self, temp_dir):
        """Test creating preview with no outputs specified"""
        from matchering.preview_creator import create_preview
        import matchering

        # Create test audio
        samples = 44100 * 3  # 3 seconds
        target = np.random.random((samples, 2)).astype(np.float32) * 0.4
        result = np.random.random((samples, 2)).astype(np.float32) * 0.8

        config = matchering.Config()

        # Should run without error even with no outputs
        create_preview(target, result, config, None, None)

    def test_create_preview_loudest_piece_selection(self, temp_dir):
        """Test that preview selects the loudest piece"""
        from matchering.preview_creator import create_preview
        import matchering
        import soundfile as sf

        # Create audio with a specific loud section
        sample_rate = 44100
        quiet_duration = 2.0
        loud_duration = 1.0

        quiet_samples = int(quiet_duration * sample_rate)
        loud_samples = int(loud_duration * sample_rate)

        # Create target with quiet-loud-quiet pattern
        quiet_section = np.random.random((quiet_samples, 2)).astype(np.float32) * 0.1
        loud_section = np.random.random((loud_samples, 2)).astype(np.float32) * 0.3

        target = np.vstack([quiet_section, loud_section, quiet_section])

        # Create result with similar pattern but louder
        quiet_result = np.random.random((quiet_samples, 2)).astype(np.float32) * 0.4
        loud_result = np.random.random((loud_samples, 2)).astype(np.float32) * 0.9

        result = np.vstack([quiet_result, loud_result, quiet_result])

        config = matchering.Config(
            internal_sample_rate=sample_rate,
            preview_size=int(sample_rate * 0.5),  # 0.5 second preview
            preview_analysis_step=int(sample_rate * 0.25),  # 0.25 second step
        )

        preview_result = matchering.Result(str(temp_dir / "loudest_preview.wav"))

        # Create preview
        create_preview(target, result, config, None, preview_result)

        # Load the preview
        preview_audio, _ = sf.read(preview_result.file)

        # Preview should have reasonable amplitude (from the loud section)
        preview_rms = np.sqrt(np.mean(preview_audio**2))
        assert preview_rms > 0.1  # Should be from a relatively loud section

    def test_create_preview_different_lengths(self, temp_dir):
        """Test preview creation with different audio lengths"""
        from matchering.preview_creator import create_preview
        import matchering

        sample_rate = 44100

        # Test different lengths
        lengths = [
            int(sample_rate * 1),    # 1 second
            int(sample_rate * 5),    # 5 seconds
            int(sample_rate * 30),   # 30 seconds
        ]

        for length in lengths:
            target = np.random.random((length, 2)).astype(np.float32) * 0.3
            result = np.random.random((length, 2)).astype(np.float32) * 0.7

            config = matchering.Config(internal_sample_rate=sample_rate)
            preview_result = matchering.Result(str(temp_dir / f"preview_{length}.wav"))

            # Should handle different lengths
            create_preview(target, result, config, None, preview_result)

            assert Path(preview_result.file).exists()

    def test_create_preview_fade_application(self, temp_dir):
        """Test that fade functionality works without errors"""
        from matchering.preview_creator import create_preview
        import matchering
        import soundfile as sf

        # Create longer audio to ensure fade gets applied
        sample_rate = 44100
        samples = int(sample_rate * 10)  # 10 seconds

        target = np.random.random((samples, 2)).astype(np.float32) * 0.3
        result = np.random.random((samples, 2)).astype(np.float32) * 0.7

        config = matchering.Config(
            internal_sample_rate=sample_rate,
            preview_size=int(sample_rate * 3),  # 3 second preview
            preview_fade_size=int(sample_rate * 0.2),  # 0.2 second fade
            preview_fade_coefficient=4
        )

        preview_result = matchering.Result(str(temp_dir / "fade_preview.wav"))

        # Create preview - should work without errors
        create_preview(target, result, config, None, preview_result)

        # Verify preview was created successfully
        assert Path(preview_result.file).exists()

        # Load and verify basic properties
        preview_audio, _ = sf.read(preview_result.file)
        assert len(preview_audio) > 0
        assert preview_audio.shape[1] == 2

        # Verify audio isn't silent (fade worked but didn't eliminate everything)
        assert np.max(np.abs(preview_audio)) > 0.01

    def test_create_preview_different_formats(self, temp_dir):
        """Test preview creation with different output formats"""
        from matchering.preview_creator import create_preview
        import matchering

        # Create test audio
        samples = 44100 * 3
        target = np.random.random((samples, 2)).astype(np.float32) * 0.3
        result = np.random.random((samples, 2)).astype(np.float32) * 0.7

        config = matchering.Config()

        # Test different output formats
        formats = ["PCM_16", "PCM_24", "FLOAT"]

        for fmt in formats:
            preview_result = matchering.Result(
                str(temp_dir / f"preview_{fmt}.wav"),
                subtype=fmt
            )

            create_preview(target, result, config, None, preview_result)

            assert Path(preview_result.file).exists()


@pytest.mark.unit
@pytest.mark.core
class TestUtilityFunctions:
    """Test utility functions"""

    def test_get_temp_folder_with_strings(self, temp_dir):
        """Test get_temp_folder with string paths"""
        from matchering.utils import get_temp_folder

        # Test with string paths
        result_path = str(temp_dir / "result.wav")
        results = [result_path]

        temp_folder = get_temp_folder(results)
        assert temp_folder == str(temp_dir)

    def test_get_temp_folder_with_result_objects(self, temp_dir):
        """Test get_temp_folder with Result objects"""
        from matchering.utils import get_temp_folder
        import matchering

        # Test with Result objects
        result_obj = matchering.Result(str(temp_dir / "result.wav"))
        results = [result_obj]

        temp_folder = get_temp_folder(results)
        assert temp_folder == str(temp_dir)

    def test_get_temp_folder_mixed_types(self, temp_dir):
        """Test get_temp_folder with mixed types"""
        from matchering.utils import get_temp_folder
        import matchering

        # Test with mixed string and Result objects
        result_path = str(temp_dir / "result1.wav")
        result_obj = matchering.Result(str(temp_dir / "result2.wav"))
        results = [result_path, result_obj]

        temp_folder = get_temp_folder(results)
        assert temp_folder == str(temp_dir)

    def test_random_str_function(self):
        """Test random string generation"""
        from matchering.utils import random_str

        # Test default size
        rand_str = random_str()
        assert len(rand_str) == 16
        assert rand_str.isalnum()

        # Test custom size
        custom_str = random_str(8)
        assert len(custom_str) == 8
        assert custom_str.isalnum()

        # Test uniqueness (very high probability)
        str1 = random_str()
        str2 = random_str()
        assert str1 != str2

    def test_random_file_function(self):
        """Test random file name generation"""
        from matchering.utils import random_file

        # Test default parameters
        filename = random_file()
        assert filename.endswith('.wav')
        assert len(filename) > 4  # Should be more than just '.wav'

        # Test with prefix
        prefixed = random_file(prefix="test")
        assert prefixed.startswith("test-")
        assert prefixed.endswith('.wav')

        # Test with custom extension
        custom_ext = random_file(extension="mp3")
        assert custom_ext.endswith('.mp3')

        # Test uniqueness
        file1 = random_file()
        file2 = random_file()
        assert file1 != file2

    def test_to_db_conversion(self):
        """Test dB conversion utilities"""
        from matchering.utils import to_db

        # Test normal values
        assert "0.0000 dB" == to_db(1.0)

        # Test quiet values
        db_str = to_db(0.5)
        assert "dB" in db_str
        assert "-" in db_str  # Should be negative

        # Test very quiet values
        db_str = to_db(0.001)
        assert "dB" in db_str
        assert "-" in db_str

        # Test zero and negative values
        assert to_db(0.0) == "-inf dB"
        assert to_db(-0.1) == "-inf dB"

    def test_ms_to_samples_conversion(self):
        """Test milliseconds to samples conversion"""
        from matchering.utils import ms_to_samples

        # Test standard cases
        assert ms_to_samples(1000, 44100) == 44100  # 1 second
        assert ms_to_samples(500, 44100) == 22050   # 0.5 seconds
        assert ms_to_samples(1, 44100) == 44        # 1 millisecond

        # Test different sample rates
        assert ms_to_samples(1000, 48000) == 48000
        assert ms_to_samples(1000, 22050) == 22050

        # Test fractional milliseconds
        assert ms_to_samples(0.5, 44100) == 22  # 0.5 ms

    def test_make_odd_function(self):
        """Test make_odd utility function"""
        from matchering.utils import make_odd

        # Test even numbers
        assert make_odd(2) == 3
        assert make_odd(4) == 5
        assert make_odd(100) == 101

        # Test odd numbers (should remain unchanged)
        assert make_odd(1) == 1
        assert make_odd(3) == 3
        assert make_odd(99) == 99

        # Test zero
        assert make_odd(0) == 1

    def test_time_str_formatting(self):
        """Test time string formatting"""
        from matchering.utils import time_str

        # Test exact seconds
        assert "0:00:01" == time_str(44100, 44100)  # 1 second
        assert "0:00:02" == time_str(88200, 44100)  # 2 seconds

        # Test minutes
        assert "0:01:00" == time_str(44100 * 60, 44100)  # 1 minute

        # Test hours (if needed)
        hour_samples = 44100 * 60 * 60
        time_result = time_str(hour_samples, 44100)
        assert "1:00:00" == time_result

        # Test fractional seconds (should truncate)
        assert "0:00:01" == time_str(44100 + 22050, 44100)  # 1.5 seconds -> 1 second


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.edge_cases
class TestPreviewEdgeCases:
    """Test edge cases for preview creation"""

    def test_create_preview_very_short_audio(self, temp_dir):
        """Test preview with very short audio"""
        from matchering.preview_creator import create_preview
        import matchering

        # Create very short audio (shorter than preview size)
        sample_rate = 44100
        samples = int(sample_rate * 0.1)  # 0.1 seconds

        target = np.random.random((samples, 2)).astype(np.float32) * 0.3
        result = np.random.random((samples, 2)).astype(np.float32) * 0.7

        config = matchering.Config(
            internal_sample_rate=sample_rate,
            preview_size=int(sample_rate * 1),  # 1 second (longer than audio)
        )

        preview_result = matchering.Result(str(temp_dir / "short_preview.wav"))

        # Should handle short audio gracefully
        create_preview(target, result, config, None, preview_result)

        if Path(preview_result.file).exists():
            import soundfile as sf
            preview_audio, _ = sf.read(preview_result.file)
            assert len(preview_audio) > 0

    def test_create_preview_silent_audio(self, temp_dir):
        """Test preview with silent audio"""
        from matchering.preview_creator import create_preview
        import matchering

        # Create silent audio
        samples = 44100 * 5
        target = np.zeros((samples, 2), dtype=np.float32)
        result = np.zeros((samples, 2), dtype=np.float32)

        config = matchering.Config()
        preview_result = matchering.Result(str(temp_dir / "silent_preview.wav"))

        # Should handle silent audio
        create_preview(target, result, config, None, preview_result)

        if Path(preview_result.file).exists():
            import soundfile as sf
            preview_audio, _ = sf.read(preview_result.file)
            # Should be silent or very quiet
            assert np.max(np.abs(preview_audio)) < 0.1

    def test_create_preview_single_piece(self, temp_dir):
        """Test preview when audio fits in single piece"""
        from matchering.preview_creator import create_preview
        import matchering

        sample_rate = 44100
        # Create audio that fits in one preview piece
        samples = int(sample_rate * 2)  # 2 seconds

        target = np.random.random((samples, 2)).astype(np.float32) * 0.3
        result = np.random.random((samples, 2)).astype(np.float32) * 0.7

        config = matchering.Config(
            internal_sample_rate=sample_rate,
            preview_size=int(sample_rate * 3),  # 3 seconds (longer than audio)
            preview_analysis_step=int(sample_rate * 1),  # 1 second step
        )

        preview_result = matchering.Result(str(temp_dir / "single_piece_preview.wav"))

        # Should work with single piece
        create_preview(target, result, config, None, preview_result)

        if Path(preview_result.file).exists():
            import soundfile as sf
            preview_audio, _ = sf.read(preview_result.file)
            assert len(preview_audio) > 0

    def test_create_preview_extreme_fade_settings(self, temp_dir):
        """Test preview with extreme fade settings"""
        from matchering.preview_creator import create_preview
        import matchering

        samples = 44100 * 5
        target = np.random.random((samples, 2)).astype(np.float32) * 0.3
        result = np.random.random((samples, 2)).astype(np.float32) * 0.7

        # Test with very large fade size
        config_large_fade = matchering.Config(
            preview_fade_size=int(44100 * 10),  # 10 seconds (very large)
            preview_fade_coefficient=2  # Small coefficient
        )

        preview_result = matchering.Result(str(temp_dir / "large_fade_preview.wav"))

        # Should handle extreme fade settings
        create_preview(target, result, config_large_fade, None, preview_result)

        if Path(preview_result.file).exists():
            import soundfile as sf
            preview_audio, _ = sf.read(preview_result.file)
            assert len(preview_audio) > 0


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.integration
class TestPreviewIntegration:
    """Test preview integration with other components"""

    def test_preview_with_real_processing_pipeline(self, test_audio_files, temp_dir):
        """Test preview creation with real processing pipeline"""
        stages = pytest.importorskip("matchering.stages")
        loader = pytest.importorskip("matchering.loader")
        from matchering.preview_creator import create_preview
        import matchering

        # Load real audio files
        target, _ = loader.load(test_audio_files["quiet_target.wav"], "target")
        reference, _ = loader.load(test_audio_files["loud_reference.wav"], "reference")

        # Process through stages
        config = matchering.Config()
        result, _, _ = stages.main(target, reference, config, need_default=True)

        # Create preview from processed result
        preview_target = matchering.Result(str(temp_dir / "real_target_preview.wav"))
        preview_result = matchering.Result(str(temp_dir / "real_result_preview.wav"))

        create_preview(target, result, config, preview_target, preview_result)

        # Verify previews were created
        assert Path(preview_target.file).exists()
        assert Path(preview_result.file).exists()

        # Verify preview quality
        import soundfile as sf
        target_preview, _ = sf.read(preview_target.file)
        result_preview, _ = sf.read(preview_result.file)

        assert len(target_preview) > 0
        assert len(result_preview) > 0
        assert target_preview.shape[1] == 2
        assert result_preview.shape[1] == 2

    def test_preview_with_different_config_settings(self, temp_dir):
        """Test preview with various configuration settings"""
        from matchering.preview_creator import create_preview
        import matchering

        # Create test audio
        samples = 44100 * 10  # 10 seconds
        target = np.random.random((samples, 2)).astype(np.float32) * 0.3
        result = np.random.random((samples, 2)).astype(np.float32) * 0.7

        # Test different configuration variations
        configs = [
            matchering.Config(preview_size=int(44100 * 1)),  # 1 second
            matchering.Config(preview_size=int(44100 * 5)),  # 5 seconds
            matchering.Config(preview_analysis_step=int(44100 * 0.5)),  # 0.5 second step
            matchering.Config(preview_analysis_step=int(44100 * 2)),    # 2 second step
        ]

        for i, config in enumerate(configs):
            preview_result = matchering.Result(str(temp_dir / f"config_test_{i}.wav"))

            create_preview(target, result, config, None, preview_result)

            if Path(preview_result.file).exists():
                import soundfile as sf
                preview_audio, _ = sf.read(preview_result.file)
                assert len(preview_audio) > 0