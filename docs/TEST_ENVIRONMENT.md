# Test Environment Configuration

## Overview
The test environment has been created to provide an isolated testing environment for the Tick-Tock Widget application. This allows for safe testing without affecting production or development data.

## Files Created

### 1. `development/run_test.py`
- **Purpose**: Launcher script for the test environment
- **Environment**: Sets `TICK_TOCK_ENV=test` and `TICK_TOCK_ENVIRONMENT=test`
- **Data File**: Uses `user_data/tick_tock_projects_test.json`
- **Usage**: `python development/run_test.py`

### 2. `user_data/tick_tock_projects_test.json`
- **Purpose**: Isolated test data file
- **Content**: Contains a minimal test project structure
- **Isolation**: Completely separate from development, production, and prototype data

## Configuration Details

### Visual Appearance (from config.json)
- **Window Title**: "Tick-Tock Widget [TEST]"
- **Title Color**: #FFFF00 (Yellow)
- **Border Color**: #444400 (Dark Yellow/Brown)

### Environment Settings
- **Environment**: test
- **Data File**: user_data/tick_tock_projects_test.json
- **Auto Save Interval**: 300 seconds (inherited from global config)
- **Backup**: Enabled (inherited from global config)

### Test Data Structure
```json
{
  "projects": [
    {
      "name": "Test Project",
      "dz_number": "TEST-001", 
      "alias": "TestProj",
      "time_records": {},
      "sub_activities": [
        {
          "name": "Test Activity",
          "alias": "TestAct", 
          "time_records": {}
        }
      ]
    }
  ],
  "current_project_alias": "TestProj",
  "last_saved": "2025-08-13T00:00:00.000000"
}
```

## Available Environments

Now all 4 environments from `config.json` have corresponding run scripts:

1. **Development**: `python development/run_development.py`
   - Window: "Tick-Tock Widget [DEV]" (Green)
   - Data: `tick_tock_projects_dev.json`

2. **Production**: `python development/run_production.py`
   - Window: "Tick-Tock Widget" (White)
   - Data: `tick_tock_projects.json`

3. **Test**: `python development/run_test.py` ✨ **NEW**
   - Window: "Tick-Tock Widget [TEST]" (Yellow)
   - Data: `tick_tock_projects_test.json`

4. **Prototype**: `python development/run_prototype.py`
   - Window: "Tick-Tock Widget [LEGACY PROTOTYPE]" (Orange)
   - Data: `tick_tock_projects_prototype.json`

## Testing Verification

### Configuration Test
```bash
cd "d:\SynologyDrive\mark_home\070 - Home Coding\GitHub\tick-tock\tick-tock"
python -c "import os; os.environ['TICK_TOCK_ENV']='test'; from src.tick_tock_widget.config import get_config; config=get_config(); print(f'Environment: {config.get_environment().value}'); print(f'Window Title: {config.get_window_title()}'); print(f'Title Color: {config.get_title_color()}'); print(f'Border Color: {config.get_border_color()}'); print(f'Data File: {config.get_data_file()}')"
```

**Expected Output:**
```
Environment: test
Window Title: Tick-Tock Widget [TEST]
Title Color: #FFFF00
Border Color: #444400
Data File: d:\SynologyDrive\mark_home\070 - Home Coding\GitHub\tick-tock\tick-tock\user_data\tick_tock_projects_test.json
```

### Application Launch Test
```bash
cd "d:\SynologyDrive\mark_home\070 - Home Coding\GitHub\tick-tock\tick-tock\development"
python run_test.py
```

**Expected Behavior:**
- Yellow title bar with "[TEST]" suffix
- Loads test project "TestProj"
- Data isolation from other environments
- All GUI features functional

## Benefits

1. **Data Isolation**: Test data is completely separate from other environments
2. **Visual Distinction**: Yellow color scheme clearly identifies test mode
3. **Safe Testing**: No risk of corrupting production or development data
4. **Consistent Pattern**: Follows same launcher pattern as other environments
5. **Configuration Driven**: All settings defined in centralized config.json

## Pytest Compatibility

- All 165 existing tests continue to pass
- No breaking changes to test infrastructure
- Test environment is available for manual testing scenarios
- Complements automated test suite with manual testing capabilities
