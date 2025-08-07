# Tick-Tock Widget Testing Guide

This document provides comprehensive information about the testing infrastructure for the Tick-Tock Widget application.

## Overview

The test suite is designed to thoroughly test a Tkinter-based time tracking application while avoiding the creation of actual GUI windows that could freeze tests or interfere with the testing environment.

## Test Structure

```
tests/
├── conftest.py                 # Test fixtures and configuration
├── unit/                      # Unit tests for individual components
│   ├── test_project_data.py   # ProjectDataManager and related classes
│   ├── test_config.py         # Configuration management tests
│   └── test_tick_tock_widget.py # Main widget tests
├── integration/               # Integration tests for component interactions
│   ├── test_data_management.py # Data persistence and management
│   └── test_gui_integration.py # GUI component integration
├── e2e/                      # End-to-end user scenario tests
│   └── test_user_scenarios.py # Complete user workflows
└── fixtures/                 # Test data and helper files
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Single classes, functions, methods
- **Mocking**: Extensive mocking of dependencies
- **Markers**: `@pytest.mark.unit`

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and data flow
- **Scope**: Multiple components working together
- **Mocking**: Limited mocking, real component integration
- **Markers**: `@pytest.mark.integration`

### End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete user scenarios and workflows
- **Scope**: Full application behavior simulation
- **Mocking**: Minimal mocking, mostly real components
- **Markers**: `@pytest.mark.e2e`

### GUI Tests (`@pytest.mark.gui`)
- **Purpose**: Test GUI components without creating actual windows
- **Approach**: Mock Tkinter components to prevent window creation
- **Safety**: No risk of frozen tests or UI interference

## Key Testing Features

### Tkinter Mocking Strategy

The test suite uses comprehensive mocking to avoid creating actual Tkinter windows:

```python
@pytest.fixture
def patch_tkinter():
    """Fixture to patch tkinter modules to prevent actual GUI creation"""
    with patch('tkinter.Tk') as mock_tk, \
         patch('tkinter.Toplevel') as mock_toplevel, \
         patch('tkinter.Frame') as mock_frame:
        # Configure mocks to return MockWidget instances
        mock_tk.return_value = MockTkRoot()
        # ... additional mocking
        yield mock_components
```

### Mock Components

- **MockTkRoot**: Simulates Tk root window behavior
- **MockWidget**: Generic widget mock with standard methods
- **Mock Event Handling**: Simulates user interactions

### Test Data Management

- **Temporary Files**: All tests use temporary files for data persistence
- **Sample Data**: Realistic test data fixtures
- **Environment Isolation**: Each test runs in isolated environment

## Running Tests

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src/tick_tock_widget --cov-report=html
```

### Using Test Runner Scripts

#### Python Script (Cross-platform)
```bash
# Run all tests
python run_tests.py all

# Run unit tests with coverage
python run_tests.py unit --coverage --verbose

# Run fast tests only
python run_tests.py fast

# Run specific test categories
python run_tests.py unit
python run_tests.py integration
python run_tests.py e2e
python run_tests.py gui
```

#### Windows Batch Script
```cmd
REM Run all tests
run_tests.bat all

REM Run unit tests with coverage
run_tests.bat unit -c -v

REM Install dependencies
run_tests.bat install
```

### Direct pytest Commands

```bash
# Run specific test types
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/e2e/                     # End-to-end tests only
pytest -m gui                         # GUI tests only
pytest -m "not slow"                  # Fast tests only

# Run specific test files
pytest tests/unit/test_project_data.py
pytest tests/e2e/test_user_scenarios.py::TestUserScenarios::test_new_user_first_project_workflow

# Coverage reporting
pytest --cov=src/tick_tock_widget --cov-report=html --cov-report=term-missing
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
markers =
    unit: Unit tests that test individual components in isolation
    integration: Integration tests that test component interactions
    e2e: End-to-end tests that test complete user scenarios
    gui: Tests that involve GUI components and require mocking
    slow: Tests that take longer to run
```

### Coverage Configuration
- **Source**: `src/tick_tock_widget/`
- **Reports**: HTML, terminal, XML
- **Exclusions**: Test files, cache directories

## Key Test Scenarios

### Data Management Tests
- Project creation, modification, deletion
- Time tracking accuracy
- Data persistence and loading
- Backup system functionality
- Environment switching

### GUI Component Tests
- Widget initialization
- Theme management and consistency
- Window positioning and geometry
- Event handling simulation
- Child window management

### User Workflow Tests
- New user first project setup
- Daily work routine simulation
- Project management workflows
- Environment switching scenarios
- Error handling and recovery

## Best Practices

### Writing New Tests

1. **Use Appropriate Fixtures**: Leverage existing fixtures for common setup
2. **Mock External Dependencies**: Always mock Tkinter components and file operations
3. **Test Error Conditions**: Include tests for error scenarios
4. **Use Descriptive Names**: Test names should clearly describe what is being tested
5. **Add Appropriate Markers**: Use `@pytest.mark.unit`, `@pytest.mark.gui`, etc.

### Example Test Structure

```python
class TestProjectManagement:
    """Test project management functionality"""
    
    def test_create_project_success(self, mock_data_manager):
        """Test successful project creation"""
        # Arrange
        manager = mock_data_manager
        
        # Act
        project = manager.add_project("Test Project", "DZ123", "TEST")
        
        # Assert
        assert project is not None
        assert project.name == "Test Project"
    
    @pytest.mark.gui
    def test_project_window_theme_update(self, patch_tkinter):
        """Test project window theme updates"""
        # Test with mocked GUI components
        pass
```

### Mocking Guidelines

1. **Mock at Component Boundaries**: Mock external dependencies, not internal logic
2. **Use Realistic Mock Data**: Ensure mock data resembles real application data
3. **Verify Mock Interactions**: Assert that mocked methods are called correctly
4. **Reset Mocks Between Tests**: Use fresh mocks for each test

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Mock Failures**: Check that all Tkinter components are properly mocked
3. **File Permission Errors**: Tests should use temporary directories
4. **Timing Issues**: Use deterministic time mocking for time-based tests

### Debug Mode

```bash
# Run tests with verbose output
pytest -v -s

# Run specific test with debugging
pytest -v -s tests/unit/test_project_data.py::TestProject::test_creation

# Show test output
pytest --capture=no
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- **No GUI Dependencies**: All GUI components are mocked
- **Isolated Environments**: Tests don't interfere with each other
- **Fast Execution**: Unit tests run quickly, slow tests are marked
- **Coverage Reporting**: Generates coverage reports for CI integration

## Contributing

When adding new features or modifying existing code:

1. **Write Tests First**: Follow TDD principles where possible
2. **Maintain Coverage**: Aim for high test coverage of new code
3. **Update Documentation**: Update this guide for new test patterns
4. **Run Full Test Suite**: Ensure all tests pass before committing

## Additional Resources

- **pytest Documentation**: https://docs.pytest.org/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **Coverage.py**: https://coverage.readthedocs.io/
- **Tkinter Testing Patterns**: See `conftest.py` for mocking examples
