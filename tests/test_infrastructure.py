"""
Basic sanity tests to verify test infrastructure is working
"""
import pytest
import sys
from pathlib import Path


class TestInfrastructure:
    """Test that the test infrastructure is properly configured"""
    
    def test_python_version(self):
        """Test that Python version is compatible"""
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    def test_imports_work(self):
        """Test that basic imports work"""
        try:
            import tick_tock_widget
            import tick_tock_widget.project_data
            import tick_tock_widget.config
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_test_structure_exists(self):
        """Test that test directory structure exists"""
        test_dir = Path(__file__).parent
        
        assert (test_dir / "unit").exists()
        assert (test_dir / "integration").exists()
        assert (test_dir / "e2e").exists()
        assert (test_dir / "fixtures").exists()
        assert (test_dir / "conftest.py").exists()
    
    def test_fixtures_available(self):
        """Test that test fixtures are available"""
        # Test that we can import fixtures from conftest
        from .conftest import MockTkRoot, MockWidget
        
        # Test basic fixture functionality
        mock_root = MockTkRoot()
        assert mock_root.geometry_value == "400x300+100+100"
        
        mock_widget = MockWidget()
        assert mock_widget.config_values == {}
    
    @pytest.mark.unit
    def test_unit_marker_works(self):
        """Test that unit test marker works"""
        assert True
    
    @pytest.mark.integration
    def test_integration_marker_works(self):
        """Test that integration test marker works"""
        assert True
    
    @pytest.mark.e2e
    def test_e2e_marker_works(self):
        """Test that e2e test marker works"""
        assert True
    
    @pytest.mark.gui
    def test_gui_marker_works(self):
        """Test that gui test marker works"""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker_works(self):
        """Test that slow test marker works"""
        assert True
    
    def test_temp_directories_work(self, temp_config_dir):
        """Test that temporary directories fixture works"""
        assert temp_config_dir.exists()
        assert temp_config_dir.is_dir()
        
        # Test writing to temp directory
        test_file = temp_config_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"
    
    def test_mock_data_manager_works(self, mock_data_manager):
        """Test that mock data manager fixture works"""
        assert mock_data_manager is not None
        assert hasattr(mock_data_manager, 'projects')
        assert hasattr(mock_data_manager, 'save_projects')
        assert hasattr(mock_data_manager, 'load_projects')
    
    def test_sample_data_available(self, sample_project_data):
        """Test that sample project data fixture works"""
        assert "projects" in sample_project_data
        assert "metadata" in sample_project_data
        assert len(sample_project_data["projects"]) > 0
    
    def test_theme_fixture_works(self, test_theme):
        """Test that theme fixture works"""
        required_keys = ['name', 'bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        for key in required_keys:
            assert key in test_theme
