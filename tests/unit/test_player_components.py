"""
Unit tests for Matchering Player components
"""

import pytest
import numpy as np
from tests.conftest import HAS_PLAYER, assert_audio_equal, assert_rms_similar


@pytest.mark.unit
@pytest.mark.player
@pytest.mark.dsp
class TestPlayerConfiguration:
    """Test player configuration functionality"""

    def test_default_config(self):
        """Test default configuration creation"""
        PlayerConfig = pytest.importorskip("matchering_player.core.config").PlayerConfig

        config = PlayerConfig()

        # Check default values
        assert config.sample_rate == 44100
        assert config.buffer_size_ms > 0
        assert config.buffer_size_samples > 0
        assert hasattr(config, 'enable_level_matching')

    def test_custom_config(self):
        """Test custom configuration parameters"""
        PlayerConfig = pytest.importorskip("matchering_player.core.config").PlayerConfig

        config = PlayerConfig(
            buffer_size_ms=50.0,
            enable_level_matching=True,
            enable_frequency_matching=False
        )

        assert config.buffer_size_ms == 50.0
        assert config.enable_level_matching is True
        assert config.enable_frequency_matching is False

    def test_config_validation(self):
        """Test configuration validation"""
        PlayerConfig = pytest.importorskip("matchering_player.core.config").PlayerConfig

        # Test reasonable buffer sizes
        for buffer_ms in [10.0, 50.0, 100.0, 200.0, 500.0]:
            config = PlayerConfig(buffer_size_ms=buffer_ms)
            assert config.buffer_size_samples > 0

        # Test different sample rates
        for sample_rate in [22050, 44100, 48000, 96000]:
            config = PlayerConfig(sample_rate=sample_rate)
            assert config.sample_rate == sample_rate


@pytest.mark.unit
@pytest.mark.player
@pytest.mark.dsp
class TestPlayerDSPProcessor:
    """Test player DSP processor"""

    def test_processor_creation(self, test_config):
        """Test processor creation and initialization"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(test_config)

        assert processor.config == test_config
        assert not processor.is_processing
        assert processor.level_matcher is not None

    def test_processor_effects(self, test_config):
        """Test processor effect management"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(test_config)

        # Test getting supported effects
        effects = processor.get_supported_effects()
        assert isinstance(effects, list)
        assert len(effects) > 0

        # Test enabling/disabling effects
        processor.set_effect_enabled("level_matching", False)
        processor.set_effect_enabled("level_matching", True)

    def test_basic_processing(self, test_config, sine_wave):
        """Test basic audio processing"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(test_config)
        test_audio, _ = sine_wave(test_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = test_config.buffer_size_samples
        if len(test_audio) != expected_samples:
            # Resize to match expected buffer size
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        # Process audio chunk
        result = processor.process_audio_chunk(test_audio)

        assert result.shape == test_audio.shape
        assert result.dtype == test_audio.dtype

    def test_processing_lifecycle(self, test_config, sine_wave):
        """Test processing start/stop lifecycle"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(test_config)
        test_audio, _ = sine_wave(test_config.buffer_size_ms / 1000.0)

        # Initially not processing
        assert not processor.is_processing

        # Start processing
        processor.start_processing()
        assert processor.is_processing

        # Process some audio
        result = processor.process_audio_chunk(test_audio)
        assert result is not None

        # Stop processing
        processor.stop_processing()
        assert not processor.is_processing


@pytest.mark.unit
@pytest.mark.player
@pytest.mark.dsp
class TestPlayerDSPEffects:
    """Test individual DSP effects"""

    def test_level_matching(self, test_config, audio_pair):
        """Test level matching functionality"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor
        rms = pytest.importorskip("matchering_player.dsp").rms

        processor = RealtimeProcessor(test_config)
        target_audio, reference_audio, sr = audio_pair

        # Load mock reference to enable level matching
        success = processor.load_reference_track("mock_reference.wav")
        assert success

        # Process quiet audio multiple times to allow smoothing
        chunk_size = test_config.buffer_size_samples
        quiet_chunk = target_audio[:chunk_size]
        if len(quiet_chunk) < chunk_size:
            quiet_chunk = np.pad(quiet_chunk, ((0, chunk_size - len(quiet_chunk)), (0, 0)), 'constant')

        original_rms = rms(quiet_chunk[:, 0])

        processor.start_processing()

        # Process multiple chunks to engage smoothing
        processed_chunk = quiet_chunk
        for _ in range(20):
            processed_chunk = processor.process_audio_chunk(processed_chunk)

        processed_rms = rms(processed_chunk[:, 0])
        gain_ratio = processed_rms / original_rms

        # Should apply some gain
        assert gain_ratio > 1.0, f"Level matching should increase gain, got {gain_ratio}"

        processor.stop_processing()

    def test_frequency_matching(self, full_config, audio_pair):
        """Test frequency matching if available"""
        pytest.importorskip("matchering_player.dsp")

        # Skip if frequency matching is not enabled in config
        if not full_config.enable_frequency_matching:
            pytest.skip("Frequency matching not enabled")

        from matchering_player.dsp import RealtimeProcessor

        processor = RealtimeProcessor(full_config)

        # Test frequency matching controls
        processor.set_effect_enabled("frequency_matching", True)
        processor.set_effect_enabled("frequency_matching", False)

    def test_stereo_width(self, full_config, sine_wave):
        """Test stereo width control if available"""
        pytest.importorskip("matchering_player.dsp")

        # Skip if stereo width is not enabled in config
        if not full_config.enable_stereo_width:
            pytest.skip("Stereo width not enabled")

        from matchering_player.dsp import RealtimeProcessor

        processor = RealtimeProcessor(full_config)
        test_audio, _ = sine_wave(full_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = full_config.buffer_size_samples
        if len(test_audio) != expected_samples:
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        # Test stereo width controls
        processor.set_effect_enabled("stereo_width", True)
        processor.set_effect_parameter("stereo_width", "width", 0.5)
        processor.set_effect_parameter("stereo_width", "width", 1.5)


@pytest.mark.unit
@pytest.mark.player
@pytest.mark.files
class TestPlayerFileLoader:
    """Test player file loading utilities"""

    def test_file_loader_info(self, test_audio_files):
        """Test getting file information"""
        get_audio_file_info = pytest.importorskip("matchering_player.utils.file_loader").get_audio_file_info

        test_file = test_audio_files["quiet_target.wav"]
        info = get_audio_file_info(test_file)

        assert hasattr(info, 'duration')
        assert hasattr(info, 'sample_rate')
        assert hasattr(info, 'channels')
        assert info.sample_rate == 44100
        assert info.channels == 2

    def test_file_loader_load(self, test_audio_files):
        """Test loading audio files"""
        load_audio_file = pytest.importorskip("matchering_player.utils.file_loader").load_audio_file

        test_file = test_audio_files["quiet_target.wav"]
        audio_data, sample_rate = load_audio_file(test_file)

        assert audio_data.shape[1] == 2  # Stereo
        assert sample_rate == 44100
        assert audio_data.dtype == np.float32

    def test_file_loader_formats(self, temp_dir):
        """Test loading different audio formats"""
        sf = pytest.importorskip("soundfile")
        load_audio_file = pytest.importorskip("matchering_player.utils.file_loader").load_audio_file

        # Create test files with different formats
        test_audio = np.column_stack([
            np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100)),
            np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100) * 1.01)
        ]).astype(np.float32) * 0.5

        formats = [
            ("test_16bit.wav", {"subtype": "PCM_16"}),
            ("test_24bit.wav", {"subtype": "PCM_24"}),
            ("test_float.wav", {"subtype": "FLOAT"})
        ]

        for filename, format_opts in formats:
            filepath = temp_dir / filename
            sf.write(filepath, test_audio, 44100, **format_opts)

            # Test loading
            loaded_audio, sample_rate = load_audio_file(str(filepath))
            assert loaded_audio.shape[1] == 2
            assert sample_rate == 44100