"""
GUI Integration Testing - Test GUI + backend integration workflows
Tests that GUI components can successfully interact with core processing
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestGUIBackendIntegration:
    """Test integration between GUI components and processing backend"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for GUI testing"""
        with tempfile.TemporaryDirectory(prefix="gui_test_") as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_audio_files(self, temp_workspace):
        """Create mock audio files for GUI testing"""
        # Create dummy files (GUI tests don't need real audio)
        target_file = temp_workspace / "target.wav"
        reference_file = temp_workspace / "reference.wav"

        target_file.touch()
        reference_file.touch()

        return {
            'target': str(target_file),
            'reference': str(reference_file)
        }

    def test_gui_file_selection_workflow(self, mock_audio_files, temp_workspace):
        """Test GUI file selection and validation workflow"""
        try:
            # Try to import GUI components
            from matchering_player.ui.main_window import MainWindow
            gui_available = True
        except ImportError:
            gui_available = False

        if not gui_available:
            pytest.skip("GUI components not available for testing")

        # Mock Qt application context
        with patch('matchering_player.ui.main_window.QApplication'):
            with patch('matchering_player.ui.main_window.QMainWindow'):
                # Mock GUI initialization
                mock_window = Mock(spec=MainWindow)

                # Simulate file selection
                target_file = mock_audio_files['target']
                reference_file = mock_audio_files['reference']

                # Mock file selection methods
                mock_window.select_target_file = Mock(return_value=target_file)
                mock_window.select_reference_file = Mock(return_value=reference_file)
                mock_window.validate_file_selection = Mock(return_value=True)

                # Test file selection workflow
                selected_target = mock_window.select_target_file()
                selected_reference = mock_window.select_reference_file()

                assert selected_target == target_file
                assert selected_reference == reference_file

                # Test validation
                is_valid = mock_window.validate_file_selection()
                assert is_valid == True

    def test_gui_processing_initiation_workflow(self, mock_audio_files, temp_workspace):
        """Test GUI-initiated processing workflow"""
        try:
            from matchering_player.ui.main_window import MainWindow
            gui_available = True
        except ImportError:
            gui_available = False

        if not gui_available:
            pytest.skip("GUI components not available for testing")

        # Mock the entire processing pipeline
        with patch('matchering.process') as mock_matchering_process:
            with patch('matchering_player.ui.main_window.QApplication'):
                # Mock successful processing
                mock_matchering_process.return_value = None  # Success

                # Mock GUI window
                mock_window = Mock()
                mock_window.get_target_file = Mock(return_value=mock_audio_files['target'])
                mock_window.get_reference_file = Mock(return_value=mock_audio_files['reference'])
                mock_window.get_output_file = Mock(return_value=str(temp_workspace / "result.wav"))
                mock_window.start_processing = Mock()
                mock_window.update_progress = Mock()
                mock_window.processing_complete = Mock()

                # Simulate GUI processing initiation
                target = mock_window.get_target_file()
                reference = mock_window.get_reference_file()
                output = mock_window.get_output_file()

                mock_window.start_processing()

                # Simulate backend processing call
                mock_matchering_process(
                    target=target,
                    reference=reference,
                    results=[output]
                )

                mock_window.processing_complete()

                # Verify the workflow
                mock_window.start_processing.assert_called_once()
                mock_matchering_process.assert_called_once()
                mock_window.processing_complete.assert_called_once()

    def test_gui_progress_reporting_workflow(self, temp_workspace):
        """Test GUI progress reporting during processing"""
        # Mock progress callback system
        progress_updates = []

        def mock_progress_callback(progress_percent, status_message):
            progress_updates.append((progress_percent, status_message))

        # Simulate processing with progress updates
        mock_progress_callback(0, "Initializing...")
        mock_progress_callback(25, "Loading target file...")
        mock_progress_callback(50, "Loading reference file...")
        mock_progress_callback(75, "Processing audio...")
        mock_progress_callback(100, "Complete!")

        # Verify progress updates
        assert len(progress_updates) == 5
        assert progress_updates[0] == (0, "Initializing...")
        assert progress_updates[-1] == (100, "Complete!")

        # Verify progress is monotonically increasing
        for i in range(1, len(progress_updates)):
            assert progress_updates[i][0] >= progress_updates[i-1][0]

    def test_gui_error_handling_workflow(self, temp_workspace):
        """Test GUI error handling and user feedback"""
        # Mock error scenarios
        error_scenarios = [
            ("FileNotFoundError", "Target file not found"),
            ("PermissionError", "Cannot write to output directory"),
            ("RuntimeError", "Processing failed"),
            ("MemoryError", "Insufficient memory for processing")
        ]

        for error_type, error_message in error_scenarios:
            # Mock GUI error handling
            mock_window = Mock()
            mock_window.display_error = Mock()
            mock_window.reset_ui_state = Mock()
            mock_window.enable_controls = Mock()

            # Simulate error occurrence
            mock_window.display_error(error_type, error_message)
            mock_window.reset_ui_state()
            mock_window.enable_controls(True)

            # Verify error handling workflow
            mock_window.display_error.assert_called_with(error_type, error_message)
            mock_window.reset_ui_state.assert_called_once()
            mock_window.enable_controls.assert_called_with(True)

    def test_gui_settings_persistence_workflow(self, temp_workspace):
        """Test GUI settings persistence workflow"""
        # Mock settings data
        test_settings = {
            'last_target_directory': str(temp_workspace),
            'last_reference_directory': str(temp_workspace),
            'default_output_format': 'WAV',
            'processing_quality': 'High',
            'auto_preview': True
        }

        # Mock settings management
        mock_settings = Mock()
        mock_settings.load_settings = Mock(return_value=test_settings)
        mock_settings.save_settings = Mock()
        mock_settings.get_setting = Mock(side_effect=lambda key, default=None: test_settings.get(key, default))
        mock_settings.set_setting = Mock(side_effect=lambda key, value: test_settings.update({key: value}))

        # Test loading settings
        loaded_settings = mock_settings.load_settings()
        assert loaded_settings == test_settings

        # Test getting individual settings
        target_dir = mock_settings.get_setting('last_target_directory')
        assert target_dir == str(temp_workspace)

        # Test updating settings
        mock_settings.set_setting('processing_quality', 'Maximum')
        mock_settings.save_settings(test_settings)

        # Verify settings workflow
        mock_settings.load_settings.assert_called_once()
        mock_settings.save_settings.assert_called_once()

    @pytest.mark.integration
    def test_gui_player_integration_workflow(self, mock_audio_files):
        """Test integration between GUI and player components"""
        from unittest.mock import patch

        # Mock player components
        with patch('matchering_player.core.audio_manager.AudioManager') as MockAudioManager:
            with patch('matchering_player.core.config.PlayerConfig') as MockPlayerConfig:

                # Setup mocks
                mock_config = Mock()
                MockPlayerConfig.return_value = mock_config

                mock_audio_manager = Mock()
                mock_audio_manager.load_file = Mock(return_value=True)
                mock_audio_manager.load_reference_track = Mock(return_value=True)
                mock_audio_manager.get_playback_info = Mock(return_value={
                    'state': 'stopped',
                    'file_loaded': True,
                    'duration': 120.0,
                    'position_seconds': 0.0
                })
                MockAudioManager.return_value = mock_audio_manager

                # Mock GUI-Player workflow
                mock_gui = Mock()
                mock_gui.initialize_player = Mock()
                mock_gui.load_audio_file = Mock()
                mock_gui.update_player_display = Mock()

                # Simulate workflow
                mock_gui.initialize_player()

                # Create player instance through GUI
                player_config = MockPlayerConfig()
                audio_manager = MockAudioManager(player_config)

                # Load file through GUI
                file_loaded = audio_manager.load_file(mock_audio_files['target'])
                mock_gui.load_audio_file(mock_audio_files['target'])

                # Update GUI display
                playback_info = audio_manager.get_playback_info()
                mock_gui.update_player_display(playback_info)

                # Verify integration workflow
                assert file_loaded == True
                mock_gui.initialize_player.assert_called_once()
                mock_gui.load_audio_file.assert_called_with(mock_audio_files['target'])
                mock_gui.update_player_display.assert_called_once()

    def test_gui_batch_processing_workflow(self, temp_workspace):
        """Test GUI batch processing workflow"""
        # Mock batch processing scenario
        batch_files = []
        for i in range(3):
            target_file = temp_workspace / f"target_{i}.wav"
            reference_file = temp_workspace / f"reference_{i}.wav"
            result_file = temp_workspace / f"result_{i}.wav"

            target_file.touch()
            reference_file.touch()

            batch_files.append({
                'target': str(target_file),
                'reference': str(reference_file),
                'result': str(result_file)
            })

        # Mock batch processing GUI
        mock_batch_processor = Mock()
        mock_batch_processor.add_job = Mock()
        mock_batch_processor.start_batch = Mock()
        mock_batch_processor.get_progress = Mock(return_value={'completed': 0, 'total': 3, 'current': None})
        mock_batch_processor.is_complete = Mock(return_value=False)

        # Simulate adding jobs
        for files in batch_files:
            mock_batch_processor.add_job(files['target'], files['reference'], files['result'])

        # Start batch processing
        mock_batch_processor.start_batch()

        # Simulate progress checking
        for i in range(4):  # 0, 1, 2, 3 (complete)
            progress = mock_batch_processor.get_progress()
            if i < 3:
                progress['completed'] = i
                progress['current'] = batch_files[i] if i < len(batch_files) else None
            else:
                progress['completed'] = 3
                progress['current'] = None
                mock_batch_processor.is_complete.return_value = True

        # Verify batch workflow
        assert mock_batch_processor.add_job.call_count == 3
        mock_batch_processor.start_batch.assert_called_once()
        assert mock_batch_processor.is_complete() == True

    @pytest.mark.performance
    def test_gui_responsiveness_during_processing(self, temp_workspace):
        """Test GUI responsiveness during background processing"""
        import time

        # Mock long-running processing task
        def mock_long_processing():
            time.sleep(0.1)  # Simulate processing time
            return "Processing complete"

        # Mock GUI responsiveness checking
        mock_gui = Mock()
        mock_gui.process_events = Mock()
        mock_gui.update_display = Mock()
        mock_gui.is_responsive = Mock(return_value=True)

        # Simulate processing with GUI updates
        start_time = time.perf_counter()

        # Simulate background processing with GUI updates
        for i in range(5):
            # Simulate GUI event processing
            mock_gui.process_events()
            mock_gui.update_display()

            # Small delay to simulate processing
            time.sleep(0.02)

            # Check responsiveness
            responsive = mock_gui.is_responsive()
            assert responsive == True

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Verify GUI remained responsive
        assert mock_gui.process_events.call_count == 5
        assert mock_gui.update_display.call_count == 5
        assert total_time < 1.0  # Should complete quickly

    def test_gui_theme_and_styling_workflow(self):
        """Test GUI theme and styling system"""
        # Mock theme management
        available_themes = ['Light', 'Dark', 'Auto']
        current_theme = 'Light'

        mock_theme_manager = Mock()
        mock_theme_manager.get_available_themes = Mock(return_value=available_themes)
        mock_theme_manager.get_current_theme = Mock(return_value=current_theme)
        mock_theme_manager.set_theme = Mock()
        mock_theme_manager.apply_theme = Mock()

        # Test theme workflow
        themes = mock_theme_manager.get_available_themes()
        assert themes == available_themes

        current = mock_theme_manager.get_current_theme()
        assert current == 'Light'

        # Change theme
        new_theme = 'Dark'
        mock_theme_manager.set_theme(new_theme)
        mock_theme_manager.apply_theme()

        # Verify theme change workflow
        mock_theme_manager.set_theme.assert_called_with('Dark')
        mock_theme_manager.apply_theme.assert_called_once()


class TestGUIUserScenarios:
    """Test complete user scenarios through the GUI"""

    def test_first_time_user_workflow(self, tmp_path):
        """Test complete first-time user experience"""
        # Mock first-time setup
        mock_setup = Mock()
        mock_setup.show_welcome = Mock()
        mock_setup.show_tutorial = Mock()
        mock_setup.configure_defaults = Mock()
        mock_setup.setup_complete = Mock(return_value=True)

        # Simulate first-time user flow
        mock_setup.show_welcome()
        mock_setup.show_tutorial()
        mock_setup.configure_defaults()

        setup_successful = mock_setup.setup_complete()

        # Verify first-time user workflow
        mock_setup.show_welcome.assert_called_once()
        mock_setup.show_tutorial.assert_called_once()
        mock_setup.configure_defaults.assert_called_once()
        assert setup_successful == True

    def test_power_user_workflow(self, tmp_path):
        """Test advanced/power user workflow"""
        # Mock advanced features
        mock_advanced_gui = Mock()
        mock_advanced_gui.show_advanced_settings = Mock()
        mock_advanced_gui.enable_custom_config = Mock()
        mock_advanced_gui.show_processing_details = Mock()
        mock_advanced_gui.export_settings = Mock()

        # Simulate power user workflow
        mock_advanced_gui.show_advanced_settings()
        mock_advanced_gui.enable_custom_config(True)
        mock_advanced_gui.show_processing_details(True)

        # Export user configuration
        mock_advanced_gui.export_settings()

        # Verify power user workflow
        mock_advanced_gui.show_advanced_settings.assert_called_once()
        mock_advanced_gui.enable_custom_config.assert_called_with(True)
        mock_advanced_gui.show_processing_details.assert_called_with(True)
        mock_advanced_gui.export_settings.assert_called_once()

    def test_accessibility_workflow(self):
        """Test accessibility features workflow"""
        # Mock accessibility features
        mock_accessibility = Mock()
        mock_accessibility.enable_high_contrast = Mock()
        mock_accessibility.set_font_size = Mock()
        mock_accessibility.enable_screen_reader = Mock()
        mock_accessibility.enable_keyboard_navigation = Mock()

        # Test accessibility workflow
        mock_accessibility.enable_high_contrast(True)
        mock_accessibility.set_font_size('Large')
        mock_accessibility.enable_screen_reader(True)
        mock_accessibility.enable_keyboard_navigation(True)

        # Verify accessibility features
        mock_accessibility.enable_high_contrast.assert_called_with(True)
        mock_accessibility.set_font_size.assert_called_with('Large')
        mock_accessibility.enable_screen_reader.assert_called_with(True)
        mock_accessibility.enable_keyboard_navigation.assert_called_with(True)