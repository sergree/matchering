"""
Tests for core processing functionality
"""

import pytest
import numpy as np
import soundfile as sf
import tempfile
import shutil
from pathlib import Path

from matchering import process, Config, Result
from matchering.loader import __load_with_ffmpeg
from matchering.log import ModuleError


@pytest.fixture
def test_files(tmp_path):
    """Create test audio files"""
    duration = 2.0
    sample_rate = 44100
    t = np.linspace(0, duration, int(duration * sample_rate))

    # Create target (quiet sine wave)
    target = np.sin(2 * np.pi * 440 * t) * 0.1
    target_stereo = np.column_stack([target, target * 0.9])
    target_path = tmp_path / "target.wav"
    sf.write(target_path, target_stereo, sample_rate)

    # Create reference (louder sine wave with different spectrum)
    ref = np.sin(2 * np.pi * 440 * t) * 0.8 + np.sin(2 * np.pi * 880 * t) * 0.2
    ref_stereo = np.column_stack([ref, ref * 0.95])
    ref_path = tmp_path / "reference.wav"
    sf.write(ref_path, ref_stereo, sample_rate)

    return {
        "target": str(target_path),
        "reference": str(ref_path),
        "sample_rate": sample_rate
    }


class TestCore:
    """Test the core audio processing"""

    def test_basic_processing(self, test_files, tmp_path):
        """Test basic audio processing with default settings"""
        output_path = tmp_path / "output.wav"
        
        # Process with default settings
        process(
            target=test_files["target"],
            reference=test_files["reference"],
            results=[Result(str(output_path), subtype="PCM_16")]
        )

        # Verify output exists and has correct format
        assert output_path.exists()
        
        # Load and check results
        output_audio, sr = sf.read(output_path)
        target_audio, _ = sf.read(test_files["target"])
        reference_audio, _ = sf.read(test_files["reference"])

        # Check basic properties
        assert sr == test_files["sample_rate"]
        assert output_audio.shape == target_audio.shape

        # Verify processing effect
        output_rms = np.sqrt(np.mean(output_audio**2))
        reference_rms = np.sqrt(np.mean(reference_audio**2))
        assert np.abs(output_rms - reference_rms) < 0.1

    def test_custom_config(self, test_files, tmp_path):
        """Test processing with custom configuration"""
        config = Config()
        config.threshold = -3.0  # More conservative limiting
        config.rms_correction_steps = 5  # More precise level matching

        output_path = tmp_path / "output_custom.wav"
        
        # Process with custom config
        process(
            target=test_files["target"],
            reference=test_files["reference"],
            results=[Result(str(output_path), subtype="PCM_16")],
            config=config
        )

        # Verify output
        assert output_path.exists()
        audio, _ = sf.read(output_path)
        
        # Check that output is finite and reasonable
        assert np.all(np.isfinite(audio))
        assert np.max(np.abs(audio)) <= 1.0

    def test_multiple_outputs(self, test_files, tmp_path):
        """Test generating multiple output formats"""
        results = [
            Result(str(tmp_path / "output_limited.wav"), subtype="PCM_16", use_limiter=True),
            Result(str(tmp_path / "output_no_limiter.wav"), subtype="PCM_16", use_limiter=False),
            Result(str(tmp_path / "output_normalized.wav"), subtype="PCM_16", 
                  use_limiter=False, normalize=True)
        ]
        
        # Process with all formats
        process(
            target=test_files["target"],
            reference=test_files["reference"],
            results=results
        )

        # Verify all files were created
        for result in results:
            assert Path(result.file).exists()
            audio, _ = sf.read(result.file)
            assert not np.any(np.isnan(audio))
            assert not np.any(np.isinf(audio))

        # Check differences between formats
        limited, _ = sf.read(results[0].file)
        no_limiter, _ = sf.read(results[1].file)
        normalized, _ = sf.read(results[2].file)

        # Limited version should be constrained
        assert np.max(np.abs(limited)) <= 1.0
        
        # Non-limited versions should differ in RMS
        nolim_rms = np.sqrt(np.mean(no_limiter**2))
        norm_rms = np.sqrt(np.mean(normalized**2))
        assert not np.allclose(nolim_rms, norm_rms, rtol=1e-2)

    def test_preview_generation(self, test_files, tmp_path):
        """Test preview file generation"""
        preview_target = Result(str(tmp_path / "preview_target.wav"), subtype="PCM_16")
        preview_result = Result(str(tmp_path / "preview_result.wav"), subtype="PCM_16")

        # Process with preview generation
        process(
            target=test_files["target"],
            reference=test_files["reference"],
            results=[Result(str(tmp_path / "output.wav"), subtype="PCM_16")],
            preview_target=preview_target,
            preview_result=preview_result
        )

        # Verify preview files were created
        assert Path(preview_target.file).exists()
        assert Path(preview_result.file).exists()

        # Check preview contents
        target_preview, _ = sf.read(preview_target.file)
        result_preview, _ = sf.read(preview_result.file)
        
        assert target_preview.shape == result_preview.shape
        assert not np.array_equal(target_preview, result_preview)


class TestErrorHandling:
    """Test error handling in core processing"""

    def test_empty_results(self, test_files):
        """Test handling of empty results list"""
        with pytest.raises(RuntimeError):
            process(
                target=test_files["target"],
                reference=test_files["reference"],
                results=[]
            )

    def test_missing_files(self, test_files, tmp_path):
        """Test handling of missing files"""
        with pytest.raises(ModuleError):
            process(
                target=str(tmp_path / "nonexistent.wav"),
                reference=test_files["reference"],
                results=[Result(str(tmp_path / "output.wav"), subtype="PCM_16")]
            )

    def test_invalid_files(self, tmp_path):
        """Test handling of invalid audio files"""
        # Create invalid file
        invalid_file = tmp_path / "invalid.wav"
        invalid_file.write_text("Not an audio file")

        output_file = tmp_path / "output.wav"
        
        with pytest.raises(ModuleError):
            process(
                target=str(invalid_file),
                reference=str(invalid_file),
                results=[Result(str(output_file), subtype="PCM_16")]
            )

    def test_file_permissions(self, test_files, tmp_path):
        """Test handling of permission errors"""
        # Create directory without write permissions
        no_write_dir = tmp_path / "no_write"
        no_write_dir.mkdir()
        no_write_dir.chmod(0o555)  # Read-only

        with pytest.raises(Exception):
            process(
                target=test_files["target"],
                reference=test_files["reference"],
                results=[Result(str(no_write_dir / "output.wav"), subtype="PCM_16")]
            )