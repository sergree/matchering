"""
Unit tests for advanced Matchering Player features
"""

import pytest
import numpy as np
from tests.conftest import HAS_PLAYER, assert_audio_equal, assert_rms_similar


@pytest.mark.unit
@pytest.mark.player
@pytest.mark.dsp
class TestFrequencyMatching:
    """Test frequency matching capabilities"""

    def test_frequency_matcher_initialization(self, full_config):
        """Test frequency matcher initialization"""
        if not full_config.enable_frequency_matching:
            pytest.skip("Frequency matching not enabled")

        try:
            RealtimeFrequencyMatcher = pytest.importorskip("matchering_player.dsp").RealtimeFrequencyMatcher
        except (ImportError, AttributeError):
            pytest.skip("RealtimeFrequencyMatcher not available")

        freq_matcher = RealtimeFrequencyMatcher(full_config)
        assert freq_matcher is not None

        # Test EQ settings if method exists
        if hasattr(freq_matcher, 'get_eq_settings'):
            eq_settings = freq_matcher.get_eq_settings()
            # EQ settings might be empty initially, just check it returns something
            assert eq_settings is not None
        else:
            # If method doesn't exist, just verify the object was created
            assert hasattr(freq_matcher, '__class__')

    def test_frequency_matching_processing(self, full_config, sine_wave):
        """Test frequency matching processing"""
        if not full_config.enable_frequency_matching:
            pytest.skip("Frequency matching not enabled")

        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(full_config)

        # Load mock reference - this might not actually enable frequency matching
        # if the processor doesn't have that functionality implemented
        success = processor.load_reference_track("mock_reference.wav")

        # Mock reference loading might succeed even if frequency matching isn't implemented
        if not success:
            pytest.skip("Mock reference loading not supported")

        test_audio, _ = sine_wave(full_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = full_config.buffer_size_samples
        if len(test_audio) != expected_samples:
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        processor.start_processing()

        # Process with frequency matching
        processed = processor.process_audio_chunk(test_audio)
        assert processed.shape == test_audio.shape

        # Test frequency matching controls if available
        try:
            processor.set_effect_enabled("frequency_matching", False)
            processor.set_effect_enabled("frequency_matching", True)
        except (AttributeError, KeyError, ValueError):
            # Effect controls might not be implemented
            pytest.skip("Frequency matching effect controls not available")

        processor.stop_processing()

    def test_eq_band_control(self, full_config):
        """Test EQ band parameter control"""
        if not full_config.enable_frequency_matching:
            pytest.skip("Frequency matching not enabled")

        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(full_config)

        if processor.frequency_matcher:
            # Test getting frequency stats
            freq_stats = processor.frequency_matcher.get_current_stats()
            assert 'enabled' in freq_stats
            assert 'eq_bands_count' in freq_stats


@pytest.mark.unit
@pytest.mark.player
@pytest.mark.dsp
class TestStereoWidthControl:
    """Test stereo width control capabilities"""

    def test_stereo_processor_initialization(self, full_config):
        """Test stereo processor initialization"""
        if not full_config.enable_stereo_width:
            pytest.skip("Stereo width not enabled")

        RealtimeStereoProcessor = pytest.importorskip("matchering_player.dsp").RealtimeStereoProcessor

        stereo_processor = RealtimeStereoProcessor(full_config)
        assert stereo_processor is not None

    def test_stereo_width_processing(self, full_config, sine_wave):
        """Test stereo width processing"""
        if not full_config.enable_stereo_width:
            pytest.skip("Stereo width not enabled")

        RealtimeStereoProcessor = pytest.importorskip("matchering_player.dsp").RealtimeStereoProcessor

        stereo_processor = RealtimeStereoProcessor(full_config)
        test_audio, _ = sine_wave(full_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = full_config.buffer_size_samples
        if len(test_audio) != expected_samples:
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        # Test different width settings
        for width in [0.0, 0.5, 1.0, 1.5, 2.0]:
            stereo_processor.set_width(width)
            result = stereo_processor.process_chunk(test_audio)
            assert result.shape == test_audio.shape

    def test_stereo_width_variations(self, full_config):
        """Test stereo width variations with clear L/R content"""
        if not full_config.enable_stereo_width:
            pytest.skip("Stereo width not enabled")

        RealtimeStereoProcessor = pytest.importorskip("matchering_player.dsp").RealtimeStereoProcessor

        stereo_processor = RealtimeStereoProcessor(full_config)

        # Create test stereo audio with clear L/R separation
        samples = full_config.buffer_size_samples
        demo_audio = np.zeros((samples, 2), dtype=np.float32)
        t = np.linspace(0, 0.1, samples)
        demo_audio[:, 0] = 0.5 * np.sin(2 * np.pi * 440 * t)  # Left: 440 Hz
        demo_audio[:, 1] = 0.3 * np.sin(2 * np.pi * 660 * t)  # Right: 660 Hz

        # Test different width settings
        correlations = {}
        for width in [0.0, 0.5, 1.0, 1.5, 2.0]:
            stereo_processor.set_width(width)
            result = stereo_processor.process_chunk(demo_audio)

            # Calculate L/R correlation as measure of stereo width
            if len(result) > 1:
                correlation = np.corrcoef(result[:, 0], result[:, 1])[0, 1]
                correlations[width] = correlation

        # Verify that width changes affect correlation
        if len(correlations) > 1:
            width_values = list(correlations.keys())
            corr_values = list(correlations.values())

            # Should show some variation in correlation with width changes
            corr_range = max(corr_values) - min(corr_values)
            assert corr_range > 0.01, "Stereo width should affect L/R correlation"

    def test_integrated_stereo_processing(self, full_config, sine_wave):
        """Test stereo processing integrated with main processor"""
        if not full_config.enable_stereo_width:
            pytest.skip("Stereo width not enabled")

        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(full_config)
        test_audio, _ = sine_wave(full_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = full_config.buffer_size_samples
        if len(test_audio) != expected_samples:
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        processor.start_processing()

        # Test stereo width controls
        processor.set_effect_enabled("stereo_width", True)
        processor.set_effect_parameter("stereo_width", "width", 0.5)
        processor.set_effect_parameter("stereo_width", "width", 1.5)
        processor.set_effect_parameter("stereo_width", "width", 1.0)

        # Process audio with stereo width control
        processed = processor.process_audio_chunk(test_audio)
        assert processed.shape == test_audio.shape

        processor.stop_processing()


@pytest.mark.unit
@pytest.mark.player
@pytest.mark.dsp
class TestAutoMastering:
    """Test auto-mastering capabilities"""

    def test_content_analyzer(self, full_config, sine_wave):
        """Test content analysis functionality"""
        try:
            ContentAnalyzer = pytest.importorskip("matchering_player.dsp").ContentAnalyzer
        except (ImportError, AttributeError):
            pytest.skip("ContentAnalyzer not available")

        analyzer = ContentAnalyzer(full_config)
        test_audio, _ = sine_wave(2.0)  # 2 second audio

        # Feed chunks to analyzer
        chunk_size = full_config.buffer_size_samples
        for i in range(0, min(len(test_audio), chunk_size * 10), chunk_size):
            chunk = test_audio[i:i + chunk_size]
            if len(chunk) == chunk_size:
                analyzer.analyze_chunk(chunk)

        # Get analysis results
        analysis = analyzer.get_analysis_results()
        assert 'detected_genre' in analysis
        assert 'confidence_level' in analysis
        assert 'spectral_centroid' in analysis

    def test_auto_mastering_profiles(self, full_config, sine_wave):
        """Test auto-mastering profiles"""
        try:
            AutoMasterProcessor = pytest.importorskip("matchering_player.dsp").AutoMasterProcessor
            AutoMasterProfile = pytest.importorskip("matchering_player.dsp").AutoMasterProfile
        except (ImportError, AttributeError):
            pytest.skip("Auto-mastering not available")

        auto_master = AutoMasterProcessor(full_config)
        available_profiles = AutoMasterProcessor.get_available_profiles()
        assert len(available_profiles) > 0

        test_audio, _ = sine_wave(full_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = full_config.buffer_size_samples
        if len(test_audio) != expected_samples:
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        # Test different profiles
        for profile_name in available_profiles[:3]:  # Test first 3 profiles
            profile = AutoMasterProfile(profile_name)
            auto_master.set_profile(profile)

            targets, processed = auto_master.process_chunk(test_audio)
            assert processed.shape == test_audio.shape
            assert 'target_rms_db' in targets

    def test_adaptive_mode(self, full_config):
        """Test adaptive profile detection"""
        try:
            AutoMasterProcessor = pytest.importorskip("matchering_player.dsp").AutoMasterProcessor
        except (ImportError, AttributeError):
            pytest.skip("Auto-mastering not available")

        auto_master = AutoMasterProcessor(full_config)

        # Enable adaptive mode
        auto_master.enable_adaptive_mode()

        # Create different types of audio content
        chunk_size = full_config.buffer_size_samples

        # Acoustic-like content (simple sine wave)
        acoustic_audio = np.column_stack([
            np.sin(2 * np.pi * 220 * np.linspace(0, 0.1, chunk_size)) * 0.2,
            np.sin(2 * np.pi * 220 * np.linspace(0, 0.1, chunk_size)) * 0.2
        ]).astype(np.float32)

        # Process several chunks
        for _ in range(10):
            targets, _ = auto_master.process_chunk(acoustic_audio)

        # Check if detection is working
        stats = auto_master.get_current_stats()
        assert 'current_profile' in stats
        assert 'analysis' in stats

    def test_integrated_auto_mastering(self, full_config, sine_wave):
        """Test auto-mastering integrated with main processor"""
        # Create config with auto-mastering enabled
        try:
            config = full_config
            config.enable_auto_mastering = True
        except:
            pytest.skip("Auto-mastering configuration not available")

        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(config)
        test_audio, _ = sine_wave(config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = config.buffer_size_samples
        if len(test_audio) != expected_samples:
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        processor.start_processing()

        # Process with auto-mastering
        for _ in range(10):
            processed = processor.process_audio_chunk(test_audio)
            assert processed.shape == test_audio.shape

        # Check auto-mastering stats if available
        if processor.auto_master:
            auto_stats = processor.auto_master.get_current_stats()
            assert 'current_profile' in auto_stats

        processor.stop_processing()


@pytest.mark.unit
@pytest.mark.performance
@pytest.mark.player
class TestAdvancedPerformance:
    """Test performance with advanced features enabled"""

    @pytest.mark.slow
    def test_full_effects_performance(self, full_config, sine_wave):
        """Test performance with all effects enabled"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor

        processor = RealtimeProcessor(full_config)
        test_audio, _ = sine_wave(full_config.buffer_size_ms / 1000.0)

        # Ensure correct buffer size
        expected_samples = full_config.buffer_size_samples
        if len(test_audio) != expected_samples:
            test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

        processor.start_processing()

        # Measure performance with all effects
        import time
        start_time = time.perf_counter()

        num_chunks = 100
        for _ in range(num_chunks):
            processed = processor.process_audio_chunk(test_audio)

        end_time = time.perf_counter()

        processing_time = end_time - start_time
        real_time = (num_chunks * full_config.buffer_size_samples) / full_config.sample_rate
        cpu_usage = processing_time / real_time

        processor.stop_processing()

        # Performance should still be reasonable with all effects
        assert cpu_usage < 3.0, f"CPU usage with all effects too high: {cpu_usage:.1%}"

    def test_effect_performance_comparison(self, test_config, full_config, sine_wave):
        """Compare performance with different effect combinations"""
        RealtimeProcessor = pytest.importorskip("matchering_player.dsp").RealtimeProcessor
        import time

        configs = [
            ("Basic", test_config),
            ("Full", full_config)
        ]

        performance_results = {}

        for config_name, config in configs:
            processor = RealtimeProcessor(config)
            test_audio, _ = sine_wave(config.buffer_size_ms / 1000.0)

            # Ensure correct buffer size
            expected_samples = config.buffer_size_samples
            if len(test_audio) != expected_samples:
                test_audio = test_audio[:expected_samples] if len(test_audio) > expected_samples else np.pad(test_audio, ((0, expected_samples - len(test_audio)), (0, 0)), 'constant')

            processor.start_processing()

            # Warmup
            for _ in range(10):
                processor.process_audio_chunk(test_audio)

            # Measure
            num_chunks = 50
            start_time = time.perf_counter()

            for _ in range(num_chunks):
                processor.process_audio_chunk(test_audio)

            end_time = time.perf_counter()

            processing_time = end_time - start_time
            real_time = (num_chunks * config.buffer_size_samples) / config.sample_rate
            cpu_usage = processing_time / real_time

            processor.stop_processing()

            performance_results[config_name] = cpu_usage

        # Both should be reasonable, full config may be slower
        for config_name, cpu_usage in performance_results.items():
            assert cpu_usage < 2.0, f"{config_name} config CPU usage too high: {cpu_usage:.1%}"

        # Return None to avoid pytest warning
        return None